/* LoRa fleet-link task (TinyHoop AIO) — core 1. Bridges the SX1262 radio
 * and the transport-free SDK/show layer:
 *
 *   RX frame -> fc_lorap_decode -> {CMD_LINE, TIME_BEACON, SWARM_START/ABORT,
 *               SHOW_CHUNK} translated into SDK ASCII lines -> g_cmd_queue
 *   TX       <- g_reply_queue (as RESP_LINE, when Wi-Fi has no client)
 *            <- g_lora_telem  (as TELEM, 2 Hz in this drone's TDMA slot)
 *
 * Translating binary frames into the same ASCII verbs the Wi-Fi path uses
 * (timesync, show start/stop/key, go, rc, ...) means the whole choreography
 * pipeline is one code path across Wi-Fi/SITL/Gazebo and LoRa. LoRa carries
 * commands/telemetry/choreography — never the piloting sticks (that is ELRS).
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include <stdio.h>
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "board_select.h"

#if BOARD_HAS_LORA

#include "drivers.h"
#include "fc_core/fc_lorap.h"
#include "stratos.h"

static const char *TAG = "lora";

static void push_line(const char *line)
{
    sdk_msg_t m;
    strlcpy(m.line, line, sizeof(m.line));
    xQueueSend(g_cmd_queue, &m, 0);
}

/* fc_sdk only reacts after "command"; make sure the mode is entered once. */
static void ensure_sdk_mode(void)
{
    static bool sent;
    if (!sent) { push_line("command"); sent = true; }
}

static void handle_frame(const lorap_frame_t *f)
{
    uint8_t me = atomic_load(&g_lora_drone_id);
    uint8_t sw = atomic_load(&g_lora_swarm_id);
    if (f->swarm_id != sw) return;                 /* another fleet */
    if (f->dst != LORAP_BROADCAST && f->dst != me) return;

    char line[SDK_LINE_MAX];
    switch (f->type) {
    case LORAP_CMD_LINE:
        ensure_sdk_mode();
        if (f->len < sizeof(line)) {
            memcpy(line, f->payload, f->len);
            line[f->len] = '\0';
            push_line(line);
        }
        break;
    case LORAP_TIME_BEACON:
        if (f->len >= 8) {
            uint64_t epoch = lorap_unpack_u64(f->payload);
            snprintf(line, sizeof(line), "timesync %llu",
                     (unsigned long long)epoch);
            ensure_sdk_mode();
            push_line(line);
        }
        break;
    case LORAP_SWARM_START:
        if (f->len >= 8) {
            uint64_t t0 = lorap_unpack_u64(f->payload);
            snprintf(line, sizeof(line), "show start %llu",
                     (unsigned long long)t0);
            ensure_sdk_mode();
            push_line("mode swarm");
            push_line(line);
        }
        break;
    case LORAP_SWARM_ABORT:
        ensure_sdk_mode();
        push_line("show stop");
        break;
    case LORAP_SHOW_CHUNK:
        /* payload: [first_idx u16][count u8][count x 12B keyframes]
         * keyframe = t_ms u32 | x_cm i16 | y_cm i16 | z_cm i16 | yaw_deg i16 */
        if (f->len >= 3) {
            uint8_t count = f->payload[2];
            const uint8_t *k = &f->payload[3];
            ensure_sdk_mode();
            for (uint8_t i = 0; i < count && (3 + (i + 1) * 12) <= f->len; i++) {
                uint32_t t = (uint32_t)k[0] | ((uint32_t)k[1] << 8) |
                             ((uint32_t)k[2] << 16) | ((uint32_t)k[3] << 24);
                int16_t x  = (int16_t)(k[4]  | (k[5] << 8));
                int16_t y  = (int16_t)(k[6]  | (k[7] << 8));
                int16_t z  = (int16_t)(k[8]  | (k[9] << 8));
                int16_t yw = (int16_t)(k[10] | (k[11] << 8));
                snprintf(line, sizeof(line), "show key %lu %d %d %d %d",
                         (unsigned long)t, x, y, z, yw);
                push_line(line);
                k += 12;
            }
        }
        break;
    default:
        break;
    }
}

static void send_frame(lorap_type_t type, uint8_t dst,
                       const uint8_t *payload, uint8_t len)
{
    lorap_frame_t f = {0};
    f.type = type;
    f.swarm_id = atomic_load(&g_lora_swarm_id);
    f.src = atomic_load(&g_lora_drone_id);
    f.dst = dst;
    f.len = len;
    if (len) memcpy(f.payload, payload, len);
    uint8_t buf[LORAP_MAX_FRAME];
    size_t n = lorap_encode(buf, &f);
    if (n) sx1262_send(buf, (uint8_t)n, 200);
}

void lora_task(void *arg)
{
    (void)arg;
    if (sx1262_init() != ESP_OK) {
        ESP_LOGE(TAG, "SX1262 init failed — fleet link down (solo build?)");
        vTaskDelete(NULL);
    }
    if (atomic_load(&g_lora_drone_id) == 0)
        atomic_store(&g_lora_drone_id, 1);         /* default id 1 */
    sx1262_rx_start();
    ESP_LOGI(TAG, "fleet link up as drone %u", atomic_load(&g_lora_drone_id));

    int64_t last_telem = 0;
    for (;;) {
        uint8_t rx[64];
        int rssi;
        int n = sx1262_receive(rx, &rssi);
        if (n > 0) {
            lorap_frame_t f;
            if (lorap_decode(rx, (size_t)n, &f))
                handle_frame(&f);
            sx1262_rx_start();
        }

        /* relay SDK replies over LoRa when Wi-Fi has no client (field mode) */
        if (atomic_load(&g_client_ip) == 0) {
            sdk_msg_t out;
            while (xQueueReceive(g_reply_queue, &out, 0) == pdTRUE) {
                size_t l = strlen(out.line);
                if (l > LORAP_MAX_PAYLOAD) l = LORAP_MAX_PAYLOAD;
                send_frame(LORAP_RESP_LINE, LORAP_ADDR_GROUND,
                           (const uint8_t *)out.line, (uint8_t)l);
                sx1262_rx_start();
            }
        }

        /* telemetry at 2 Hz, in this drone's TDMA slot */
        int64_t now = esp_timer_get_time();
        if (now - last_telem > 500000) {
            last_telem = now;
            lorap_telem_t t = g_lora_telem;        /* snapshot copy */
            uint8_t pl[LORAP_TELEM_LEN];
            lorap_pack_telem(pl, &t);
            send_frame(LORAP_TELEM, LORAP_ADDR_GROUND, pl, LORAP_TELEM_LEN);
            sx1262_rx_start();
        }
        vTaskDelay(1);
    }
}

#endif /* BOARD_HAS_LORA */
