/* board_pinmap.h — PROVISIONAL pin map (pre-PCB). The hardware generator
 * finalizes this file to match PCB rev A; macro names are the contract.
 * SPDX-License-Identifier: MIT */
#ifndef BOARD_PINMAP_H
#define BOARD_PINMAP_H

/* SPI bus (ICM-42688-P + PMW3901) */
#define PIN_SPI_SCLK   9
#define PIN_SPI_MOSI   10
#define PIN_SPI_MISO   11
#define PIN_CS_IMU     12
#define PIN_CS_FLOW    13
#define PIN_IMU_INT    21

/* I2C bus (SPL06-001 0x76, VL53L1X 0x29, camera SCCB) */
#define PIN_I2C_SDA    7
#define PIN_I2C_SCL    8
#define PIN_VL53_XSHUT 23

/* motors (M1 FR, M2 BR, M3 BL, M4 FL — see fc_core mixer) */
#define PIN_MOTOR_1    45
#define PIN_MOTOR_2    46
#define PIN_MOTOR_3    47
#define PIN_MOTOR_4    48

/* battery sense: 100k/100k divider */
#define PIN_VBAT_ADC     20
#define VBAT_ADC_UNIT    ADC_UNIT_1
#define VBAT_ADC_CHANNEL ADC_CHANNEL_4

/* misc */
#define PIN_WS2812     24
#define PIN_CAM_PWDN   25

/* SDIO link to ESP32-C6 (esp-hosted) — configured via sdkconfig */
#define PIN_SDIO_CLK   18
#define PIN_SDIO_CMD   19
#define PIN_SDIO_D0    14
#define PIN_SDIO_D1    15
#define PIN_SDIO_D2    16
#define PIN_SDIO_D3    17
#define PIN_C6_EN      54

#endif
