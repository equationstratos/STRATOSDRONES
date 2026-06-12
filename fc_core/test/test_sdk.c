/* Protocol-level test: drive the SIL plant exclusively through Tello SDK
 * text commands and verify replies and the state packet format.
 * SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <string.h>
#include "fc_core/fc_sdk.h"
#include "test_util.h"
#include "sil_plant.h"

typedef struct {
    char last_reply[128];
    int replies;
    bool video_on;
    int video_h;
    uint8_t led[3];
} cap_t;

static void cb_reply(void *u, const char *m)
{
    cap_t *c = (cap_t *)u;
    snprintf(c->last_reply, sizeof(c->last_reply), "%s", m);
    c->replies++;
}
static void cb_video(void *u, bool on, int h)
{
    cap_t *c = (cap_t *)u;
    c->video_on = on;
    c->video_h = h;
}
static void cb_led(void *u, uint8_t r, uint8_t g, uint8_t b)
{
    cap_t *c = (cap_t *)u;
    c->led[0] = r; c->led[1] = g; c->led[2] = b;
}

static const fc_sdk_platform_t k_plat = {
    .send_reply = cb_reply,
    .video_ctrl = cb_video,
    .set_led = cb_led,
};

static fc_core_t fc;
static sil_plant_t pl;
static fc_sdk_t sdk;
static cap_t cap;
static long g_step;

static void run_ms(long ms)
{
    for (long i = 0; i < ms; i++) {
        fc_imu_t imu;
        sil_get_imu(&pl, &imu);
        fc_core_imu_update(&fc, &imu, 0.001f);
        if (g_step % 10 == 3) {
            fc_flow_t fl;
            sil_get_flow(&pl, fc.par.flow_cpr, 0.010f, &fl);
            fc_core_flow_update(&fc, &fl, 0.010f);
        }
        if (g_step % 20 == 7) {
            bool v;
            float r = sil_get_tof(&pl, &v);
            fc_core_tof_update(&fc, r, v);
        }
        if (g_step % 20 == 13)
            fc_core_baro_update(&fc, sil_get_baro_pa(&pl));
        if (g_step % 100 == 0)
            fc_core_battery_update(&fc, 4.2f); /* full battery -> 100% */
        float m[4];
        fc_core_get_motors(&fc, m);
        sil_step(&pl, m, 0.001f);
        if (g_step % 5 == 0) fc_sdk_poll(&sdk);
        g_step++;
    }
}

/* send a command and wait (sim-time) for its reply */
static const char *cmd(const char *line, long timeout_ms)
{
    int before = cap.replies;
    fc_sdk_handle_line(&sdk, line);
    long waited = 0;
    while (cap.replies == before && waited < timeout_ms) {
        run_ms(10);
        waited += 10;
    }
    return cap.replies == before ? "(timeout)" : cap.last_reply;
}

int main(void)
{
    fc_core_init(&fc);
    sil_init(&pl, 99);
    fc_sdk_init(&sdk, &fc, &k_plat, &cap);
    run_ms(1500); /* sensor settle */

    /* commands before "command" are ignored */
    int r0 = cap.replies;
    fc_sdk_handle_line(&sdk, "takeoff");
    CHECK(cap.replies == r0);

    CHECK(!strcmp(cmd("command", 100), "ok"));
    CHECK(!strcmp(cmd("battery?", 100), "100"));
    CHECK(!strcmp(cmd("sdk?", 100), "20"));
    CHECK(!strcmp(cmd("speed 30", 100), "ok"));
    CHECK(!strcmp(cmd("speed?", 100), "30.0"));
    CHECK(!strcmp(cmd("speed 999", 100), "error"));
    CHECK(!strcmp(cmd("streamon", 100), "ok"));
    CHECK(cap.video_on && cap.video_h == 720);
    CHECK(!strcmp(cmd("video 1080", 100), "ok"));
    CHECK(cap.video_h == 1080);
    CHECK(!strcmp(cmd("EXT led 0 128 255", 100), "led ok"));
    CHECK(cap.led[2] == 255);
    CHECK(!strcmp(cmd("mon", 100), "ok"));

    /* go before takeoff must fail */
    CHECK(!strcmp(cmd("go 50 0 0 50", 500), "error"));

    CHECK(!strcmp(cmd("takeoff", 10000), "ok"));
    CHECK(pl.pos.z > 0.5f);

    /* motion while busy -> immediate error for the second command */
    fc_sdk_handle_line(&sdk, "forward 100");
    CHECK(!strcmp(cmd("back 50", 200), "error"));
    /* the first one still completes with ok */
    long waited = 0;
    int before = cap.replies;
    while (cap.replies == before && waited < 15000) { run_ms(10); waited += 10; }
    CHECK(!strcmp(cap.last_reply, "ok"));
    CHECK_NEAR(pl.pos.x, 1.0f, 0.3);

    CHECK(!strcmp(cmd("cw 90", 10000), "ok"));

    /* state packet format */
    char st[256];
    int len = fc_sdk_state_string(&sdk, st, sizeof(st));
    CHECK(len > 60 && len < 200);
    printf("state: %s", st);
    CHECK(strstr(st, "pitch:") == st);
    CHECK(strstr(st, ";baro:") != NULL);
    CHECK(strstr(st, ";bat:") != NULL);
    CHECK(st[len - 2] == '\r' && st[len - 1] == '\n');
    int pitch, bat;
    CHECK(sscanf(st, "pitch:%d;", &pitch) == 1);
    char *b = strstr(st, ";bat:");
    CHECK(sscanf(b, ";bat:%d;", &bat) == 1 && bat >= 95);

    CHECK(!strcmp(cmd("land", 10000), "ok"));
    CHECK(fc_core_state(&fc) == FC_ST_IDLE);

    /* rc and emergency produce no replies */
    int r1 = cap.replies;
    fc_sdk_handle_line(&sdk, "rc 0 0 0 0");
    fc_sdk_handle_line(&sdk, "emergency");
    CHECK(cap.replies == r1);
    CHECK(fc_core_state(&fc) == FC_ST_EMERGENCY);

    TEST_END();
}
