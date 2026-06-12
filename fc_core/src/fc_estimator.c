/* State estimation: Mahony AHRS, 3-state vertical Kalman filter (ToF primary,
 * baro fallback), and the optical-flow horizontal velocity estimator that is
 * the heart of Tello-grade position hold.
 *
 * Algorithm references (clean-room, no code copied):
 *   Mahony, Hamel, Pflimlin — "Nonlinear Complementary Filters on SO(3)" (2008)
 *   Honegger et al. — PX4FLOW paper (ETHZ, 2013) for the flow/gyro/height model
 * SPDX-License-Identifier: MIT */
#include "fc_core/fc_core.h"
#include "fc_internal.h"

/* ------------------------------------------------------------------ AHRS */

static void ahrs_init_from_accel(fc_ahrs_t *a, fcv3_t acc)
{
    float roll = atan2f(acc.y, acc.z);
    float pitch = atan2f(-acc.x, sqrtf(acc.y * acc.y + acc.z * acc.z));
    a->q = fcq_from_euler(roll, pitch, 0.0f);
    a->err_int = fcv3(0, 0, 0);
    a->init = true;
}

static void ahrs_update(fc_core_t *fc, fcv3_t gyro, fcv3_t acc, float dt)
{
    fc_ahrs_t *a = &fc->ahrs;
    if (!a->init) {
        ahrs_init_from_accel(a, acc);
        return;
    }
    float an = fcv3_norm(acc);
    fcv3_t gcorr = gyro;
    if (an > 0.5f * FC_G && an < 1.5f * FC_G) {
        fcv3_t am = fcv3_scale(acc, 1.0f / an);
        /* estimated gravity direction in body frame = R^T * ez */
        fcq_t q = a->q;
        fcv3_t vg = fcv3(2.0f * (q.x * q.z - q.w * q.y),
                         2.0f * (q.y * q.z + q.w * q.x),
                         q.w * q.w - q.x * q.x - q.y * q.y + q.z * q.z);
        fcv3_t e = fcv3_cross(am, vg);
        a->err_int = fcv3_add(a->err_int, fcv3_scale(e, fc->par.ahrs_ki * dt));
        float ilim = 0.05f;
        a->err_int.x = fc_clampf(a->err_int.x, -ilim, ilim);
        a->err_int.y = fc_clampf(a->err_int.y, -ilim, ilim);
        a->err_int.z = fc_clampf(a->err_int.z, -ilim, ilim);
        gcorr = fcv3_add(gcorr, fcv3_add(fcv3_scale(e, fc->par.ahrs_kp), a->err_int));
    }
    a->q = fcq_integrate(a->q, gcorr, dt);
}

/* ------------------------------------------------------- vertical Kalman */

static void kfz_predict(fc_kfz_t *k, float az, float dt)
{
    if (!k->init) {
        k->z = 0.0f; k->vz = 0.0f; k->ab = 0.0f;
        for (int i = 0; i < 3; i++)
            for (int j = 0; j < 3; j++)
                k->P[i][j] = (i == j) ? 0.5f : 0.0f;
        k->init = true;
    }
    float a = az - k->ab;
    k->z += k->vz * dt + 0.5f * a * dt * dt;
    k->vz += a * dt;

    /* P = F P F' + Q,  F = [[1,dt,-dt^2/2],[0,1,-dt],[0,0,1]] */
    float F[3][3] = {{1, dt, -0.5f * dt * dt}, {0, 1, -dt}, {0, 0, 1}};
    float FP[3][3], P2[3][3];
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            FP[i][j] = F[i][0] * k->P[0][j] + F[i][1] * k->P[1][j] + F[i][2] * k->P[2][j];
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            P2[i][j] = FP[i][0] * F[j][0] + FP[i][1] * F[j][1] + FP[i][2] * F[j][2];
    const float sa = 0.4f;          /* accel noise m/s^2 */
    const float sab = 0.01f;        /* bias random walk */
    P2[0][0] += 0.25f * dt * dt * dt * dt * sa * sa;
    P2[1][1] += dt * dt * sa * sa;
    P2[2][2] += dt * sab * sab;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            k->P[i][j] = P2[i][j];
}

/* Scalar update with H = [1,0,0] (both ToF-derived z and baro z). */
static void kfz_correct_z(fc_kfz_t *k, float z_meas, float r)
{
    float y = z_meas - k->z;
    float s = k->P[0][0] + r;
    if (s < 1e-9f) return;
    float K[3] = {k->P[0][0] / s, k->P[1][0] / s, k->P[2][0] / s};
    k->z += K[0] * y;
    k->vz += K[1] * y;
    k->ab += K[2] * y;
    k->ab = fc_clampf(k->ab, -1.5f, 1.5f);
    float P[3][3];
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            P[i][j] = k->P[i][j] - K[i] * k->P[0][j];
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            k->P[i][j] = P[i][j];
}

