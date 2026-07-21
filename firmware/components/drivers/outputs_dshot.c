/* DShot600 motor output on the ESP32-P4 RMT (4 TX channels).
 *
 * Frame: 11-bit throttle | telemetry-request bit | 4-bit CRC (xor of the
 * three nibbles), MSB first. Bit time 1.667 us (600 kbit/s): '1' = 1250 ns
 * high, '0' = 625 ns high. Values: 0 = disarmed, 48..2047 = throttle
 * (1..47 are BLHeli special commands — never emitted here).
 *
 * The flight loop calls dshot_write() at 1 kHz; while fc_core holds the
 * motors at 0 (IDLE/EMERGENCY) that continuous stream of zero-throttle
 * frames IS the BLHeli_S/Bluejay arming sequence. First bench spin can use
 * the LEDC driver instead (outputs.c) — ESCs also accept 1-2 kHz PWM.
 * VERIFY on hardware: RMT resolution rounding at 24 MHz, GPIO drive.
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "driver/rmt_tx.h"
#include "esp_check.h"
#include "esp_log.h"
#include "board_select.h"
#include "drivers.h"

static const char *TAG = "dshot";

#define DSHOT_RES_HZ  24000000    /* 41.67 ns ticks */
#define DSHOT_T1H     30          /* 1250 ns */
#define DSHOT_T1L     10          /*  417 ns */
#define DSHOT_T0H     15          /*  625 ns */
#define DSHOT_T0L     25          /* 1042 ns */

static rmt_channel_handle_t s_chan[4];
static rmt_encoder_handle_t s_copy_enc;
static bool s_ready;

static const int k_pins[4] = {PIN_MOTOR_1, PIN_MOTOR_2, PIN_MOTOR_3, PIN_MOTOR_4};

esp_err_t dshot_init(void)
{
    for (int i = 0; i < 4; i++) {
        const rmt_tx_channel_config_t cfg = {
            .gpio_num = k_pins[i],
            .clk_src = RMT_CLK_SRC_DEFAULT,
            .resolution_hz = DSHOT_RES_HZ,
            .mem_block_symbols = 64,
            .trans_queue_depth = 2,
        };
        ESP_RETURN_ON_ERROR(rmt_new_tx_channel(&cfg, &s_chan[i]), TAG, "chan");
        ESP_RETURN_ON_ERROR(rmt_enable(s_chan[i]), TAG, "enable");
    }
    const rmt_copy_encoder_config_t enc_cfg = {};
    ESP_RETURN_ON_ERROR(rmt_new_copy_encoder(&enc_cfg, &s_copy_enc), TAG, "enc");
    s_ready = true;
    ESP_LOGI(TAG, "DShot600 up on GPIO %d/%d/%d/%d",
             k_pins[0], k_pins[1], k_pins[2], k_pins[3]);
    return ESP_OK;
}

static uint16_t dshot_pack(float duty)
{
    uint16_t value = 0;                          /* 0 = disarmed */
    if (duty > 0.0f) {
        if (duty > 1.0f) duty = 1.0f;
        value = 48 + (uint16_t)(duty * (2047.0f - 48.0f));
    }
    uint16_t data = (uint16_t)(value << 1);      /* telemetry bit = 0 */
    uint16_t crc = (data ^ (data >> 4) ^ (data >> 8)) & 0x0F;
    return (uint16_t)((data << 4) | crc);
}

void dshot_write(const float duty[4])
{
    if (!s_ready) return;
    static rmt_symbol_word_t sym[4][16];
    const rmt_transmit_config_t tx_cfg = {.loop_count = 0};
    for (int m = 0; m < 4; m++) {
        uint16_t f = dshot_pack(duty[m]);
        for (int b = 0; b < 16; b++) {
            bool one = (f >> (15 - b)) & 1;
            sym[m][b].level0 = 1;
            sym[m][b].duration0 = one ? DSHOT_T1H : DSHOT_T0H;
            sym[m][b].level1 = 0;
            sym[m][b].duration1 = one ? DSHOT_T1L : DSHOT_T0L;
        }
        /* fire-and-forget: at 1 kHz the previous 27 us frame is long done */
        rmt_transmit(s_chan[m], s_copy_enc, sym[m], sizeof(sym[m]), &tx_cfg);
    }
}

void dshot_kill(void)
{
    const float zero[4] = {0, 0, 0, 0};
    dshot_write(zero);
}
