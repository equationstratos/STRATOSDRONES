/* Default tuning + named parameter table.
 * Defaults are tuned against the closed-loop SIL tests in fc_core/test/
 * (92 g, 118 mm wheelbase, brushed 8520, ~60 ms motor lag).
 * SPDX-License-Identifier: MIT */
#include "fc_core/fc_core.h"
#include <string.h>

void fc_params_defaults(fc_params_t *p)
{
    memset(p, 0, sizeof(*p));
    /* estimator */
    p->ahrs_kp = 0.8f;
    p->ahrs_ki = 0.02f;
    p->gyro_lpf_hz = 120.0f;
    p->accel_lpf_hz = 30.0f;
    p->flow_cpr = 500.0f;        /* counts per radian; calibrate on hardware */
    p->flow_sign_x = 1.0f;
    p->flow_sign_y = 1.0f;
    p->flow_kv = 0.18f;
    p->flow_qual_min = 30.0f;
    /* rate loop */
    p->rate_rp_kp = 0.10f;
    p->rate_rp_ki = 0.12f;
    p->rate_rp_kd = 0.0028f;
    p->rate_yaw_kp = 0.18f;
    p->rate_yaw_ki = 0.10f;
    p->dterm_lpf_hz = 70.0f;
    /* attitude loop */
    p->att_kp = 7.0f;
    p->att_yaw_kp = 4.0f;
    /* velocity loop */
    p->vel_xy_kp = 2.4f;
    p->vel_xy_ki = 0.6f;
    p->vel_z_kp = 3.0f;
    p->vel_z_ki = 1.0f;
    /* position loop */
    p->pos_xy_kp = 1.5f;
    p->pos_z_kp = 1.8f;
    /* limits */
    p->tilt_max_deg = 25.0f;
    p->vmax_xy = 2.0f;
    p->vmax_up = 1.5f;
    p->vmax_down = 1.0f;
    p->yaw_rate_max_dps = 120.0f;
    p->rate_max_dps = 360.0f;
    /* behavior */
    p->speed_cms = 100.0f;
    p->takeoff_height_m = 0.8f;
    p->takeoff_vz = 0.7f;
    p->land_vz = 0.45f;
    p->hover_thr = 0.55f;
    p->rc_vmax_xy = 1.5f;
    p->rc_vmax_z = 1.0f;
    /* manual (angle/acro FPV) */
    p->angle_max_deg = 45.0f;
    p->acro_rate_dps = 720.0f;
    /* flips */
    p->flip_rate_dps = 800.0f;
    p->flip_min_bat_pct = 50.0f;
    p->flip_enable = 1.0f;
    /* battery: 1S LiHV under load */
    p->vbat_full = 4.20f;
    p->vbat_empty = 3.30f;
    p->bat_low_pct = 15.0f;
    p->bat_crit_pct = 7.0f;
    /* safety */
    p->cmd_timeout_s = 15.0f;
    p->tilt_kill_deg = 75.0f;
}

#define P(field) { #field, offsetof(fc_params_t, field) }
static const struct { const char *name; size_t off; } k_table[] = {
    P(ahrs_kp), P(ahrs_ki), P(gyro_lpf_hz), P(accel_lpf_hz),
    P(flow_cpr), P(flow_sign_x), P(flow_sign_y), P(flow_kv), P(flow_qual_min),
    P(rate_rp_kp), P(rate_rp_ki), P(rate_rp_kd), P(rate_yaw_kp), P(rate_yaw_ki),
    P(dterm_lpf_hz), P(att_kp), P(att_yaw_kp),
    P(vel_xy_kp), P(vel_xy_ki), P(vel_z_kp), P(vel_z_ki),
    P(pos_xy_kp), P(pos_z_kp),
    P(tilt_max_deg), P(vmax_xy), P(vmax_up), P(vmax_down),
    P(yaw_rate_max_dps), P(rate_max_dps),
    P(speed_cms), P(takeoff_height_m), P(takeoff_vz), P(land_vz), P(hover_thr),
    P(rc_vmax_xy), P(rc_vmax_z),
    P(angle_max_deg), P(acro_rate_dps),
    P(flip_rate_dps), P(flip_min_bat_pct), P(flip_enable),
    P(vbat_full), P(vbat_empty), P(bat_low_pct), P(bat_crit_pct),
    P(cmd_timeout_s), P(tilt_kill_deg),
};
#undef P

int fc_param_count(void) { return (int)(sizeof(k_table) / sizeof(k_table[0])); }

const char *fc_param_name(int idx)
{
    if (idx < 0 || idx >= fc_param_count()) return NULL;
    return k_table[idx].name;
}

static float *param_ptr(fc_params_t *p, const char *name)
{
    for (int i = 0; i < fc_param_count(); i++)
        if (strcmp(k_table[i].name, name) == 0)
            return (float *)((char *)p + k_table[i].off);
    return NULL;
}

bool fc_param_set(fc_core_t *fc, const char *name, float v)
{
    float *ptr = param_ptr(&fc->par, name);
    if (!ptr) return false;
    *ptr = v;
    return true;
}

bool fc_param_get(const fc_core_t *fc, const char *name, float *out)
{
    float *ptr = param_ptr((fc_params_t *)&fc->par, name);
    if (!ptr) return false;
    *out = *ptr;
    return true;
}
