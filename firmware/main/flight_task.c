/* Flight task — core 0, highest priority. Owns fc_core + fc_sdk.
 * 1 kHz loop paced by the IMU data-ready interrupt (fallback: 1 ms timer).
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "fc_core/fc_core.h"
#include "fc_core/fc_sdk.h"
#include "drivers.h"
#include "stratos.h"

static const char *TAG = "flight";

static fc_core_t s_fc;
static fc_sdk_t s_sdk;
static char s_sn[24];

/* ---- fc_sdk platform callbacks (called from this task only) ---- */
static void cb_reply(void *u, const char *msg)
{
    (void)u;
    sdk_msg_t m;
    strlcpy(m.line, msg, sizeof(m.line));
    xQueueSend(g_reply_queue, &m, 0);
}
static void cb_video(void *u, bool on, int height)
{
    (void)u;
    atomic_store(&g_video_height, height);
    atomic_store(&g_video_on, on);
}
static void cb_led(void *u, uint8_t r, uint8_t g, uint8_t b)
{
    (void)u;
    leds_set(r, g, b);
}
static bool cb_wifi(void *u, const char *ssid, const char *pass, bool sta)
{
    (void)u;
    return wifi_link_set_config(ssid, pass, sta);
}
static const char *cb_sn(void *u) { (void)u; return s_sn; }
static int cb_snr(void *u) { (void)u; return wifi_link_rssi(); }

static const fc_sdk_platform_t k_plat = {
    .send_reply = cb_reply,
    .video_ctrl = cb_video,
    .set_led = cb_led,
    .wifi_config = cb_wifi,
    .get_sn = cb_sn,
    .get_wifi_snr = cb_snr,
};

void flight_task(void *arg)
{
    (void)arg;
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    snprintf(s_sn, sizeof(s_sn), "STRATOS%02X%02X%02X", mac[3], mac[4], mac[5]);

    fc_core_init(&s_fc);
    fc_sdk_init(&s_sdk, &s_fc, &k_plat, NULL);

    int64_t last_us = esp_timer_get_time();
    uint32_t tick = 0;
    float flow_dt = 0.0f;
    leds_set(0, 24, 0); /* green: ready */

    for (;;) {
        /* pace: IMU DRDY at 1 kHz; poll at 2 kHz so jitter stays < 0.5 ms */
        int waited = 0;
        while (!icm42688_data_ready() && waited++ < 4)
            vTaskDelay(1); /* CONFIG_FREERTOS_HZ=1000 -> 1 ms ticks */

        const int64_t now = esp_timer_get_time();
        float dt = (float)(now - last_us) * 1e-6f;
        last_us = now;
        if (dt <= 0.0f || dt > 0.05f) dt = 0.001f;
        flow_dt += dt;

        imu_sample_t imu;
        if (icm42688_read(&imu) == ESP_OK) {
            fc_imu_t s;
            memcpy(s.gyro, imu.gyro, sizeof(s.gyro));
            memcpy(s.accel, imu.accel, sizeof(s.accel));
            fc_core_imu_update(&s_fc, &s, dt);
        }

        if (tick % 10 == 3) { /* 100 Hz optical flow */
            flow_sample_t fl;
            if (pmw3901_read(&fl) == ESP_OK) {
                fc_flow_t f = {.dx = fl.dx, .dy = fl.dy, .quality = fl.squal};
                fc_core_flow_update(&s_fc, &f, flow_dt);
            }
            flow_dt = 0.0f;
        }
        if (tick % 20 == 7) { /* 50 Hz ToF */
            uint16_t mm;
            bool valid;
            if (vl53l1x_read(&mm, &valid))
                fc_core_tof_update(&s_fc, (float)mm * 0.001f, valid);
        }
        if (tick % 20 == 13) { /* 50 Hz baro */
            float pa, tc;
            if (spl06_read(&pa, &tc))
                fc_core_baro_update(&s_fc, pa);
        }
        if (tick % 100 == 51) /* 10 Hz battery */
            fc_core_battery_update(&s_fc, vbat_read());

        /* SDK plumbing */
        sdk_msg_t m;
        while (xQueueReceive(g_cmd_queue, &m, 0) == pdTRUE)
            fc_sdk_handle_line(&s_sdk, m.line);
        if (tick % 5 == 0)
            fc_sdk_poll(&s_sdk);
        if (tick % 100 == 0 && atomic_load(&g_client_ip) != 0) {
            sdk_msg_t st;
            fc_sdk_state_string(&s_sdk, st.line, sizeof(st.line));
            xQueueSend(g_state_queue, &st, 0);
        }

        /* motors out */
        float duty[4];
        fc_core_get_motors(&s_fc, duty);
        motors_write(duty);

        /* status LED: red on low battery, blue when flying */
        if (tick % 500 == 0) {
            if (s_fc.bat_pct < 15.0f) leds_set(48, 0, 0);
            else if (fc_core_state(&s_fc) != FC_ST_IDLE) leds_set(0, 0, 32);
        }
        tick++;
    }
    (void)TAG;
}
