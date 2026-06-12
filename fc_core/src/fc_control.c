/* Cascaded position -> velocity -> attitude -> rate control and X-mixer.
 *
 * Loop rates (decimated from the 1 kHz IMU tick):
 *   rate PID   1 kHz     attitude P  500 Hz
 *   velocity   100 Hz    position P  25 Hz
 *
 * Motor layout (body FLU, props down-facing):
 *   M1 front-right CCW   M2 back-right CW   M3 back-left CCW   M4 front-left CW
 * SPDX-License-Identifier: MIT */
#include "fc_core/fc_core.h"
#include "fc_internal.h"

void fc_ctl_init(fc_core_t *fc)
{
    const fc_params_t *p = &fc->par;
    fc_pid_setup(&fc->pid_rate[0], p->rate_rp_kp, p->rate_rp_ki, p->rate_rp_kd,
                 0.35f, 1.0f, p->dterm_lpf_hz, 1000.0f);
    fc_pid_setup(&fc->pid_rate[1], p->rate_rp_kp, p->rate_rp_ki, p->rate_rp_kd,
                 0.35f, 1.0f, p->dterm_lpf_hz, 1000.0f);
    fc_pid_setup(&fc->pid_rate[2], p->rate_yaw_kp, p->rate_yaw_ki, 0.0f,
                 0.25f, 0.4f, p->dterm_lpf_hz, 1000.0f);
    fc_pid_setup(&fc->pid_vel[0], p->vel_xy_kp, p->vel_xy_ki, 0.0f, 2.0f, 6.0f, 0, 100.0f);
    fc_pid_setup(&fc->pid_vel[1], p->vel_xy_kp, p->vel_xy_ki, 0.0f, 2.0f, 6.0f, 0, 100.0f);
    fc_pid_setup(&fc->pid_vel[2], p->vel_z_kp, p->vel_z_ki, 0.0f, 3.0f, 8.0f, 0, 100.0f);
}

void fc_ctl_reset(fc_core_t *fc)
{
    for (int i = 0; i < 3; i++) {
        fc_pid_reset(&fc->pid_rate[i]);
        fc_pid_reset(&fc->pid_vel[i]);
    }
    float r, pch, y;
    fcq_to_euler(fc->ahrs.q, &r, &pch, &y);
    fc->pos_sp = fcv3(fc->hest.px, fc->hest.py, fc->kfz.z);
    fc->yaw_sp = y;
    fc->vel_ff = fcv3(0, 0, 0);
    fc->yaw_rate_sp_ext = 0.0f;
}

static void position_loop(fc_core_t *fc)
{
    const fc_params_t *p = &fc->par;
    fcv3_t pos = fcv3(fc->hest.px, fc->hest.py, fc->kfz.z);
    fcv3_t err = fcv3_sub(fc->pos_sp, pos);
    /* reduce horizontal authority while flow is unhealthy to avoid runaway */
    float trust = fc->hest.unhealthy_s > 0.5f ? 0.3f : 1.0f;
    fc->vel_sp.x = fc_clampf(p->pos_xy_kp * err.x * trust + fc->vel_ff.x, -p->vmax_xy, p->vmax_xy);
    fc->vel_sp.y = fc_clampf(p->pos_xy_kp * err.y * trust + fc->vel_ff.y, -p->vmax_xy, p->vmax_xy);
    fc->vel_sp.z = fc_clampf(p->pos_z_kp * err.z + fc->vel_ff.z, -p->vmax_down, p->vmax_up);
}

static void velocity_loop(fc_core_t *fc, float dt)
{
    const fc_params_t *p = &fc->par;
    float ax = fc_pid_step(&fc->pid_vel[0], fc->vel_sp.x, fc->hest.vx, dt);
    float ay = fc_pid_step(&fc->pid_vel[1], fc->vel_sp.y, fc->hest.vy, dt);
    float az = fc_pid_step(&fc->pid_vel[2], fc->vel_sp.z, fc->kfz.vz, dt);

    /* horizontal accel -> attitude setpoint, in yaw frame */
    float cy = cosf(fc->yaw_sp), sy = sinf(fc->yaw_sp);
    float axf = cy * ax + sy * ay;
    float ayf = -sy * ax + cy * ay;
    float tilt_max = p->tilt_max_deg * FC_DEG2RAD;
    float pitch_sp = fc_clampf(atanf(axf / FC_G), -tilt_max, tilt_max);
    float roll_sp = fc_clampf(atanf(-ayf / FC_G), -tilt_max, tilt_max);
    fc->att_sp = fcq_from_euler(roll_sp, pitch_sp, fc->yaw_sp);

    /* vertical accel -> collective thrust, with tilt compensation */
    float tc = fc_clampf(fcq_tilt_cos(fc->ahrs.q), 0.5f, 1.0f);
    float thr = p->hover_thr * (1.0f + az / FC_G) / tc;
    /* battery sag compensation around nominal 3.9 V under load */
    if (fc->vbat > 2.5f)
        thr *= fc_clampf(3.9f / fc->vbat, 0.85f, 1.25f);
    fc->thrust = fc_clampf(thr, 0.08f, 0.95f);
}

