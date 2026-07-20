/* Mode-manager tests: arbitration, arming, radio failsafe, MANUAL control
 * path, STABILIZED stick flying — closed-loop on the SIL plant.
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
    bool radio_on;
    float ch[16];
} rig_t;

static void rig_init(rig_t *r, uint32_t seed)
{
    memset(r, 0, sizeof(*r));
    fc_core_init(&r->fc);
    sil_init(&r->pl, seed);
    r->ch[2] = -1.0f;   /* throttle low */
    r->ch[4] = -1.0f;   /* disarmed */
    r->ch[5] = -1.0f;   /* CH6 low: defer to SDK */
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
    if (r->radio_on && r->step % 7 == 0)   /* ~143 Hz CRSF */
        fc_input_crsf(&r->fc, r->ch, 16);
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

int main(void)
{
    rig_t r;

    /* --- defaults: PROGRAM, legacy behavior intact --- */
    rig_init(&r, 7);
    CHECK(fc_mode_get(&r.fc) == FC_MODE_PROGRAM);
    CHECK(!strcmp(fc_mode_name(fc_mode_get(&r.fc)), "prog"));
    CHECK(!fc_mode_request(&r.fc, FC_MODE_MANUAL)); /* no radio -> refused */
    CHECK(fc_mode_request(&r.fc, FC_MODE_STABILIZED));
    CHECK(fc_mode_get(&r.fc) == FC_MODE_STABILIZED);
    CHECK(fc_mode_request(&r.fc, FC_MODE_PROGRAM));

    /* --- radio present, CH6 high -> MANUAL; arm; throttle response --- */
    r.radio_on = true;
    r.ch[5] = 1.0f;                    /* CH6 high: MANUAL */
    r.ch[6] = -1.0f;                   /* angle sub-mode */
    run_s(&r, 0.5f);
    CHECK(fc_mode_get(&r.fc) == FC_MODE_MANUAL);
    CHECK(fc_core_state(&r.fc) == FC_ST_IDLE);
    float m[4];
    fc_core_get_motors(&r.fc, m);
    for (int i = 0; i < 4; i++) CHECK_NEAR(m[i], 0.0f, 1e-6);

    r.ch[4] = 1.0f;                    /* arm, throttle low */
    run_s(&r, 0.2f);
    CHECK(fc_core_state(&r.fc) == FC_ST_FLYING);
    fc_core_get_motors(&r.fc, m);
    for (int i = 0; i < 4; i++) CHECK(m[i] > 0.0f && m[i] < 0.15f); /* idle spin */

    r.ch[2] = 0.3f;                    /* throttle ~65% */
    run_s(&r, 1.0f);
    fc_core_get_motors(&r.fc, m);
    float avg = (m[0] + m[1] + m[2] + m[3]) * 0.25f;
    printf("manual angle: avg motor %.2f alt %.2f\n", avg, r.pl.pos.z);
    CHECK(avg > 0.4f);
    CHECK(r.pl.pos.z > 0.2f);          /* it flies */

    /* angle sub-mode: right roll stick -> rolls right (positive roll) */
    r.ch[0] = 0.5f;
    run_s(&r, 0.4f);
    float rr, pp, yy;
    fcq_to_euler(r.pl.q, &rr, &pp, &yy);
    printf("manual angle: roll %.1f deg\n", rr * FC_RAD2DEG);
    CHECK(rr * FC_RAD2DEG > 8.0f);
    r.ch[0] = 0.0f;
    run_s(&r, 0.5f);

    /* acro sub-mode: rate setpoint follows the stick */
    r.ch[6] = 1.0f;
    run_s(&r, 0.1f);
    r.ch[0] = 0.5f;
    run_s(&r, 0.05f);
    CHECK_NEAR(r.fc.rate_sp.x, 0.5f * r.fc.par.acro_rate_dps * FC_DEG2RAD, 0.5);
    r.ch[0] = 0.0f;
    r.ch[6] = -1.0f;
    run_s(&r, 0.3f);

    /* --- disarm: CH5 low -> instant cut, back to IDLE --- */
    r.ch[4] = -1.0f;
    r.ch[2] = -1.0f;
    run_s(&r, 0.1f);
    CHECK(fc_core_state(&r.fc) == FC_ST_IDLE);
    fc_core_get_motors(&r.fc, m);
    for (int i = 0; i < 4; i++) CHECK_NEAR(m[i], 0.0f, 1e-6);

    /* --- failsafe: flying MANUAL, radio dies -> emergency cut --- */
    r.ch[4] = 1.0f;
    run_s(&r, 0.2f);
    CHECK(fc_core_state(&r.fc) == FC_ST_FLYING);
    r.radio_on = false;
    run_s(&r, 0.5f);
    CHECK(fc_core_state(&r.fc) == FC_ST_EMERGENCY);
    fc_core_get_motors(&r.fc, m);
    for (int i = 0; i < 4; i++) CHECK_NEAR(m[i], 0.0f, 1e-6);

    /* --- STABILIZED: CH6 mid, arm, throttle up = takeoff, sticks = velocity */
    rig_init(&r, 21);
    r.radio_on = true;
    r.ch[5] = 0.0f;                    /* CH6 mid: STABILIZED */
    run_s(&r, 0.3f);
    CHECK(fc_mode_get(&r.fc) == FC_MODE_STABILIZED);
    r.ch[4] = 1.0f;                    /* arm */
    run_s(&r, 0.2f);
    CHECK(fc_core_state(&r.fc) == FC_ST_IDLE);  /* armed but throttle low */
    r.ch[2] = 0.5f;                    /* push throttle: takeoff */
    run_s(&r, 0.3f);
    CHECK(fc_core_state(&r.fc) == FC_ST_TAKEOFF || fc_core_state(&r.fc) == FC_ST_FLYING);
    r.ch[2] = 0.0f;                    /* center = hold height */
    run_s(&r, 5.0f);
    CHECK(fc_core_state(&r.fc) == FC_ST_FLYING);
    printf("stab takeoff: z %.2f\n", r.pl.pos.z);
    CHECK(r.pl.pos.z > 0.5f && r.pl.pos.z < 1.2f);

    /* pitch stick forward: flies forward; release: brakes and holds */
    float x0 = r.pl.pos.x;
    r.ch[1] = 0.6f;
    run_s(&r, 2.0f);
    r.ch[1] = 0.0f;
    run_s(&r, 1.5f);
    printf("stab fwd: dx %.2f z %.2f\n", r.pl.pos.x - x0, r.pl.pos.z);
    CHECK(r.pl.pos.x - x0 > 0.6f);
    CHECK(r.pl.pos.z > 0.4f && r.pl.pos.z < 1.4f);

    /* --- pilot seizes a PROGRAM drone: CH6 high grabs MANUAL mid-flight --- */
    r.ch[5] = 1.0f;
    r.ch[2] = 0.1f;                    /* near-hover throttle ready */
    run_s(&r, 0.2f);
    CHECK(fc_mode_get(&r.fc) == FC_MODE_MANUAL);
    CHECK(fc_core_state(&r.fc) == FC_ST_FLYING);

    /* --- radio failsafe in STABILIZED lands instead of cutting --- */
    rig_init(&r, 33);
    r.radio_on = true;
    r.ch[5] = 0.0f;
    r.ch[4] = 1.0f;
    run_s(&r, 0.3f);
    r.ch[2] = 0.5f;
    run_s(&r, 0.5f);
    r.ch[2] = 0.0f;
    run_s(&r, 4.0f);
    CHECK(fc_core_state(&r.fc) == FC_ST_FLYING);
    r.radio_on = false;
    run_s(&r, 1.0f);
    CHECK(fc_core_state(&r.fc) == FC_ST_LANDING || fc_core_state(&r.fc) == FC_ST_IDLE);

    TEST_END();
}
