/* sil_plant.c — see sil_plant.h. SPDX-License-Identifier: MIT */
#include <string.h>
#include "sil_plant.h"

static uint32_t xorshift(uint32_t *s)
{
    uint32_t x = *s;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    return *s = x;
}

static float frand(sil_plant_t *p) /* uniform 0..1 */
{
    return (float)(xorshift(&p->rng) >> 8) / 16777216.0f;
}

float sil_randn(sil_plant_t *p) /* sum of 12 uniforms - 6: ~N(0,1) */
{
    float s = 0.0f;
    for (int i = 0; i < 12; i++) s += frand(p);
    return s - 6.0f;
}

void sil_init(sil_plant_t *p, uint32_t seed)
{
    memset(p, 0, sizeof(*p));
    p->mass = 0.092f;
    p->Ixx = p->Iyy = 1.1e-4f;
    p->Izz = 2.0e-4f;
    p->arm = 0.0417f;          /* 118 mm wheelbase: x = y = 118/2/sqrt(2) */
    p->kT = 0.42f;             /* ~43 gf max per 8520 + 3" prop at 4.2 V */
    p->cQ = 0.006f;
    p->tau_motor = 0.06f;
    p->drag = 0.06f;
    p->seed = seed ? seed : 1u;
    p->rng = p->seed;
    p->q = fcq_ident();
    p->gyro_bias = fcv3(0.01f * sil_randn(p), 0.01f * sil_randn(p), 0.01f * sil_randn(p));
}

/* Motor layout must match fc_mixer_run():
 *   M1 FR (+x,-y) CCW   M2 BR (-x,-y) CW   M3 BL (-x,+y) CCW   M4 FL (+x,+y) CW */
static const float k_mx[4] = {+1.0f, -1.0f, -1.0f, +1.0f}; /* x position sign */
static const float k_my[4] = {-1.0f, -1.0f, +1.0f, +1.0f}; /* y position sign */
static const float k_cw[4] = {-1.0f, +1.0f, -1.0f, +1.0f}; /* body yaw reaction sign */

void sil_step(sil_plant_t *p, const float motors[4], float dt)
{
    /* motor lag + forces */
    float F[4], Ftot = 0.0f;
    fcv3_t tau = fcv3(0, 0, 0);
    for (int i = 0; i < 4; i++) {
        float m = fc_clampf(motors[i], 0.0f, 1.0f);
        p->thr_lag[i] += (m - p->thr_lag[i]) * dt / p->tau_motor;
        F[i] = p->kT * p->thr_lag[i];
        Ftot += F[i];
        tau.x += k_my[i] * p->arm * F[i];
        tau.y += -k_mx[i] * p->arm * F[i];
        tau.z += k_cw[i] * p->cQ * F[i];
    }

    /* rotational dynamics (body frame) */
    fcv3_t Iw = fcv3(p->Ixx * p->omega.x, p->Iyy * p->omega.y, p->Izz * p->omega.z);
    fcv3_t gyr = fcv3_cross(Iw, p->omega); /* -w x Iw, sign folded below */
    fcv3_t wdot = fcv3((tau.x + gyr.x) / p->Ixx,
                       (tau.y + gyr.y) / p->Iyy,
                       (tau.z + gyr.z) / p->Izz);
    /* small aero rotational damping */
    wdot = fcv3_sub(wdot, fcv3_scale(p->omega, 0.4f));
    p->omega = fcv3_add(p->omega, fcv3_scale(wdot, dt));
    p->q = fcq_integrate(p->q, p->omega, dt);

    /* translational dynamics (world frame) */
    fcv3_t thrust_w = fcq_rotate(p->q, fcv3(0, 0, Ftot));
    fcv3_t acc = fcv3_scale(thrust_w, 1.0f / p->mass);
    acc.z -= FC_G;
    acc = fcv3_sub(acc, fcv3_scale(p->vel, p->drag / p->mass));
    p->vel = fcv3_add(p->vel, fcv3_scale(acc, dt));
    p->pos = fcv3_add(p->pos, fcv3_scale(p->vel, dt));

    /* ground contact: simple inelastic floor with high friction */
    if (p->pos.z <= 0.0f) {
        p->pos.z = 0.0f;
        if (p->vel.z < 0.0f) p->vel.z = 0.0f;
        float f = 1.0f - fc_clampf(25.0f * dt, 0.0f, 1.0f);
        p->vel.x *= f;
        p->vel.y *= f;
        p->omega = fcv3_scale(p->omega, f);
        if (Ftot < 0.3f * p->mass * FC_G) { /* settle upright when nearly unpowered */
            float r, pi, y;
            fcq_to_euler(p->q, &r, &pi, &y);
            p->q = fcq_from_euler(r * f, pi * f, y);
        }
    }
    p->t += dt;
}

