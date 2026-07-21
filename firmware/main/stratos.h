/* Shared task plumbing for the STRATOSDRONE firmware.
 *
 * Threading contract: fc_core/fc_sdk are single-threaded and live in the
 * flight task (core 0). The network task (core 1) only moves datagrams:
 *   net rx  -> cmd_queue  -> flight task (fc_sdk_handle_line)
 *   replies <- reply_queue <- flight task (fc_sdk send_reply callback)
 *   state   <- state_queue <- flight task @10 Hz
 * Video runs entirely on core 1 and is controlled via atomics.
 * SPDX-License-Identifier: MIT */
#ifndef STRATOS_H
#define STRATOS_H

#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "fc_core/fc_lorap.h"

#define STRATOS_VERSION "0.1.0"

#define SDK_LINE_MAX 128

typedef struct { char line[SDK_LINE_MAX]; } sdk_msg_t;

extern QueueHandle_t g_cmd_queue;    /* sdk_msg_t, net/lora -> flight */
extern QueueHandle_t g_reply_queue;  /* sdk_msg_t, flight -> net/lora */
extern QueueHandle_t g_state_queue;  /* sdk_msg_t, flight -> net */

/* CRSF channels: crsf_task decodes, flight task feeds fc_input_crsf().
 * 16 channels normalized -1..+1 (fc_mode.h order). */
typedef struct { float ch[16]; } crsf_channels_t;
extern QueueHandle_t g_crsf_queue;   /* crsf_channels_t, crsf -> flight */

/* client (last command sender) ip, network byte order; 0 = none */
extern _Atomic uint32_t g_client_ip;

/* video control (flight task writes, video task reads) */
extern _Atomic bool g_video_on;
extern _Atomic int g_video_height;   /* 720 | 1080 */

/* Telemetry snapshot: flight task writes @10 Hz, lora_task reads to build
 * TELEM frames. Benign single-writer/single-reader race (M0). */
extern volatile lorap_telem_t g_lora_telem;
extern _Atomic uint8_t g_lora_drone_id;   /* 1..250; TDMA slot + src addr */
extern _Atomic uint8_t g_lora_swarm_id;

void flight_task(void *arg);
void net_task(void *arg);
void crsf_task(void *arg);   /* TinyHoop: ELRS RX on UART */
void lora_task(void *arg);   /* TinyHoop: SX1262 fleet link */
void video_task_start(void);

/* wifi_link: brings up esp-hosted (ESP32-C6) and the netif */
void wifi_link_start(void);
bool wifi_link_set_config(const char *ssid, const char *pass, bool sta_mode);
int wifi_link_rssi(void);

#endif
