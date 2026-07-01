/* Wi-Fi via ESP32-C6 co-processor (esp-hosted over SDIO + esp_wifi_remote).
 *
 * The esp_wifi_remote component transparently maps the esp_wifi_* API onto
 * the hosted C6, so this file looks like normal ESP32 Wi-Fi code. Default:
 * open softAP "STRATOS-XXXXXX" (Tello-style). "ap <ssid> <pass>" switches to
 * station mode (swarm); "wifi <ssid> <pass>" re-keys the AP. Both persist in
 * NVS and reboot, like the real Tello.
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "esp_event.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs.h"

#include "stratos.h"

static const char *TAG = "wifi_link";

/* power save off: control latency matters more than idle current */
static void common_wifi_up(void)
{
    esp_wifi_set_ps(WIFI_PS_NONE);
    ESP_ERROR_CHECK(esp_wifi_start());
}

void wifi_link_start(void)
{
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    nvs_handle_t nvs;
    char ssid[33] = "", pass[65] = "";
    uint8_t sta_mode = 0;
    if (nvs_open("wifi", NVS_READONLY, &nvs) == ESP_OK) {
        size_t sl = sizeof(ssid), pl = sizeof(pass);
        nvs_get_str(nvs, "ssid", ssid, &sl);
        nvs_get_str(nvs, "pass", pass, &pl);
        nvs_get_u8(nvs, "sta", &sta_mode);
        nvs_close(nvs);
    }

    if (sta_mode && ssid[0]) {
        esp_netif_create_default_wifi_sta();
        wifi_config_t wc = {0};
        strlcpy((char *)wc.sta.ssid, ssid, sizeof(wc.sta.ssid));
        strlcpy((char *)wc.sta.password, pass, sizeof(wc.sta.password));
        ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
        ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wc));
        common_wifi_up();
        esp_wifi_connect();
        ESP_LOGI(TAG, "STA mode, joining '%s' (swarm)", ssid);
    } else {
        esp_netif_t *ap_netif = esp_netif_create_default_wifi_ap();
        /* Pin the AP to the real Tello's address (192.168.10.1), not the
         * ESP-IDF default (192.168.4.1) — every Tello SDK client, incl.
         * djitellopy and this repo's own docs, hardcodes the Tello IP. */
        ESP_ERROR_CHECK(esp_netif_dhcps_stop(ap_netif));
        esp_netif_ip_info_t ip_info = {
            .ip      = { .addr = ESP_IP4TOADDR(192, 168, 10, 1) },
            .gw      = { .addr = ESP_IP4TOADDR(192, 168, 10, 1) },
            .netmask = { .addr = ESP_IP4TOADDR(255, 255, 255, 0) },
        };
        ESP_ERROR_CHECK(esp_netif_set_ip_info(ap_netif, &ip_info));
        ESP_ERROR_CHECK(esp_netif_dhcps_start(ap_netif));
        uint8_t mac[6];
        esp_read_mac(mac, ESP_MAC_WIFI_SOFTAP);
        wifi_config_t wc = {0};
        if (!ssid[0])
            snprintf((char *)wc.ap.ssid, sizeof(wc.ap.ssid),
                     "STRATOS-%02X%02X%02X", mac[3], mac[4], mac[5]);
        else
            strlcpy((char *)wc.ap.ssid, ssid, sizeof(wc.ap.ssid));
        wc.ap.ssid_len = strlen((char *)wc.ap.ssid);
        wc.ap.channel = 6;
        wc.ap.max_connection = 4;
        if (pass[0]) {
            strlcpy((char *)wc.ap.password, pass, sizeof(wc.ap.password));
            wc.ap.authmode = WIFI_AUTH_WPA2_PSK;
        } else {
            wc.ap.authmode = WIFI_AUTH_OPEN; /* Tello-style open AP */
        }
        ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
        ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &wc));
        common_wifi_up();
        ESP_LOGI(TAG, "AP mode '%s' (open=%d)", wc.ap.ssid, !pass[0]);
    }
}

static void reboot_task(void *arg)
{
    (void)arg;
    vTaskDelay(pdMS_TO_TICKS(2000)); /* let the "ok" reply leave first */
    esp_restart();
}

bool wifi_link_set_config(const char *ssid, const char *pass, bool sta_mode)
{
    nvs_handle_t nvs;
    if (nvs_open("wifi", NVS_READWRITE, &nvs) != ESP_OK) return false;
    nvs_set_str(nvs, "ssid", ssid);
    nvs_set_str(nvs, "pass", pass);
    nvs_set_u8(nvs, "sta", sta_mode ? 1 : 0);
    nvs_commit(nvs);
    nvs_close(nvs);
    ESP_LOGW(TAG, "wifi config saved (%s '%s'), rebooting in 2 s",
             sta_mode ? "STA" : "AP", ssid);
    xTaskCreate(reboot_task, "reboot", 2048, NULL, 1, NULL);
    return true;
}

int wifi_link_rssi(void)
{
    wifi_ap_record_t ap;
    if (esp_wifi_sta_get_ap_info(&ap) == ESP_OK)
        return ap.rssi + 100; /* Tello "wifi?" returns a 0..100-ish SNR */
    return 90; /* AP mode: clients connect to us */
}
