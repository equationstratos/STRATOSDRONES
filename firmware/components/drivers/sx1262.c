/* SX1262 LoRa transceiver driver (EU868) — shared SPI2 bus, own CS/BUSY/
 * DIO1/RST pins. Command set per the Semtech SX1261/2 datasheet
 * (DS.SX1261-2.W.APP, rev 2.1): every SPI transaction waits for BUSY low.
 *
 * Fixed M0 profile (matches stratospy/lora.py and the dongle bridge):
 *   869.525 MHz (EU868 10 % duty sub-band), SF7, BW 250 kHz, CR 4/5,
 *   preamble 8, explicit header, CRC on, TX +14 dBm (module PA limits
 *   apply — E22-900M22S has its own PA config, VERIFY before fab).
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "board_select.h"
#include "drivers.h"

#if BOARD_HAS_LORA

static const char *TAG = "sx1262";

extern spi_device_handle_t g_spi_lora;      /* added in buses.c for tinyhoop */

/* --- opcodes (datasheet §13) --- */
#define OP_SET_STANDBY          0x80
#define OP_SET_PACKET_TYPE      0x8A
#define OP_SET_RF_FREQUENCY     0x86
#define OP_SET_PA_CONFIG        0x95
#define OP_SET_TX_PARAMS        0x8E
#define OP_SET_BUF_BASE         0x8F
#define OP_SET_MOD_PARAMS       0x8B
#define OP_SET_PKT_PARAMS       0x8C
#define OP_SET_DIO_IRQ          0x08
#define OP_SET_DIO2_RF_SWITCH   0x9D
#define OP_SET_REGULATOR_MODE   0x96
#define OP_CALIBRATE            0x89
#define OP_WRITE_BUFFER         0x0E
#define OP_READ_BUFFER          0x1E
#define OP_SET_TX               0x83
#define OP_SET_RX               0x82
#define OP_GET_IRQ_STATUS       0x12
#define OP_CLR_IRQ_STATUS       0x02
#define OP_GET_RX_BUF_STATUS    0x13
#define OP_GET_PKT_STATUS       0x14

#define IRQ_TX_DONE     0x0001
#define IRQ_RX_DONE     0x0002
#define IRQ_CRC_ERR     0x0040
#define IRQ_TIMEOUT     0x0200

#define FREQ_HZ         869525000ULL
#define FREQ_STEP_NUM   (FREQ_HZ * 33554432ULL / 32000000ULL) /* f * 2^25 / 32M */

static bool s_ready;

static void wait_busy(void)
{
    for (int i = 0; i < 1000 && gpio_get_level(PIN_LORA_BUSY); i++)
        esp_rom_delay_us(10);
}

static esp_err_t cmd(uint8_t op, const uint8_t *args, size_t n)
{
    wait_busy();
    uint8_t buf[16];
    buf[0] = op;
    if (n) memcpy(&buf[1], args, n);
    spi_transaction_t t = {.length = 8 * (n + 1), .tx_buffer = buf};
    return spi_device_transmit(g_spi_lora, &t);
}

static esp_err_t cmd_read(uint8_t op, uint8_t *out, size_t n)
{
    wait_busy();
    uint8_t tx[16] = {op, 0x00};                 /* opcode + NOP status */
    uint8_t rx[16] = {0};
    spi_transaction_t t = {.length = 8 * (n + 2), .tx_buffer = tx, .rx_buffer = rx};
    esp_err_t err = spi_device_transmit(g_spi_lora, &t);
    memcpy(out, &rx[2], n);
    return err;
}

