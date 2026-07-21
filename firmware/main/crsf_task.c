/* CRSF task (TinyHoop AIO) — core 1. Reads the ExpressLRS receiver on a
 * UART at 420 kbaud 8N1, runs the platform-free fc_crsf parser, and posts
 * decoded 16-channel frames to the flight task. The flight task applies
 * them via fc_input_crsf(); the 300 ms radio-loss failsafe lives inside
 * fc_mode.c (this task simply stops posting when frames stop arriving).
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "board_select.h"

#if BOARD_HAS_CRSF

#include "driver/uart.h"
#include "fc_core/fc_crsf.h"
#include "stratos.h"

static const char *TAG = "crsf";
#define CRSF_UART       UART_NUM_1
#define CRSF_BAUD       420000

void crsf_task(void *arg)
{
    (void)arg;
    const uart_config_t cfg = {
        .baud_rate = CRSF_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    uart_driver_install(CRSF_UART, 512, 0, 0, NULL, 0);
    uart_param_config(CRSF_UART, &cfg);
    uart_set_pin(CRSF_UART, PIN_CRSF_TX, PIN_CRSF_RX,
                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    ESP_LOGI(TAG, "ELRS/CRSF on UART%d rx=%d @%d", CRSF_UART, PIN_CRSF_RX, CRSF_BAUD);

    fc_crsf_t crsf;
    fc_crsf_init(&crsf);
    uint8_t buf[128];

    for (;;) {
        int n = uart_read_bytes(CRSF_UART, buf, sizeof(buf), pdMS_TO_TICKS(10));
        if (n <= 0) continue;
        if (fc_crsf_input(&crsf, buf, (size_t)n) > 0 && crsf.fresh) {
            crsf_channels_t m;
            fc_crsf_norm(&crsf, m.ch);
            xQueueOverwrite(g_crsf_queue, &m); /* keep only the latest frame */
        }
    }
}

#endif /* BOARD_HAS_CRSF */
