/* STRATOSDRONE firmware entry point (ESP32-P4).
 * Core 0: flight loop. Core 1: Wi-Fi (hosted C6), SDK UDP, video.
 * SPDX-License-Identifier: MIT */
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

#include "drivers.h"
#include "board_select.h"
#include "stratos.h"

static const char *TAG = "main";

QueueHandle_t g_cmd_queue, g_reply_queue, g_state_queue;
QueueHandle_t g_crsf_queue;
_Atomic uint32_t g_client_ip = 0;
volatile lorap_telem_t g_lora_telem;
_Atomic uint8_t g_lora_drone_id = 1;
_Atomic uint8_t g_lora_swarm_id = 0;

void app_main(void)
{
    ESP_LOGI(TAG, "STRATOSDRONE fw %s", STRATOS_VERSION);

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
    }

    g_cmd_queue = xQueueCreate(8, sizeof(sdk_msg_t));
    g_reply_queue = xQueueCreate(8, sizeof(sdk_msg_t));
    g_state_queue = xQueueCreate(4, sizeof(sdk_msg_t));
    g_crsf_queue = xQueueCreate(1, sizeof(crsf_channels_t)); /* latest-only */

    /* hardware bring-up: motors first so the pins are driven low ASAP */
#if BOARD_HAS_DSHOT
    ESP_ERROR_CHECK(dshot_init());
    dshot_kill();
#else
    ESP_ERROR_CHECK(motors_init());
    motors_kill();
#endif
    ESP_ERROR_CHECK(board_buses_init());
    leds_init();
    leds_set(24, 12, 0); /* amber: booting */
    vbat_init();

    bool sensors_ok = true;
    sensors_ok &= icm42688_init() == ESP_OK;
    sensors_ok &= pmw3901_init() == ESP_OK;
    sensors_ok &= vl53l1x_init() == ESP_OK;
    sensors_ok &= spl06_init() == ESP_OK;
    if (!sensors_ok) {
        ESP_LOGE(TAG, "sensor init failed — flight inhibited, check bringup.md");
        leds_set(64, 0, 0);
        /* keep network up for diagnostics, but never start the flight task */
    }

    wifi_link_start();
    xTaskCreatePinnedToCore(net_task, "net", 4096, NULL, 10, NULL, 1);
    video_task_start();

#if BOARD_HAS_CRSF
    xTaskCreatePinnedToCore(crsf_task, "crsf", 3072, NULL, 12, NULL, 1);
#endif
#if BOARD_HAS_LORA
    xTaskCreatePinnedToCore(lora_task, "lora", 4096, NULL, 9, NULL, 1);
#endif
    ESP_LOGI(TAG, "board: %s", BOARD_NAME);

    if (sensors_ok)
        xTaskCreatePinnedToCore(flight_task, "flight", 8192, NULL,
                                configMAX_PRIORITIES - 2, NULL, 0);
}