/* --------------------------------------------------------- public inputs */

void fc_est_imu(fc_core_t *fc, const fc_imu_t *imu, float dt)
{
    for (int i = 0; i < 3; i++) {
        ((float *)&fc->gyro)[i] = fc_lpf1_step(&fc->gyro_f[i], imu->gyro[i]);
        ((float *)&fc->accel)[i] = fc_lpf1_step(&fc->accel_f[i], imu->accel[i]);
    }
    ahrs_update(fc, fc->gyro, fc->accel, dt);

    /* world-frame specific force minus gravity = inertial acceleration */
    fcv3_t aw = fcq_rotate(fc->ahrs.q, fc->accel);
    aw.z -= FC_G;
    fc->accel_w = aw;

    kfz_predict(&fc->kfz, aw.z, dt);

    /* horizontal velocity dead-reckoning between flow corrections */
    fc->hest.vx += aw.x * dt;
    fc->hest.vy += aw.y * dt;
    fc->hest.px += fc->hest.vx * dt;
    fc->hest.py += fc->hest.vy * dt;
    fc->hest.unhealthy_s += dt;

    fc->tof_age_s += dt;
    if (fc->tof_age_s > 0.25f) fc->tof_valid = false;
    fc->flow_dt_acc += dt;
}

void fc_core_tof_update(fc_core_t *fc, float range_m, bool valid)
{
    fc->tof_age_s = 0.0f;
    float tc = fcq_tilt_cos(fc->ahrs.q);
    if (!valid || range_m < 0.015f || range_m > 4.0f || tc < 0.77f) {
        fc->tof_valid = false;
        return;
    }
    fc->tof_valid = true;
    fc->tof_m = range_m;
    float z = range_m * tc;
    float r = 0.012f + 0.004f * range_m;       /* std grows with range */
    kfz_correct_z(&fc->kfz, z, r * r);
    /* keep the baro offset servoed to the ToF-based solution */
    if (fc->baro_ref_set)
        fc->baro_off += 0.5f * 0.02f * ((fc->baro_alt_m - fc->kfz.z) - fc->baro_off);
}

void fc_core_baro_update(fc_core_t *fc, float pressure_pa)
{
    /* ISA conversion, relative altitude vs first sample */
    float alt = 44330.0f * (1.0f - powf(pressure_pa / 101325.0f, 0.1902949f));
    if (!fc->baro_ref_set) {
        fc->baro_ref = alt;
        fc->baro_ref_set = true;
    }
    fc->baro_alt_m = alt - fc->baro_ref;
    /* only trust baro when ToF can't see the ground */
    if (!fc->tof_valid && fc->state != FC_ST_IDLE) {
        const float r = 0.6f;
        kfz_correct_z(&fc->kfz, fc->baro_alt_m - fc->baro_off, r * r);
    }
}

void fc_core_flow_update(fc_core_t *fc, const fc_flow_t *flow, float dt)
{
    float dtf = (dt > 1e-4f) ? dt : fc->flow_dt_acc;
    fc->flow_dt_acc = 0.0f;
    if (dtf < 1e-4f) return;

    float h = fc->kfz.z;
    if (flow->quality < (uint8_t)fc->par.flow_qual_min) return;
    if (h < 0.08f || !fc->tof_valid) return;
    float tc = fcq_tilt_cos(fc->ahrs.q);
    if (tc < 0.77f) return;

    /* image angular rates (rad/s) */
    float fx = fc->par.flow_sign_x * (float)flow->dx / (fc->par.flow_cpr * dtf);
    float fy = fc->par.flow_sign_y * (float)flow->dy / (fc->par.flow_cpr * dtf);
    if (fabsf(fx) > 5.0f || fabsf(fy) > 5.0f) return; /* tracking surely lost */

    /* translation = (flow - rotation) * height; see fc_internal.h note */
    float vx_b = (fc->gyro.y - fx) * h;
    float vy_b = (-fc->gyro.x - fy) * h;

    /* body -> world (full attitude) */
    fcv3_t vw = fcq_rotate(fc->ahrs.q, fcv3(vx_b, vy_b, 0.0f));

    float k = fc_clampf(fc->par.flow_kv, 0.0f, 1.0f);
    fc->hest.vx += k * (vw.x - fc->hest.vx);
    fc->hest.vy += k * (vw.y - fc->hest.vy);
    fc->hest.unhealthy_s = 0.0f;
}

void fc_core_battery_update(fc_core_t *fc, float volts)
{
    if (fc->vbat <= 0.1f) fc->vbat = volts;
    fc->vbat += 0.05f * (volts - fc->vbat);
    float pct = 100.0f * (fc->vbat - fc->par.vbat_empty) /
                (fc->par.vbat_full - fc->par.vbat_empty);
    fc->bat_pct = fc_clampf(pct, 0.0f, 100.0f);
}