void sil_get_imu(sil_plant_t *p, fc_imu_t *imu)
{
    /* specific force f = a - g, in body frame; at rest reads +g on body z */
    fcv3_t thrust_w = fcq_rotate(p->q, fcv3(0, 0, 1.0f)); /* direction only */
    (void)thrust_w;
    /* reconstruct from last dynamics: f_world = a_world + g_z_up. We recompute
     * thrust-based accel instead of storing it: f = R^T * (acc_nongrav). For
     * simplicity, use thrust/mass minus drag (the only non-gravity forces). */
    float Ftot = p->kT * (p->thr_lag[0] + p->thr_lag[1] + p->thr_lag[2] + p->thr_lag[3]);
    fcv3_t f_body = fcv3(0, 0, Ftot / p->mass);
    fcv3_t drag_w = fcv3_scale(p->vel, -p->drag / p->mass);
    fcv3_t f = fcv3_add(f_body, fcq_rotate_inv(p->q, drag_w));
    if (p->pos.z <= 0.001f) {
        /* ground normal force: at rest the accelerometer reads +g */
        fcv3_t up_b = fcq_rotate_inv(p->q, fcv3(0, 0, FC_G));
        if (f.z < up_b.z) f = up_b;
    }
    imu->accel[0] = f.x + 0.25f * sil_randn(p);
    imu->accel[1] = f.y + 0.25f * sil_randn(p);
    imu->accel[2] = f.z + 0.25f * sil_randn(p);
    imu->gyro[0] = p->omega.x + p->gyro_bias.x + 0.015f * sil_randn(p);
    imu->gyro[1] = p->omega.y + p->gyro_bias.y + 0.015f * sil_randn(p);
    imu->gyro[2] = p->omega.z + p->gyro_bias.z + 0.015f * sil_randn(p);
}

/* Flow model — must be the exact inverse of fc_estimator.c's decode:
 *   flow_rate_x = gyro_y - vx_body / h
 *   flow_rate_y = -gyro_x - vy_body / h   */
void sil_get_flow(sil_plant_t *p, float flow_cpr, float dt, fc_flow_t *out)
{
    float h = p->pos.z > 0.03f ? p->pos.z : 0.03f;
    fcv3_t v_body = fcq_rotate_inv(p->q, p->vel);
    float fx = p->omega.y - v_body.x / h;
    float fy = -p->omega.x - v_body.y / h;
    float nx = 1.2f * sil_randn(p), ny = 1.2f * sil_randn(p);
    out->dx = (int16_t)fc_clampf(fx * flow_cpr * dt + nx, -32000.0f, 32000.0f);
    out->dy = (int16_t)fc_clampf(fy * flow_cpr * dt + ny, -32000.0f, 32000.0f);
    float tc = fcq_tilt_cos(p->q);
    out->quality = (uint8_t)(p->pos.z > 0.06f && p->pos.z < 3.5f && tc > 0.75f ? 120 : 25);
}

float sil_get_tof(sil_plant_t *p, bool *valid)
{
    float tc = fcq_tilt_cos(p->q);
    if (tc < 0.5f || p->pos.z > 3.9f) {
        *valid = false;
        return 8.19f;
    }
    *valid = true;
    float r = p->pos.z / tc + 0.008f * sil_randn(p);
    return r < 0.0f ? 0.0f : r;
}

float sil_get_baro_pa(sil_plant_t *p)
{
    float alt = 35.0f + p->pos.z + 0.35f * sil_randn(p);
    float x = 1.0f - 2.25577e-5f * alt;
    return 101325.0f * powf(x, 5.25588f);
}
