/* Sensor / actuator drivers for the STRATOSDRONE board (ESP32-P4).
 * Register-level implementations from the component datasheets (see each .c).
 * SPDX-License-Identifier: MIT */
#ifndef STRATOS_DRIVERS_H
#define STRATOS_DRIVERS_H

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

/* ---- ICM-42688-P IMU (SPI) ---- */
typedef struct {
    float gyro[3];   /* rad/s, remapped to body FLU */
    float accel[3];  /* m/s^2 */
    float temp_c;
} imu_sample_t;

esp_err_t icm42688_init(void);                 /* 1 kHz ODR, 2000 dps, 16 g */
esp_err_t icm42688_read(imu_sample_t *out);
bool icm42688_data_ready(void);                /* INT1 latched flag */

/* ---- PMW3901 optical flow (SPI) ---- */
typedef struct {
    int16_t dx, dy;
    uint8_t squal;
} flow_sample_t;

esp_err_t pmw3901_init(void);
esp_err_t pmw3901_read(flow_sample_t *out);    /* motion burst, accumulated */

/* ---- VL53L1X ToF (I2C) ---- */
esp_err_t vl53l1x_init(void);                  /* long range, ~50 Hz */
bool vl53l1x_read(uint16_t *range_mm, bool *valid);

/* ---- SPL06-001 barometer (I2C) ---- */
esp_err_t spl06_init(void);                    /* 64 Hz, 8x oversample */
bool spl06_read(float *pressure_pa, float *temp_c);

/* ---- brushed motors (LEDC, 20 kHz) ---- */
esp_err_t motors_init(void);
void motors_write(const float duty[4]);        /* 0..1, M1..M4 */
void motors_kill(void);

/* ---- brushless DShot600 (RMT, TinyHoop AIO) ---- */
esp_err_t dshot_init(void);
void dshot_write(const float duty[4]);         /* 0..1, M1..M4 */
void dshot_kill(void);

/* ---- SX1262 LoRa (SPI2, EU868; TinyHoop AIO) ---- */
esp_err_t sx1262_init(void);
bool sx1262_send(const uint8_t *data, uint8_t len, uint32_t timeout_ms);
void sx1262_rx_start(void);
int  sx1262_receive(uint8_t out[64], int *rssi_dbm); /* bytes, 0 = none */

/* ---- battery voltage (ADC + divider) ---- */
esp_err_t vbat_init(void);
float vbat_read(void);                         /* volts */

/* ---- WS2812 status LEDs ---- */
esp_err_t leds_init(void);
void leds_set(uint8_t r, uint8_t g, uint8_t b);

/* shared buses, called once before sensor inits */
esp_err_t board_buses_init(void);

#endif
