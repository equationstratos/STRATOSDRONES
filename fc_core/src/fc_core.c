/* fc_core.c — top-level glue: init, the 1 kHz heartbeat, telemetry.
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "fc_core/fc_core.h"
#include "fc_internal.h"

void fc_core_init(fc_core_t *fc)
{
    memset(fc, 0, sizeof(*fc));
    fc_params_defaults(&fc->par);

    fc->ahrs.q = fcq_ident();
    for (int i = 0; i < 3; i++) {
        fc_lpf1_setup(&fc->gyro_f[i], fc->par.gyro_lpf_hz, 1000.0f);
        fc_lpf1_setup(&fc->accel_f[i], fc->par.accel_lpf_hz, 1000.0f);
    }
    fc->kfz.P[0][0] = 0.01f;
    fc->kfz.P[1][1] = 0.01f;
    fc->kfz.P[2][2] = 0.01f;

    fc_ctl_init(fc);

    fc->state = FC_ST_IDLE;
    fc->vbat = fc->par.vbat_full;
    fc->bat_pct = 100.0f;
    fc->tof_age_s = 10.0f;
    fc->hest.unhealthy_s = 10.0f;
    fc->cmdr.status = FC_CMD_NONE;
}

void fc_core_imu_update(fc_core_t *fc, const fc_imu_t *imu, float dt)
{
    if (dt <= 0.0f || dt > 0.05f) dt = 0.001f;
    fc->t += dt;
    fc->state_t += dt;
    fc->tof_age_s += dt;
    fc->sdk_traffic_age_s += dt;
    fc->cmdr.rc_age_s += dt;
    if (fc->state != FC_ST_IDLE && fc->state != FC_ST_EMERGENCY)
        fc->flight_time_s += dt;

    /* estimation */
    fc_est_imu(fc, imu, dt);

    /* commander + state machine at 100 Hz */
    if (fc->tick % 10 == 0)
        fc_cmdr_step(fc, dt * 10.0f);

    /* control cascade + mixer every tick */
    fc_ctl_step(fc, dt);

    fc->tick++;
}

void fc_core_get_motors(const fc_core_t *fc, float m[4])
{
    for (int i = 0; i < 4; i++) m[i] = fc->motors[i];
}

void fc_core_get_telemetry(fc_core_t *fc, fc_telemetry_t *t)
{
    float roll, pitch, yaw;
    fcq_to_euler(fc->ahrs.q, &roll, &pitch, &yaw);
    /* Tello reports yaw positive clockwise; internal yaw is positive CCW (z up) */
    t->roll_deg = (int)(roll * FC_RAD2DEG);
    t->pitch_deg = (int)(pitch * FC_RAD2DEG);
    t->yaw_deg = (int)(-yaw * FC_RAD2DEG);

    /* velocities in Tello axes (x fwd, y left, z up), cm/s, world frame */
    t->vgx_cms = (int)(fc->hest.vx * 100.0f);
    t->vgy_cms = (int)(fc->hest.vy * 100.0f);
    t->vgz_cms = (int)(fc->kfz.vz * 100.0f);

    t->templ_c = 48;
    t->temph_c = 52;
    t->tof_cm = fc->tof_valid ? (int)(fc->tof_m * 100.0f) : 0;
    t->h_cm = (int)(fc->kfz.z * 100.0f);
    t->bat_pct = (int)fc->bat_pct;
    t->baro_m = fc->baro_alt_m; /* already relative to the first sample */
    t->time_s = (int)fc->flight_time_s;

    /* body accel in 0.001 g, Tello z reports ~-1000 at rest (z down sign) */
    t->agx_mg = fc->accel.x / FC_G * 1000.0f;
    t->agy_mg = -fc->accel.y / FC_G * 1000.0f;
    t->agz_mg = -fc->accel.z / FC_G * 1000.0f;

    t->state = fc->state;
    t->px_m = fc->hest.px;
    t->py_m = fc->hest.py;
    t->pz_m = fc->kfz.z;
}
