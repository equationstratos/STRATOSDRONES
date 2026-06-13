/* Shared SPI/I2C bus bring-up. SPDX-License-Identifier: MIT */
#include "driver/i2c_master.h"
#include "driver/spi_master.h"
#include "board_pinmap.h"
#include "drivers.h"
#include "esp_log.h"

static const char *TAG = "buses";

i2c_master_bus_handle_t g_i2c_bus;
spi_device_handle_t g_spi_imu;
spi_device_handle_t g_spi_flow;

esp_err_t board_buses_init(void)
{
    const spi_bus_config_t buscfg = {
        .sclk_io_num = PIN_SPI_SCLK,
        .mosi_io_num = PIN_SPI_MOSI,
        .miso_io_num = PIN_SPI_MISO,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 64,
    };
    ESP_RETURN_ON_ERROR(spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO),
                        TAG, "spi bus");

    const spi_device_interface_config_t imu_cfg = {
        .clock_speed_hz = 8 * 1000 * 1000,   /* ICM-42688-P max 24 MHz */
        .mode = 3,
        .spics_io_num = PIN_CS_IMU,
        .queue_size = 2,
    };
    ESP_RETURN_ON_ERROR(spi_bus_add_device(SPI2_HOST, &imu_cfg, &g_spi_imu),
                        TAG, "imu dev");

    const spi_device_interface_config_t flow_cfg = {
        .clock_speed_hz = 2 * 1000 * 1000,   /* PMW3901 max 2 MHz */
        .mode = 3,
        .spics_io_num = PIN_CS_FLOW,
        .cs_ena_pretrans = 4,                /* PMW3901 wants CS setup time */
        .cs_ena_posttrans = 4,
        .queue_size = 2,
    };
    ESP_RETURN_ON_ERROR(spi_bus_add_device(SPI2_HOST, &flow_cfg, &g_spi_flow),
                        TAG, "flow dev");

    const i2c_master_bus_config_t i2c_cfg = {
        .i2c_port = 0,
        .sda_io_num = PIN_I2C_SDA,
        .scl_io_num = PIN_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true, /* board has external 4.7k too */
    };
    ESP_RETURN_ON_ERROR(i2c_new_master_bus(&i2c_cfg, &g_i2c_bus), TAG, "i2c bus");
    ESP_LOGI(TAG, "buses up (SPI2 @8/2 MHz, I2C0 @400 kHz)");
    return ESP_OK;
}

/* small helpers shared by SPI sensor drivers */
esp_err_t spi_reg_write(spi_device_handle_t dev, uint8_t reg, uint8_t val)
{
    uint8_t tx[2] = {(uint8_t)(reg & 0x7F), val};
    spi_transaction_t t = {.length = 16, .tx_buffer = tx};
    return spi_device_polling_transmit(dev, &t);
}

esp_err_t spi_reg_read(spi_device_handle_t dev, uint8_t reg, uint8_t *buf, size_t n)
{
    uint8_t tx[1 + 16] = {(uint8_t)(reg | 0x80)};
    uint8_t rx[1 + 16] = {0};
    if (n > 16) return ESP_ERR_INVALID_ARG;
    spi_transaction_t t = {
        .length = 8 * (1 + n),
        .tx_buffer = tx,
        .rx_buffer = rx,
    };
    esp_err_t err = spi_device_polling_transmit(dev, &t);
    for (size_t i = 0; i < n; i++) buf[i] = rx[1 + i];
    return err;
}
