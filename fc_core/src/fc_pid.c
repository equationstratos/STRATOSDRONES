/* Generic PID with derivative-on-measurement, D low-pass, integrator clamp
 * and conditional anti-windup.
 * SPDX-License-Identifier: MIT */
#include "fc_core/fc_core.h"
#include "fc_internal.h"

void fc_pid_setup(fc_pid_t *pid, float kp, float ki, float kd,
                  float i_limit, float out_limit, float dlpf_hz, float rate_hz)
{
    pid->kp = kp;
    pid->ki = ki;
    pid->kd = kd;
    pid->i = 0.0f;
    pid->i_limit = i_limit;
    pid->out_limit = out_limit;
    fc_lpf1_setup(&pid->dlpf, dlpf_hz, rate_hz);
    pid->prev_meas = 0.0f;
    pid->has_prev = false;
}

void fc_pid_reset(fc_pid_t *pid)
{
    pid->i = 0.0f;
    pid->has_prev = false;
    pid->dlpf.init = false;
}

float fc_pid_step(fc_pid_t *pid, float sp, float meas, float dt)
{
    float err = sp - meas;
    float d = 0.0f;
    if (pid->kd != 0.0f) {
        if (pid->has_prev && dt > 1e-6f)
            d = -fc_lpf1_step(&pid->dlpf, (meas - pid->prev_meas) / dt);
        else
            fc_lpf1_step(&pid->dlpf, 0.0f);
    }
    pid->prev_meas = meas;
    pid->has_prev = true;

    float out_pd = pid->kp * err + pid->kd * d;
    float out = out_pd + pid->i;

    /* conditional integration: don't wind further into saturation */
    bool sat_hi = out > pid->out_limit;
    bool sat_lo = out < -pid->out_limit;
    if ((!sat_hi || err < 0.0f) && (!sat_lo || err > 0.0f)) {
        pid->i += pid->ki * err * dt;
        pid->i = fc_clampf(pid->i, -pid->i_limit, pid->i_limit);
    }
    out = out_pd + pid->i;
    return fc_clampf(out, -pid->out_limit, pid->out_limit);
}