static void attitude_loop(fc_core_t *fc)
{
    const fc_params_t *p = &fc->par;
    /* body-frame attitude error quaternion: q_e = q^-1 * q_sp */
    fcq_t qi = {fc->ahrs.q.w, -fc->ahrs.q.x, -fc->ahrs.q.y, -fc->ahrs.q.z};
    fcq_t qe = fcq_mul(qi, fc->att_sp);
    float s = qe.w >= 0.0f ? 2.0f : -2.0f;
    float rate_max = p->rate_max_dps * FC_DEG2RAD;
    float yaw_max = p->yaw_rate_max_dps * FC_DEG2RAD;
    fc->rate_sp.x = fc_clampf(s * p->att_kp * qe.x, -rate_max, rate_max);
    fc->rate_sp.y = fc_clampf(s * p->att_kp * qe.y, -rate_max, rate_max);
    fc->rate_sp.z = fc_clampf(s * p->att_yaw_kp * qe.z + fc->yaw_rate_sp_ext,
                              -yaw_max, yaw_max);
}

static void rate_loop(fc_core_t *fc, float dt)
{
    fc->torque[0] = fc_pid_step(&fc->pid_rate[0], fc->rate_sp.x, fc->gyro.x, dt);
    fc->torque[1] = fc_pid_step(&fc->pid_rate[1], fc->rate_sp.y, fc->gyro.y, dt);
    fc->torque[2] = fc_pid_step(&fc->pid_rate[2], fc->rate_sp.z, fc->gyro.z, dt);
}

void fc_mixer_run(fc_core_t *fc)
{
    if (fc->state == FC_ST_IDLE || fc->state == FC_ST_EMERGENCY) {
        for (int i = 0; i < 4; i++) fc->motors[i] = 0.0f;
        return;
    }
    float T = fc->thrust;
    float tx = fc->torque[0], ty = fc->torque[1];
    float tz = fc_clampf(fc->torque[2], -0.25f, 0.25f);
    /*            sx (roll)  sy (pitch)  sz (yaw reaction)  */
    float m[4] = {
        T - tx - ty - tz,   /* M1 front-right, CCW */
        T - tx + ty + tz,   /* M2 back-right,  CW  */
        T + tx + ty - tz,   /* M3 back-left,   CCW */
        T + tx - ty + tz,   /* M4 front-left,  CW  */
    };
    float mx = m[0], mn = m[0];
    for (int i = 1; i < 4; i++) {
        if (m[i] > mx) mx = m[i];
        if (m[i] < mn) mn = m[i];
    }
    float shift = 0.0f;
    if (mn < 0.0f) shift = -mn;
    if (mx + shift > 1.0f) shift = 1.0f - mx; /* upper bound wins (keeps control authority) */
    for (int i = 0; i < 4; i++)
        fc->motors[i] = fc_clampf(m[i] + shift, 0.04f, 1.0f);
}

void fc_ctl_step(fc_core_t *fc, float dt)
{
    bool flying = (fc->state == FC_ST_FLYING || fc->state == FC_ST_TAKEOFF ||
                   fc->state == FC_ST_LANDING);
    if (flying) {
        if (fc->tick % 40 == 0) position_loop(fc);
        if (fc->tick % 10 == 0) velocity_loop(fc, dt * 10.0f);
        if (fc->tick % 2 == 0) attitude_loop(fc);
        rate_loop(fc, dt);
    } else if (fc->state == FC_ST_FLIP) {
        /* commander drives rate_sp / thrust directly during the flip */
        if (fc->tick % 10 == 0) { /* keep vertical PID warm for recovery */ }
        rate_loop(fc, dt);
    }
    fc_mixer_run(fc);
}
