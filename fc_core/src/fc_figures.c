/* On-board figure generators: parametric paths compiled into the show
 * buffer, starting from the drone's current position. Used by the `figure`
 * SDK verb for single-drone practice; fleet shows are compiled on the
 * ground (stratospy.show) and uploaded as keyframes.
 * SPDX-License-Identifier: MIT */
#include "fc_core/fc_core.h"
#include "fc_internal.h"

#define SEG_PER_TURN 16

static bool here(fc_core_t *fc, float *x_cm, float *y_cm, float *z_cm, float *yaw_deg)
{
    *x_cm = fc->hest.px * 100.0f;
    *y_cm = fc->hest.py * 100.0f;
    *z_cm = fc->kfz.z * 100.0f;
    float r, p, y;
    fcq_to_euler(fc->ahrs.q, &r, &p, &y);
    *yaw_deg = -y * FC_RAD2DEG;      /* cw-positive keys */
    return true;
}

bool fc_figure_circle(fc_core_t *fc, float r_cm, float period_ms, float turns)
{
    return fc_figure_spiral(fc, r_cm, 0.0f, period_ms, turns);
}

/* circle with optional climb: starts at "here", circles around a center
 * r_cm to the drone's left, climbing climb_cm per turn */
bool fc_figure_spiral(fc_core_t *fc, float r_cm, float climb_cm,
                      float period_ms, float turns)
{
    if (r_cm < 20.0f || r_cm > 1000.0f) return false;
    if (period_ms < 2000.0f || turns <= 0.0f || turns > 8.0f) return false;
    int n = (int)(turns * SEG_PER_TURN);
    if (n < 2 || n + 1 > FC_SHOW_MAX_KEYS) return false;
    float x0, y0, z0, yaw0;
    here(fc, &x0, &y0, &z0, &yaw0);
    fc_show_clear(fc);
    float cy = cosf(fc->yaw_sp), sy = sinf(fc->yaw_sp);
    /* center r_cm to the left of the nose (body +y) */
    float cx = x0 - sy * r_cm, cyw = y0 + cy * r_cm;
    float a0 = atan2f(y0 - cyw, x0 - cx);
    for (int i = 0; i <= n; i++) {
        float f = (float)i / (float)SEG_PER_TURN;   /* turns done */
        float a = a0 + f * 2.0f * FC_PI;
        if (!fc_show_add_key(fc, (uint32_t)(f * period_ms),
                             cx + r_cm * cosf(a), cyw + r_cm * sinf(a),
                             z0 + climb_cm * f, yaw0))
            return false;
    }
    return true;
}

bool fc_figure_line(fc_core_t *fc, float dx_cm, float dy_cm, float dz_cm, float dur_ms)
{
    float d = sqrtf(dx_cm * dx_cm + dy_cm * dy_cm + dz_cm * dz_cm);
    if (d < 20.0f || d > 3000.0f || dur_ms < 1000.0f) return false;
    float x0, y0, z0, yaw0;
    here(fc, &x0, &y0, &z0, &yaw0);
    fc_show_clear(fc);
    /* dx/dy in the current heading frame, like `go` */
    float cy = cosf(fc->yaw_sp), sy = sinf(fc->yaw_sp);
    float wx = cy * dx_cm - sy * dy_cm, wy = sy * dx_cm + cy * dy_cm;
    return fc_show_add_key(fc, 0, x0, y0, z0, yaw0) &&
           fc_show_add_key(fc, (uint32_t)dur_ms, x0 + wx, y0 + wy, z0 + dz_cm, yaw0);
}

bool fc_figure_poly(fc_core_t *fc, int sides, float r_cm, float period_ms)
{
    if (sides < 3 || sides > 12) return false;
    if (r_cm < 30.0f || r_cm > 1000.0f || period_ms < 4000.0f) return false;
    if (sides + 1 > FC_SHOW_MAX_KEYS) return false;
    float x0, y0, z0, yaw0;
    here(fc, &x0, &y0, &z0, &yaw0);
    fc_show_clear(fc);
    float cy = cosf(fc->yaw_sp), sy = sinf(fc->yaw_sp);
    float cx = x0 - sy * r_cm, cyw = y0 + cy * r_cm;
    float a0 = atan2f(y0 - cyw, x0 - cx);
    for (int i = 0; i <= sides; i++) {
        float a = a0 + (float)i / (float)sides * 2.0f * FC_PI;
        if (!fc_show_add_key(fc, (uint32_t)((float)i / (float)sides * period_ms),
                             cx + r_cm * cosf(a), cyw + r_cm * sinf(a), z0, yaw0))
            return false;
    }
    return true;
}

/* straight run with a sinusoidal height ripple on top */
bool fc_figure_wave(fc_core_t *fc, float dx_cm, float dy_cm, float amp_cm,
                    float cycles, float dur_ms)
{
    float d = sqrtf(dx_cm * dx_cm + dy_cm * dy_cm);
    if (d < 50.0f || d > 3000.0f || dur_ms < 2000.0f) return false;
    if (amp_cm < 10.0f || amp_cm > 200.0f || cycles < 0.5f || cycles > 8.0f)
        return false;
    int n = (int)(cycles * 8.0f);
    if (n < 2 || n + 1 > FC_SHOW_MAX_KEYS) return false;
    float x0, y0, z0, yaw0;
    here(fc, &x0, &y0, &z0, &yaw0);
    fc_show_clear(fc);
    float cy = cosf(fc->yaw_sp), sy = sinf(fc->yaw_sp);
    float wx = cy * dx_cm - sy * dy_cm, wy = sy * dx_cm + cy * dy_cm;
    for (int i = 0; i <= n; i++) {
        float u = (float)i / (float)n;
        if (!fc_show_add_key(fc, (uint32_t)(u * dur_ms),
                             x0 + wx * u, y0 + wy * u,
                             z0 + amp_cm * sinf(u * cycles * 2.0f * FC_PI), yaw0))
            return false;
    }
    return true;
}
