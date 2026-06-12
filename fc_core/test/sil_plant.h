/* sil_plant.h — minimal 6-DOF quadrotor plant for closed-loop (SIL) testing
 * of fc_core on the host, with synthetic noisy sensors. The Gazebo plugin is
 * the high-fidelity twin; this keeps CI fast and dependency-free.
 *
 * Physical model matches the STRATOSDRONE airframe estimates:
 * 92 g AUW, 118 mm wheelbase, brushed 8520 + 3" props (first-order lag).
 * SPDX-License-Identifier: MIT */
#ifndef SIL_PLANT_H
#define SIL_PLANT_H

#include "fc_core/fc_core.h"

typedef struct {
    /* config */
    float mass;          /* kg */
    float Ixx, Iyy, Izz; /* kg m^2 */
    float arm;           /* motor x/y offset from CG, m */
    float kT;            /* max thrust per motor, N (thrust = kT * duty_lagged) */
    float cQ;            /* yaw torque per newton of thrust, m */
    float tau_motor;     /* motor first-order time constant, s */
    float drag;          /* linear drag coefficient, N/(m/s) */
    uint32_t seed;

    /* state */
    fcv3_t pos, vel;     /* world */
    fcq_t q;             /* body -> world */
    fcv3_t omega;        /* body rates */
    float thr_lag[4];    /* lagged motor duty */
    fcv3_t gyro_bias;
    double t;
    uint32_t rng;
} sil_plant_t;

void sil_init(sil_plant_t *p, uint32_t seed);
void sil_step(sil_plant_t *p, const float motors[4], float dt);

/* Synthetic sensors (call at the firmware's natural rates) */
void sil_get_imu(sil_plant_t *p, fc_imu_t *imu);
void sil_get_flow(sil_plant_t *p, float flow_cpr, float dt, fc_flow_t *out);
float sil_get_tof(sil_plant_t *p, bool *valid);
float sil_get_baro_pa(sil_plant_t *p);

float sil_randn(sil_plant_t *p); /* unit gaussian */

#endif
