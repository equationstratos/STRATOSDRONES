/* fc_sdk.h — Tello SDK 2.0 wire-compatible command protocol (transport-free).
 *
 * The platform (ESP32 firmware lwIP task, Gazebo plugin thread, SITL runner)
 * owns the UDP sockets and pumps this module:
 *   - one call to fc_sdk_handle_line() per received datagram on :8889
 *   - fc_sdk_poll() every few ms -> emits deferred "ok"/"error" replies when
 *     motion commands (takeoff, go, cw, flip, ...) complete
 *   - fc_sdk_state_string() at 10 Hz -> datagram to <client>:8890
 *
 * Replies are routed through the platform callback; rc and emergency get no
 * reply (matches Tello, keeps djitellopy's response queue aligned).
 *
 * Extensions (all optional, never sent unless asked):
 *   EXT led <r> <g> <b>        RMTT-compatible LED control
 *   EXT version?               -> "stratos <version>"
 *   video 720 | video 1080     select H.264 stream height
 *   param <name> <value>       set a fc_core parameter (float)
 *   param <name>?              read a fc_core parameter
 *
 * SPDX-License-Identifier: MIT */
#ifndef FC_SDK_H
#define FC_SDK_H

#include "fc_core.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    /* required */
    void (*send_reply)(void *user, const char *msg);
    /* optional (NULL = feature reports ok but does nothing) */
    void (*video_ctrl)(void *user, bool on, int height /* 720|1080 */);
    void (*set_led)(void *user, uint8_t r, uint8_t g, uint8_t b);
    bool (*wifi_config)(void *user, const char *ssid, const char *pass, bool sta_mode);
    const char *(*get_sn)(void *user);
    int (*get_wifi_snr)(void *user);
} fc_sdk_platform_t;

typedef struct {
    fc_core_t *fc;
    const fc_sdk_platform_t *plat;
    void *user;
    bool sdk_mode;     /* entered after "command" */
    bool stream_on;
    int video_height;  /* 720 or 1080 */
    bool pending;      /* a motion command awaits completion */
    uint32_t pending_seq;
} fc_sdk_t;

void fc_sdk_init(fc_sdk_t *s, fc_core_t *fc, const fc_sdk_platform_t *plat, void *user);
void fc_sdk_handle_line(fc_sdk_t *s, const char *line);
void fc_sdk_poll(fc_sdk_t *s);
int fc_sdk_state_string(fc_sdk_t *s, char *buf, size_t n);

#define FC_SDK_VERSION_STR "stratos 0.1.0"

#ifdef __cplusplus
}
#endif
#endif /* FC_SDK_H */