esp_err_t sx1262_init(void)
{
    gpio_config_t io = {
        .pin_bit_mask = (1ULL << PIN_LORA_BUSY) | (1ULL << PIN_LORA_DIO1),
        .mode = GPIO_MODE_INPUT,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&io), TAG, "in pins");
    io.pin_bit_mask = 1ULL << PIN_LORA_RST;
    io.mode = GPIO_MODE_OUTPUT;
    ESP_RETURN_ON_ERROR(gpio_config(&io), TAG, "rst pin");

    gpio_set_level(PIN_LORA_RST, 0);
    vTaskDelay(pdMS_TO_TICKS(2));
    gpio_set_level(PIN_LORA_RST, 1);
    vTaskDelay(pdMS_TO_TICKS(10));

    uint8_t a[8];
    a[0] = 0x00;                                  /* STDBY_RC */
    ESP_RETURN_ON_ERROR(cmd(OP_SET_STANDBY, a, 1), TAG, "standby");
    a[0] = 0x01;                                  /* LoRa */
    ESP_RETURN_ON_ERROR(cmd(OP_SET_PACKET_TYPE, a, 1), TAG, "pkt type");
    a[0] = 0x01;                                  /* DC-DC regulator */
    cmd(OP_SET_REGULATOR_MODE, a, 1);
    a[0] = 0x01;                                  /* DIO2 = RF switch */
    cmd(OP_SET_DIO2_RF_SWITCH, a, 1);

    uint32_t frf = (uint32_t)FREQ_STEP_NUM;
    a[0] = frf >> 24; a[1] = frf >> 16; a[2] = frf >> 8; a[3] = frf;
    ESP_RETURN_ON_ERROR(cmd(OP_SET_RF_FREQUENCY, a, 4), TAG, "freq");

    a[0] = 0x04; a[1] = 0x07; a[2] = 0x00; a[3] = 0x01;  /* PA: SX1262 +14dBm class */
    cmd(OP_SET_PA_CONFIG, a, 4);
    a[0] = 14; a[1] = 0x04;                       /* +14 dBm, 200 us ramp */
    cmd(OP_SET_TX_PARAMS, a, 2);

    a[0] = 0x00; a[1] = 0x00;                     /* TX/RX buffer bases */
    cmd(OP_SET_BUF_BASE, a, 2);

    a[0] = 7;                                     /* SF7 */
    a[1] = 0x05;                                  /* BW 250 kHz */
    a[2] = 0x01;                                  /* CR 4/5 */
    a[3] = 0x00;                                  /* no low-data-rate opt */
    ESP_RETURN_ON_ERROR(cmd(OP_SET_MOD_PARAMS, a, 4), TAG, "mod");

    /* IRQs: TX_DONE + RX_DONE + CRC_ERR + TIMEOUT on DIO1 */
    uint16_t mask = IRQ_TX_DONE | IRQ_RX_DONE | IRQ_CRC_ERR | IRQ_TIMEOUT;
    a[0] = mask >> 8; a[1] = (uint8_t)mask;
    a[2] = mask >> 8; a[3] = (uint8_t)mask;
    a[4] = 0; a[5] = 0; a[6] = 0; a[7] = 0;
    cmd(OP_SET_DIO_IRQ, a, 8);

    s_ready = true;
    ESP_LOGI(TAG, "SX1262 up: 869.525 MHz SF7/BW250/CR4:5");
    return ESP_OK;
}

static void set_packet_len(uint8_t len)
{
    uint8_t a[6] = {0x00, 0x08,      /* preamble 8 */
                    0x00,            /* explicit header */
                    len, 0x01, 0x00}; /* CRC on, IQ normal */
    cmd(OP_SET_PKT_PARAMS, a, 6);
}

static uint16_t irq_status(void)
{
    uint8_t s[2] = {0};
    cmd_read(OP_GET_IRQ_STATUS, s, 2);
    return ((uint16_t)s[0] << 8) | s[1];
}

static void irq_clear(uint16_t m)
{
    uint8_t a[2] = {(uint8_t)(m >> 8), (uint8_t)m};
    cmd(OP_CLR_IRQ_STATUS, a, 2);
}

bool sx1262_send(const uint8_t *data, uint8_t len, uint32_t timeout_ms)
{
    if (!s_ready || len == 0) return false;
    set_packet_len(len);
    wait_busy();
    uint8_t buf[2 + 64];
    buf[0] = OP_WRITE_BUFFER;
    buf[1] = 0x00;
    memcpy(&buf[2], data, len);
    spi_transaction_t t = {.length = 8 * (len + 2), .tx_buffer = buf};
    if (spi_device_transmit(g_spi_lora, &t) != ESP_OK) return false;
    uint8_t a[3] = {0x00, 0x00, 0x00};            /* no TX timeout */
    cmd(OP_SET_TX, a, 3);
    for (uint32_t i = 0; i < timeout_ms; i++) {
        if (gpio_get_level(PIN_LORA_DIO1)) {
            uint16_t s = irq_status();
            irq_clear(0xFFFF);
            return (s & IRQ_TX_DONE) != 0;
        }
        vTaskDelay(1);
    }
    return false;
}

void sx1262_rx_start(void)
{
    if (!s_ready) return;
    set_packet_len(64);
    uint8_t a[3] = {0xFF, 0xFF, 0xFF};            /* continuous RX */
    cmd(OP_SET_RX, a, 3);
}

int sx1262_receive(uint8_t out[64], int *rssi_dbm)
{
    if (!s_ready || !gpio_get_level(PIN_LORA_DIO1)) return 0;
    uint16_t s = irq_status();
    irq_clear(0xFFFF);
    if (!(s & IRQ_RX_DONE) || (s & IRQ_CRC_ERR)) return 0;
    uint8_t st[2] = {0};
    cmd_read(OP_GET_RX_BUF_STATUS, st, 2);        /* [len, offset] */
    uint8_t len = st[0], off = st[1];
    if (len == 0 || len > 64) return 0;
    wait_busy();
    uint8_t tx[3 + 64] = {OP_READ_BUFFER, off, 0x00};
    uint8_t rx[3 + 64] = {0};
    spi_transaction_t t = {.length = 8 * (len + 3), .tx_buffer = tx, .rx_buffer = rx};
    if (spi_device_transmit(g_spi_lora, &t) != ESP_OK) return 0;
    memcpy(out, &rx[3], len);
    if (rssi_dbm) {
        uint8_t ps[3] = {0};
        cmd_read(OP_GET_PKT_STATUS, ps, 3);
        *rssi_dbm = -(int)ps[0] / 2;
    }
    return len;
}

#endif /* BOARD_HAS_LORA */
