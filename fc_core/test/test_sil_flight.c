/* Closed-loop SIL flight test: fc_core flying the 6-DOF plant through the
 * full Tello mission vocabulary — takeoff, hover hold, go, rotate, land.
 * This is also the gain-tuning bench: if this passes, the Gazebo model and
 * the real airframe start from a sane controller.
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

/* advance one 1 ms step with sensor feeds at firmware-realistic rates */
static void rig_step(rig_t *r)
{
    fc_imu_t imu;
    sil_get_imu(&r->pl, &imu);
    fc_core_imu_update(&r->fc, &imu, 0.001f);

    if (r->step % 10 == 3) { /* 100 Hz flow */
        fc_flow_t fl;
        sil_get_flow(&r->pl, r->fc.par.flow_cpr, 0.010f, &fl);
        fc_core_flow_update(&r->fc, &fl, 0.010f);
    }
    if (r->step % 20 == 7) { /* 50 Hz ToF */
        bool valid;
        float rng = sil_get_tof(&r->pl, &valid);
        fc_core_tof_update(&r->fc, rng, valid);
    }
    if (r->step % 20 == 13) /* 50 Hz baro */
        fc_core_baro_update(&r->fc, sil_get_baro_pa(&r->pl));
    if (r->step % 100 == 51) /* 10 Hz battery */
        fc_core_battery_update(&r->fc, 4.05f - 0.02f * (float)(r->pl.t / 60.0));

    float m[4];
    fc_core_get_motors(&r->fc, m);
    sil_step(&r->pl, m, 0.001f);
    r->step++;
    /* keep the SDK watchdog quiet (a client is "connected") */
    if (r->step % 500 == 0) fc_note_sdk_traffic(&r->fc);
}

static void run_s(rig_t *r, float seconds)
{
    long n = (long)(seconds * 1000.0f);
    for (long i = 0; i < n; i++) rig_step(r);
}

/* run until command seq completes (or timeout); returns status */
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
    rig_init(&r, 42);

    /* --- settle on ground: motors must stay off, estimator level --- */
    run_s(&r, 2.0f);
    float m[4];
    fc_core_get_motors(&r.fc, m);
    for (int i = 0; i < 4; i++) CHECK_NEAR(m[i], 0.0f, 1e-6);
    CHECK(fc_core_state(&r.fc) == FC_ST_IDLE);

    /* --- takeoff --- */
    uint32_t seq = fc_cmd_takeoff(&r.fc);
    CHECK(seq != 0);
    fc_cmd_status_t st = run_until_done(&r, seq, 8.0f);
    printf("takeoff: st=%d z=%.2f vz=%.2f\n", st, r.pl.pos.z, r.pl.vel.z);
    CHECK(st == FC_CMD_DONE);
    CHECK_NEAR(r.pl.pos.z, r.fc.par.takeoff_height_m, 0.25);
    CHECK(fc_core_state(&r.fc) == FC_ST_FLYING);

    /* --- hover hold 6 s: bounded height error and horizontal drift --- */
    fcv3_t p0 = r.pl.pos;
    float zmin = 99.0f, zmax = -99.0f, dmax = 0.0f;
    for (int i = 0; i < 6000; i++) {
        rig_step(&r);
        if (r.pl.pos.z < zmin) zmin = r.pl.pos.z;
        if (r.pl.pos.z > zmax) zmax = r.pl.pos.z;
        float dx = r.pl.pos.x - p0.x, dy = r.pl.pos.y - p0.y;
        float d = sqrtf(dx * dx + dy * dy);
        if (d > dmax) dmax = d;
    }
    printf("hover: z=[%.2f..%.2f] drift=%.2f m\n", zmin, zmax, dmax);
    CHECK(zmax - zmin < 0.25f);
    CHECK(dmax < 0.5f);

    /* --- go 100 cm forward at 50 cm/s --- */
    fcv3_t pgo = r.pl.pos;
    seq = fc_cmd_go(&r.fc, 100, 0, 0, 50);
    CHECK(seq != 0);
    st = run_until_done(&r, seq, 10.0f);
    printf("go: st=%d dx=%.2f dy=%.2f z=%.2f\n", st,
           r.pl.pos.x - pgo.x, r.pl.pos.y - pgo.y, r.pl.pos.z);
    CHECK(st == FC_CMD_DONE);
    CHECK_NEAR(r.pl.pos.x - pgo.x, 1.0f, 0.25);
    CHECK_NEAR(r.pl.pos.y - pgo.y, 0.0f, 0.25);

    /* --- rotate cw 90 deg --- */
    seq = fc_cmd_rotate(&r.fc, 90);
    CHECK(seq != 0);
    st = run_until_done(&r, seq, 8.0f);
    float rr, pp, yy;
    fcq_to_euler(r.pl.q, &rr, &pp, &yy);
    printf("cw90: st=%d yaw=%.1f deg\n", st, yy * FC_RAD2DEG);
    CHECK(st == FC_CMD_DONE);
    CHECK_NEAR(yy * FC_RAD2DEG, -90.0f, 10.0); /* cw = negative about z-up */

    /* --- rc sideways for 2 s then stop: must not lose height --- */
    fc_cmd_rc(&r.fc, 50, 0, 0, 0); /* right */
    run_s(&r, 2.0f);
    fc_cmd_rc(&r.fc, 0, 0, 0, 0);
    run_s(&r, 2.0f);
    printf("rc: z=%.2f\n", r.pl.pos.z);
    CHECK(r.pl.pos.z > 0.4f && r.pl.pos.z < 1.4f);

    /* --- land --- */
    seq = fc_cmd_land(&r.fc);
    CHECK(seq != 0);
    st = run_until_done(&r, seq, 10.0f);
    printf("land: st=%d z=%.3f state=%d\n", st, r.pl.pos.z, (int)fc_core_state(&r.fc));
    CHECK(st == FC_CMD_DONE);
    CHECK(r.pl.pos.z < 0.08f);
    CHECK(fc_core_state(&r.fc) == FC_ST_IDLE);
    fc_core_get_motors(&r.fc, m);
    for (int i = 0; i < 4; i++) CHECK_NEAR(m[i], 0.0f, 1e-6);

    /* --- telemetry sanity --- */
    fc_telemetry_t tel;
    fc_core_get_telemetry(&r.fc, &tel);
    CHECK(tel.bat_pct > 50 && tel.bat_pct <= 100);
    CHECK(tel.time_s > 10);

    TEST_END();
}
