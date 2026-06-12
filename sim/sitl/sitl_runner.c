/* sitl_runner — software-in-the-loop STRATOSDRONE without Gazebo.
 *
 * Runs fc_core + the 6-DOF SIL plant in real time and exposes the Tello SDK
 * UDP surface, so djitellopy (or any Tello client) can fly a virtual drone:
 *
 *   ./sitl_runner --ip 127.0.0.2          # one drone
 *   ./sitl_runner --ip 127.0.0.3 &        # swarm: one process per loopback IP
 *
 * Ports (Tello-identical): commands in on <ip>:8889 (replies from the same
 * socket), state pushed to <client>:8890 at 10 Hz. Video is not simulated
 * here (use the Gazebo model for camera work) — streamon still replies ok.
 *
 * --rtf <x>  real-time factor (default 1.0; 0 = as fast as possible)
 * --seed <n> plant noise seed
 * SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include "fc_core/fc_core.h"
#include "fc_core/fc_sdk.h"
#include "../../fc_core/test/sil_plant.h"

typedef struct {
    int cmd_sock;
    struct sockaddr_in client;
    bool have_client;
    char sn[32];
} net_t;

static volatile sig_atomic_t g_stop;
static void on_sig(int s) { (void)s; g_stop = 1; }

static void cb_reply(void *u, const char *msg)
{
    net_t *n = (net_t *)u;
    if (!n->have_client) return;
    sendto(n->cmd_sock, msg, strlen(msg), 0,
           (struct sockaddr *)&n->client, sizeof(n->client));
}
static const char *cb_sn(void *u) { return ((net_t *)u)->sn; }
static int cb_snr(void *u) { (void)u; return 90; }
static void cb_video(void *u, bool on, int h)
{
    (void)u;
    fprintf(stderr, "[sitl] video %s (%dp) — not rendered in SITL, use Gazebo\n",
            on ? "on" : "off", h);
}
static void cb_led(void *u, uint8_t r, uint8_t g, uint8_t b)
{
    (void)u;
    fprintf(stderr, "[sitl] led %u %u %u\n", r, g, b);
}

static const fc_sdk_platform_t k_plat = {
    .send_reply = cb_reply,
    .video_ctrl = cb_video,
    .set_led = cb_led,
    .get_sn = cb_sn,
    .get_wifi_snr = cb_snr,
};

int main(int argc, char **argv)
{
    const char *ip = "127.0.0.2";
    float rtf = 1.0f;
    uint32_t seed = 42;
    for (int i = 1; i < argc - 1; i++) {
        if (!strcmp(argv[i], "--ip")) ip = argv[++i];
        else if (!strcmp(argv[i], "--rtf")) rtf = strtof(argv[++i], NULL);
        else if (!strcmp(argv[i], "--seed")) seed = (uint32_t)strtoul(argv[++i], NULL, 10);
    }
    signal(SIGINT, on_sig);
    signal(SIGTERM, on_sig);

    net_t net = {0};
    snprintf(net.sn, sizeof(net.sn), "STRATOSSITL%s", strrchr(ip, '.') + 1);
    net.cmd_sock = socket(AF_INET, SOCK_DGRAM, 0);
    int one = 1;
    setsockopt(net.cmd_sock, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(8889);
    if (inet_pton(AF_INET, ip, &addr.sin_addr) != 1) {
        fprintf(stderr, "bad ip %s\n", ip);
        return 1;
    }
    if (bind(net.cmd_sock, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        fprintf(stderr, "bind %s:8889: %s\n", ip, strerror(errno));
        return 1;
    }

    fc_core_t *fc = calloc(1, sizeof(fc_core_t));
    sil_plant_t *pl = calloc(1, sizeof(sil_plant_t));
    fc_sdk_t sdk;
    fc_core_init(fc);
    sil_init(pl, seed);
    fc_sdk_init(&sdk, fc, &k_plat, &net);

    fprintf(stderr, "[sitl] STRATOSDRONE SITL on %s (rtf=%.1f). "
                    "djitellopy: Tello(host='%s')\n", ip, (double)rtf, ip);

    struct timespec next;
    clock_gettime(CLOCK_MONOTONIC, &next);
    long step = 0;
    const long ns_per_step = rtf > 0.0f ? (long)(1e6 / rtf) : 0;

    while (!g_stop) {
        /* --- network in (non-blocking) --- */
        char buf[256];
        struct sockaddr_in src;
        socklen_t slen = sizeof(src);
        ssize_t r;
        while ((r = recvfrom(net.cmd_sock, buf, sizeof(buf) - 1, MSG_DONTWAIT,
                             (struct sockaddr *)&src, &slen)) > 0) {
            buf[r] = '\0';
            net.client = src; /* replies go back to the client's source port */
            net.have_client = true;
            fc_sdk_handle_line(&sdk, buf);
            slen = sizeof(src);
        }

        /* --- 1 kHz physics + control --- */
        fc_imu_t imu;
        sil_get_imu(pl, &imu);
        fc_core_imu_update(fc, &imu, 0.001f);
        if (step % 10 == 3) {
            fc_flow_t fl;
            sil_get_flow(pl, fc->par.flow_cpr, 0.010f, &fl);
            fc_core_flow_update(fc, &fl, 0.010f);
        }
        if (step % 20 == 7) {
            bool valid;
            float rng = sil_get_tof(pl, &valid);
            fc_core_tof_update(fc, rng, valid);
        }
        if (step % 20 == 13)
            fc_core_baro_update(fc, sil_get_baro_pa(pl));
        if (step % 100 == 51)
            fc_core_battery_update(fc, 4.15f - 0.0004f * (float)(pl->t / 60.0));
        float m[4];
        fc_core_get_motors(fc, m);
        sil_step(pl, m, 0.001f);

        if (step % 5 == 0) fc_sdk_poll(&sdk);

        /* --- state packet at 10 Hz to <client>:8890 --- */
        if (step % 100 == 0 && net.have_client) {
            char st[256];
            int len = fc_sdk_state_string(&sdk, st, sizeof(st));
            struct sockaddr_in dst = net.client;
            dst.sin_port = htons(8890);
            sendto(net.cmd_sock, st, (size_t)len, 0,
                   (struct sockaddr *)&dst, sizeof(dst));
        }

        /* --- pacing --- */
        if (ns_per_step > 0) {
            next.tv_nsec += ns_per_step;
            while (next.tv_nsec >= 1000000000L) {
                next.tv_nsec -= 1000000000L;
                next.tv_sec++;
            }
            clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL);
        }
        step++;
    }
    close(net.cmd_sock);
    free(fc);
    free(pl);
    return 0;
}
