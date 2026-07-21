/* Show-executor tests: keyframe playback tracks the figure in closed loop
 * on the SIL plant; clock sync; on-board figure generators.
 * SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <string.h>
#include "fc_core/fc_core.h"
#include "test_util.h"
#include "sil_plant.h"

typedef struct {
    fc_core_t fc;
    sil_plant_t pl;
    long step;
} rig_t;

static void rig_init(rig_t *r, uint32_t seed)
{
    fc_core_init(&r->fc);
    sil_init(&r->pl, seed);
    r->step = 0;
}

static void rig_step(rig_t *r)
{
    fc_imu_t imu;
    sil_get_imu(&r->pl, &imu);
    fc_core_imu_update(&r->fc, &imu, 0.001f);
    if (r->step % 10 == 3) {
        fc_flow_t fl;
        sil_get_flow(&r->pl, r->fc.par.flow_cpr, 0.010f, &fl);
        fc_core_flow_update(&r->fc, &fl, 0.010f);
    }
    if (r->step % 20 == 7) {
        bool valid;
        float rng = sil_get_tof(&r->pl, &valid);
        fc_core_tof_update(&r->fc, rng, valid);
    }
    if (r->step % 20 == 13)
        fc_core_baro_update(&r->fc, sil_get_baro_pa(&r->pl));
    if (r->step % 100 == 51)
        fc_core_battery_update(&r->fc, 4.05f);
    float m[4];
    fc_core_get_motors(&r->fc, m);
    sil_step(&r->pl, m, 0.001f);
    r->step++;
    if (r->step % 500 == 0) fc_note_sdk_traffic(&r->fc);
}

static void run_s(rig_t *r, float seconds)
{
    long n = (long)(seconds * 1000.0f);
    for (long i = 0; i < n; i++) rig_step(r);
}

static fc_cmd_status_t run_until_done(rig_t *r, uint32_t seq, float timeout_s)
{
    long n = (long)(timeout_s * 1000.0f);
    for (long i = 0; i < n; i++) {
        rig_step(r);
        fc_cmd_status_t st = fc_cmd_status(&r->fc, seq);
        if (st == FC_CMD_DONE || st == FC_CMD_ERROR) return st;
    }
    return FC_CMD_RUNNING;
}

int main(void)
{
    rig_t r;
    rig_init(&r, 11);

    /* --- keyframe API guards --- */
    CHECK(fc_show_count(&r.fc) == 0);
    CHECK(!fc_show_start(&r.fc, 0));               /* empty: refuse */
    CHECK(fc_show_add_key(&r.fc, 0, 0, 0, 80, 0));
    CHECK(!fc_show_add_key(&r.fc, 0, 10, 0, 80, 0)); /* not increasing */
    CHECK(fc_show_add_key(&r.fc, 3000, 100, 0, 80, 0));
    CHECK(fc_show_count(&r.fc) == 2);
    fc_show_clear(&r.fc);
    CHECK(fc_show_count(&r.fc) == 0);

    /* --- clock sync: epoch = local + offset --- */
    run_s(&r, 1.0f);
    fc_show_time_sync(&r.fc, 5000000.0);
    run_s(&r, 0.5f);
    CHECK_NEAR(fc_show_epoch_ms(&r.fc), 5000500.0, 30.0);

    /* --- fly an L-shaped 3-key show --- */
    uint32_t seq = fc_cmd_takeoff(&r.fc);
    CHECK(run_until_done(&r, seq, 8.0f) == FC_CMD_DONE);
    CHECK(fc_mode_request(&r.fc, FC_MODE_SWARM));
    CHECK(fc_mode_get(&r.fc) == FC_MODE_SWARM);

    CHECK(fc_show_add_key(&r.fc, 0, 0, 0, 80, 0));
    CHECK(fc_show_add_key(&r.fc, 3000, 100, 0, 80, 0));
    CHECK(fc_show_add_key(&r.fc, 6000, 100, 100, 120, 0));
    CHECK(fc_show_start(&r.fc, 0));                /* t0 = now */
    CHECK(fc_show_playing(&r.fc));

    /* Tracking is judged on the *estimated* position (what the controller
     * can know); flow drift vs ground truth is the estimator's accepted
     * M0 limitation, so the plant check is looser. */
    run_s(&r, 3.0f);                               /* at key 1 */
    printf("show mid: est (%.2f %.2f) plant (%.2f %.2f %.2f)\n",
           r.fc.hest.px, r.fc.hest.py, r.pl.pos.x, r.pl.pos.y, r.pl.pos.z);
    CHECK_NEAR(r.fc.hest.px, 1.0f, 0.25);
    CHECK_NEAR(r.fc.hest.py, 0.0f, 0.25);
    CHECK_NEAR(r.pl.pos.x, 1.0f, 0.6);

    run_s(&r, 3.5f);                               /* past the end */
    printf("show end: est (%.2f %.2f %.2f) plant (%.2f %.2f %.2f) playing=%d\n",
           r.fc.hest.px, r.fc.hest.py, r.fc.kfz.z,
           r.pl.pos.x, r.pl.pos.y, r.pl.pos.z, (int)fc_show_playing(&r.fc));
    CHECK_NEAR(r.fc.hest.px, 1.0f, 0.25);
    CHECK_NEAR(r.fc.hest.py, 1.0f, 0.25);
    CHECK_NEAR(r.fc.kfz.z, 1.2f, 0.25);
    CHECK_NEAR(r.pl.pos.y, 1.0f, 0.8);
    CHECK_NEAR(r.pl.pos.z, 1.2f, 0.30);
    CHECK(!fc_show_playing(&r.fc));                /* done -> holds last key */

    /* --- deferred start on the shared clock --- */
    double t0 = fc_show_epoch_ms(&r.fc) + 1500.0;
    fc_show_clear(&r.fc);
    CHECK(fc_show_add_key(&r.fc, 0, 100, 100, 120, 0));
    CHECK(fc_show_add_key(&r.fc, 2000, 0, 100, 120, 0));
    CHECK(fc_show_start(&r.fc, t0));
    run_s(&r, 1.0f);
    CHECK(fc_show_playing(&r.fc));                 /* armed, not moving yet */
    CHECK_NEAR(r.fc.hest.px, 1.0f, 0.25);          /* still parked */
    run_s(&r, 3.5f);
    printf("deferred: est (%.2f %.2f) plant (%.2f %.2f)\n",
           r.fc.hest.px, r.fc.hest.py, r.pl.pos.x, r.pl.pos.y);
    CHECK_NEAR(r.fc.hest.px, 0.0f, 0.25);
    CHECK_NEAR(r.fc.hest.py, 1.0f, 0.25);
    CHECK_NEAR(r.pl.pos.x, 0.0f, 0.6);

    /* --- show stop parks the drone --- */
    fc_show_clear(&r.fc);
    CHECK(fc_show_add_key(&r.fc, 0, 0, 100, 120, 0));
    CHECK(fc_show_add_key(&r.fc, 4000, 300, 100, 120, 0));
    CHECK(fc_show_start(&r.fc, 0));
    run_s(&r, 1.0f);
    fc_show_stop(&r.fc);
    float xs = r.pl.pos.x;
    run_s(&r, 1.5f);
    printf("stop: x %.2f (was %.2f)\n", r.pl.pos.x, xs);
    CHECK(fabsf(r.pl.pos.x - xs) < 0.3f);          /* parked, not continuing */

    /* --- figure generators fill sane keyframes from "here" --- */
    CHECK(fc_figure_circle(&r.fc, 100.0f, 8000.0f, 1.0f));
    CHECK(fc_show_count(&r.fc) == 17);             /* 16 seg/turn + closing */
    /* key 0 is (approximately) the current position */
    CHECK_NEAR(r.fc.show.keys[0].x_cm * 0.01f, r.fc.hest.px, 0.15);
    CHECK_NEAR(r.fc.show.keys[0].y_cm * 0.01f, r.fc.hest.py, 0.15);
    CHECK(!fc_figure_circle(&r.fc, 5.0f, 8000.0f, 1.0f));   /* r too small */
    CHECK(!fc_figure_poly(&r.fc, 2, 100.0f, 8000.0f));      /* sides < 3 */
    CHECK(fc_figure_wave(&r.fc, 200.0f, 0.0f, 50.0f, 2.0f, 8000.0f));
    CHECK(fc_show_count(&r.fc) == 17);             /* 2 cycles x 8 + 1 */

    /* fly the circle for real */
    CHECK(fc_figure_circle(&r.fc, 80.0f, 8000.0f, 1.0f));
    fcv3_t pstart = r.pl.pos;
    CHECK(fc_show_start(&r.fc, 0));
    run_s(&r, 4.0f);                               /* half turn: far side */
    float dx = r.pl.pos.x - pstart.x, dy = r.pl.pos.y - pstart.y;
    float d_half = sqrtf(dx * dx + dy * dy);
    printf("circle half: %.2f m from start\n", d_half);
    CHECK_NEAR(d_half, 1.6f, 0.5);                 /* diameter away */
    run_s(&r, 4.5f);
    dx = r.pl.pos.x - pstart.x;
    dy = r.pl.pos.y - pstart.y;
    printf("circle done: %.2f m from start\n", sqrtf(dx * dx + dy * dy));
    CHECK(sqrtf(dx * dx + dy * dy) < 0.5f);        /* back home */

    TEST_END();
}
