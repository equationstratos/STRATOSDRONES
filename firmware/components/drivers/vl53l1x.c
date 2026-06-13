/* VL53L1X time-of-flight ranger (I2C 0x29), compact driver.
 *
 * The 0x2D..0x87 default configuration block and register map are from
 * STMicroelectronics' "VL53L1X ULD" (UM2510 / STSW-IMG009), licensed
 * BSD-3-Clause by ST — reproduced here with attribution as permitted.
 * Mode: long distance, 33 ms timing budget, ~50 Hz intermeasurement.
 * SPDX-License-Identifier: MIT AND BSD-3-Clause */
#include "driver/i2c_master.h"
#include "board_pinmap.h"
#include "drivers.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"

static const char *TAG = "vl53l1x";
extern i2c_master_bus_handle_t g_i2c_bus;
static i2c_master_dev_handle_t s_dev;

static const uint8_t k_default_cfg[] = { /* index 0x2D..0x87 (ST ULD) */
    0x00, 0x00, 0x00, 0x01, 0x02, 0x00, 0x02, 0x08, 0x00, 0x08, 0x10, 0x01,
    0x01, 0x00, 0x00, 0x00, 0x00, 0xff, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x20, 0x0b, 0x00, 0x00, 0x02, 0x0a, 0x21, 0x00, 0x00, 0x05, 0x00,
    0x00, 0x00, 0x00, 0xc8, 0x00, 0x00, 0x38, 0xff, 0x01, 0x00, 0x08, 0x00,
    0x00, 0x01, 0xdb, 0x0f, 0x01, 0xf1, 0x0d, 0x01, 0x68, 0x00, 0x80, 0x08,
    0xb8, 0x00, 0x00, 0x00, 0x00, 0x0f, 0x89, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x07, 0x05, 0x06, 0x06, 0x00, 0x00, 0x02, 0xc7, 0xff,
    0x9B, 0x00, 0x00, 0x00, 0x01, 0x01, 0x40
};

static esp_err_t wr16(uint16_t reg, const uint8_t *data, size_t n)
{
    uint8_t buf[2 + 8];
    if (n > 8) return ESP_ERR_INVALID_ARG;
    buf[0] = reg >> 8;
    buf[1] = reg & 0xFF;
    for (size_t i = 0; i < n; i++) buf[2 + i] = data[i];
    return i2c_master_transmit(s_dev, buf, 2 + n, 50);
}

static esp_err_t wr8(uint16_t reg, uint8_t v) { return wr16(reg, &v, 1); }

static esp_err_t rd(uint16_t reg, uint8_t *data, size_t n)
{
    uint8_t a[2] = {reg >> 8, reg & 0xFF};
    return i2c_master_transmit_receive(s_dev, a, 2, data, n, 50);
}

esp_err_t vl53l1x_init(void)
{
    const i2c_device_config_t cfg = {
        .device_address = 0x29,
        .scl_speed_hz = 400000,
    };
    ESP_RETURN_ON_ERROR(i2c_master_bus_add_device(g_i2c_bus, &cfg, &s_dev),
                        TAG, "add dev");
    uint8_t id[2] = {0};
    rd(0x010F, id, 2); /* model id+type: 0xEA 0xCC */
    if (id[0] != 0xEA) {
        ESP_LOGE(TAG, "model id 0x%02x%02x", id[0], id[1]);
        return ESP_ERR_NOT_FOUND;
    }
    /* wait for firmware boot */
    uint8_t st = 0;
    for (int i = 0; i < 100 && !(st & 0x01); i++) {
        rd(0x00E5, &st, 1); /* FIRMWARE__SYSTEM_STATUS */
        vTaskDelay(pdMS_TO_TICKS(2));
    }
    for (size_t i = 0; i < sizeof(k_default_cfg); i++)
        wr8(0x2D + i, k_default_cfg[i]);

    /* long-distance mode + ~33 ms budget (ULD values) */
    wr8(0x004B, 0x0A); /* PHASECAL_CONFIG__TIMEOUT_MACROP */
    wr8(0x0060, 0x0F); /* RANGE_CONFIG__VCSEL_PERIOD_A */
    wr8(0x0063, 0x0D); /* RANGE_CONFIG__VCSEL_PERIOD_B */
    wr8(0x0069, 0xB8); /* SD_CONFIG__WOI etc. per ULD long mode */
    uint8_t to_a[2] = {0x00, 0xD6}, to_b[2] = {0x00, 0xC6};
    wr16(0x005E, to_a, 2); /* RANGE_CONFIG__TIMEOUT_MACROP_A */
    wr16(0x0061, to_b, 2); /* RANGE_CONFIG__TIMEOUT_MACROP_B */
    uint8_t im[4] = {0, 0, 0x07, 0xD0}; /* ~20 ms intermeasurement ticks */
    wr16(0x006C, im, 4);

    wr8(0x0087, 0x40); /* RANGING_ENABLE: start continuous */
    ESP_LOGI(TAG, "ranging started");
    return ESP_OK;
}

bool vl53l1x_read(uint16_t *range_mm, bool *valid)
{
    uint8_t rdy = 0;
    rd(0x0031, &rdy, 1); /* GPIO__TIO_HV_STATUS, bit0 == 0 -> data ready */
    if ((rdy & 0x01) != 0) return false;
    uint8_t b[2], status = 0;
    rd(0x0089, &status, 1); /* RESULT__RANGE_STATUS */
    rd(0x0096, b, 2);       /* final corrected range, mm */
    *range_mm = ((uint16_t)b[0] << 8) | b[1];
    /* ULD: status 9 (RANGECOMPLETE) is the good one */
    *valid = (status & 0x1F) == 9;
    wr8(0x0086, 0x01); /* SYSTEM__INTERRUPT_CLEAR */
    return true;
}
