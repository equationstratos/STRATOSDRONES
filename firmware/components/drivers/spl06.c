/* SPL06-001 barometric pressure sensor (I2C 0x76).
 * Compensation math per Goertek SPL06-001 datasheet rev 1.x.
 * Config: pressure 64 Hz x8 oversampling, temperature 8 Hz x1.
 * SPDX-License-Identifier: MIT */
#include "driver/i2c_master.h"
#include "drivers.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"

static const char *TAG = "spl06";
extern i2c_master_bus_handle_t g_i2c_bus;
static i2c_master_dev_handle_t s_dev;

static struct {
    int16_t c0, c1;
    int32_t c00, c10;
    int16_t c01, c11, c20, c21, c30;
    float kp, kt;
    float t_raw_sc;
} s_cal;

static esp_err_t wr(uint8_t reg, uint8_t v)
{
    uint8_t b[2] = {reg, v};
    return i2c_master_transmit(s_dev, b, 2, 50);
}
static esp_err_t rd(uint8_t reg, uint8_t *d, size_t n)
{
    return i2c_master_transmit_receive(s_dev, &reg, 1, d, n, 50);
}

static int32_t s24(uint32_t v) { return (v & 0x800000) ? (int32_t)(v | 0xFF000000u) : (int32_t)v; }
static int16_t s12(uint16_t v) { return (v & 0x800) ? (int16_t)(v | 0xF000u) : (int16_t)v; }
static int32_t s20(uint32_t v) { return (v & 0x80000) ? (int32_t)(v | 0xFFF00000u) : (int32_t)v; }

esp_err_t spl06_init(void)
{
    const i2c_device_config_t cfg = {.device_address = 0x76, .scl_speed_hz = 400000};
    ESP_RETURN_ON_ERROR(i2c_master_bus_add_device(g_i2c_bus, &cfg, &s_dev), TAG, "add");
    uint8_t id = 0;
    rd(0x0D, &id, 1);
    if ((id >> 4) != 0x1) {
        ESP_LOGE(TAG, "bad id 0x%02x", id);
        return ESP_ERR_NOT_FOUND;
    }
    /* wait for coefficients ready */
    uint8_t st = 0;
    for (int i = 0; i < 50 && !(st & 0x80); i++) {
        rd(0x08, &st, 1);
        vTaskDelay(pdMS_TO_TICKS(3));
    }
    uint8_t c[18];
    rd(0x10, c, 18);
    s_cal.c0 = s12(((uint16_t)c[0] << 4) | (c[1] >> 4));
    s_cal.c1 = s12((((uint16_t)c[1] & 0x0F) << 8) | c[2]);
    s_cal.c00 = s20(((uint32_t)c[3] << 12) | ((uint32_t)c[4] << 4) | (c[5] >> 4));
    s_cal.c10 = s20((((uint32_t)c[5] & 0x0F) << 16) | ((uint32_t)c[6] << 8) | c[7]);
    s_cal.c01 = (int16_t)(((uint16_t)c[8] << 8) | c[9]);
    s_cal.c11 = (int16_t)(((uint16_t)c[10] << 8) | c[11]);
    s_cal.c20 = (int16_t)(((uint16_t)c[12] << 8) | c[13]);
    s_cal.c21 = (int16_t)(((uint16_t)c[14] << 8) | c[15]);
    s_cal.c30 = (int16_t)(((uint16_t)c[16] << 8) | c[17]);

    wr(0x06, 0x63);      /* PRS_CFG: 64 Hz, 8x oversample */
    wr(0x07, 0x80 | 0x30); /* TMP_CFG: external sensor, 8 Hz, 1x */
    wr(0x09, 0x00);      /* CFG_REG: no shift needed for 8x */
    wr(0x08, 0x07);      /* MEAS_CFG: continuous pressure + temperature */
    s_cal.kp = 7864320.0f; /* scale factor for 8x oversampling */
    s_cal.kt = 524288.0f;  /* 1x */
    ESP_LOGI(TAG, "ready (64 Hz x8)");
    return ESP_OK;
}

bool spl06_read(float *pressure_pa, float *temp_c)
{
    uint8_t b[6];
    if (rd(0x00, b, 6) != ESP_OK) return false;
    float p_raw = (float)s24(((uint32_t)b[0] << 16) | ((uint32_t)b[1] << 8) | b[2]) / s_cal.kp;
    float t_raw = (float)s24(((uint32_t)b[3] << 16) | ((uint32_t)b[4] << 8) | b[5]) / s_cal.kt;
    *temp_c = 0.5f * s_cal.c0 + s_cal.c1 * t_raw;
    *pressure_pa = s_cal.c00 +
        p_raw * (s_cal.c10 + p_raw * (s_cal.c20 + p_raw * s_cal.c30)) +
        t_raw * s_cal.c01 + t_raw * p_raw * (s_cal.c11 + p_raw * s_cal.c21);
    return true;
}
