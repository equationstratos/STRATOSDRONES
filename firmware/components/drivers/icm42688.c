/* ICM-42688-P 6-axis IMU driver (SPI).
 * Register addresses/values from TDK DS-000347 datasheet (facts, not code).
 * Config: gyro 2000 dps @1 kHz, accel 16 g @1 kHz, low-noise mode, INT1
 * push-pull active-high pulsed on UI data ready.
 * SPDX-License-Identifier: MIT */
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "board_pinmap.h"
#include "drivers.h"
#include "esp_log.h"
#include "fc_core/fc_math.h"
#include "freertos/FreeRTOS.h"

static const char *TAG = "icm42688";
extern spi_device_handle_t g_spi_imu;
esp_err_t spi_reg_write(spi_device_handle_t dev, uint8_t reg, uint8_t val);
esp_err_t spi_reg_read(spi_device_handle_t dev, uint8_t reg, uint8_t *buf, size_t n);

#define REG_WHO_AM_I      0x75 /* = 0x47 */
#define REG_DEVICE_CONFIG 0x11
#define REG_INT_CONFIG    0x14
#define REG_TEMP_DATA1    0x1D
#define REG_PWR_MGMT0     0x4E
#define REG_GYRO_CONFIG0  0x4F
#define REG_ACCEL_CONFIG0 0x50
#define REG_GYRO_ACCEL_CONFIG0 0x52
#define REG_INT_CONFIG1   0x64
#define REG_INT_SOURCE0   0x65

#define GYRO_SCALE  (2000.0f / 32768.0f * FC_DEG2RAD) /* rad/s per LSB */
#define ACCEL_SCALE (16.0f * FC_G / 32768.0f)         /* m/s^2 per LSB */

static volatile bool s_drdy;

static void IRAM_ATTR drdy_isr(void *arg)
{
    (void)arg;
    s_drdy = true;
}

bool icm42688_data_ready(void)
{
    bool v = s_drdy;
    s_drdy = false;
    return v;
}

esp_err_t icm42688_init(void)
{
    uint8_t id = 0;
    spi_reg_write(g_spi_imu, REG_DEVICE_CONFIG, 0x01); /* soft reset */
    vTaskDelay(pdMS_TO_TICKS(2));
    spi_reg_read(g_spi_imu, REG_WHO_AM_I, &id, 1);
    if (id != 0x47) {
        ESP_LOGE(TAG, "WHO_AM_I=0x%02x (want 0x47)", id);
        return ESP_ERR_NOT_FOUND;
    }
    spi_reg_write(g_spi_imu, REG_GYRO_CONFIG0, 0x06);  /* 2000 dps, ODR 1 kHz */
    spi_reg_write(g_spi_imu, REG_ACCEL_CONFIG0, 0x06); /* 16 g, ODR 1 kHz */
    spi_reg_write(g_spi_imu, REG_GYRO_ACCEL_CONFIG0, 0x44); /* UI filter BW = ODR/10 */
    spi_reg_write(g_spi_imu, REG_INT_CONFIG, 0x03);    /* INT1 push-pull, active high */
    spi_reg_write(g_spi_imu, REG_INT_SOURCE0, 0x08);   /* UI data-ready -> INT1 */
    spi_reg_write(g_spi_imu, REG_PWR_MGMT0, 0x0F);     /* gyro+accel low-noise */
    vTaskDelay(pdMS_TO_TICKS(2));                      /* 200 us min after PWR_MGMT0 */

    gpio_config_t io = {
        .pin_bit_mask = 1ULL << PIN_IMU_INT,
        .mode = GPIO_MODE_INPUT,
        .intr_type = GPIO_INTR_POSEDGE,
    };
    gpio_config(&io);
    gpio_install_isr_service(0);
    gpio_isr_handler_add(PIN_IMU_INT, drdy_isr, NULL);
    ESP_LOGI(TAG, "ready (2000 dps / 16 g @ 1 kHz)");
    return ESP_OK;
}

esp_err_t icm42688_read(imu_sample_t *out)
{
    /* TEMP(2) ACCEL xyz(6) GYRO xyz(6) starting at 0x1D */
    uint8_t b[14];
    esp_err_t err = spi_reg_read(g_spi_imu, REG_TEMP_DATA1, b, sizeof(b));
    if (err != ESP_OK) return err;
    int16_t t = (int16_t)((b[0] << 8) | b[1]);
    int16_t ax = (int16_t)((b[2] << 8) | b[3]);
    int16_t ay = (int16_t)((b[4] << 8) | b[5]);
    int16_t az = (int16_t)((b[6] << 8) | b[7]);
    int16_t gx = (int16_t)((b[8] << 8) | b[9]);
    int16_t gy = (int16_t)((b[10] << 8) | b[11]);
    int16_t gz = (int16_t)((b[12] << 8) | b[13]);
    out->temp_c = (float)t / 132.48f + 25.0f;
    /* IMU axes -> body FLU mapping for PCB rev A (IMU x = body x fwd,
     * IMU y = body y left, IMU z = body z up; adjust here if layout rotates) */
    out->accel[0] = ax * ACCEL_SCALE;
    out->accel[1] = ay * ACCEL_SCALE;
    out->accel[2] = az * ACCEL_SCALE;
    out->gyro[0] = gx * GYRO_SCALE;
    out->gyro[1] = gy * GYRO_SCALE;
    out->gyro[2] = gz * GYRO_SCALE;
    return ESP_OK;
}
