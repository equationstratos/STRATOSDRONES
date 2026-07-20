/* Internal interfaces between fc_core compilation units.
 *
 * Optical-flow sign convention (PMW3901 mounted looking down, sensor x axis
 * aligned with body x): pixel motion is opposite to translation and follows
 * body rotation, so
 *     flow_rate_x = gyro_y - vx_body / h
 *     flow_rate_y = -gyro_x - vy_body / h
 * The simulator generates counts with this exact model; on real hardware the
 * two flow_sign_* params absorb the mounting orientation.
 * SPDX-License-Identifier: MIT */
#ifndef FC_INTERNAL_H
#define FC_INTERNAL_H

#include "fc_core/fc_core.h"

/* fc_estimator.c */
void fc_est_imu(fc_core_t *fc, const fc_imu_t *imu, float dt);

/* fc_pid.c */
void fc_pid_setup(fc_pid_t *pid, float kp, float ki, float kd,
                  float i_limit, float out_limit, float dlpf_hz, float rate_hz);
float fc_pid_step(fc_pid_t *pid, float sp, float meas, float dt);
void fc_pid_reset(fc_pid_t *pid);

/* fc_control.c */
void fc_ctl_init(fc_core_t *fc);
void fc_ctl_step(fc_core_t *fc, float dt);   /* called every imu tick */
void fc_ctl_reset(fc_core_t *fc);
void fc_mixer_run(fc_core_t *fc);

/* fc_commander.c */
void fc_cmdr_step(fc_core_t *fc, float dt);  /* 100 Hz: setpoints + state machine */
void fc_cmdr_force_state(fc_core_t *fc, fc_state_t st); /* MANUAL direct arm */

/* fc_mode.c */
void fc_mode_step(fc_core_t *fc, float dt);  /* 100 Hz, before the state machine */

/* fc_show.c */
void fc_show_step(fc_core_t *fc, float dt);  /* 100 Hz, SWARM playback */

#endif
