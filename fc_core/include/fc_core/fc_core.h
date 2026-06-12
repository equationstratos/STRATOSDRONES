/* fc_core.h — STRATOSDRONE platform-independent flight control core.
 *
 * Pure C99, no OS / heap / platform dependencies. The exact same library is
 * compiled into the ESP32-P4 firmware and into the Gazebo simulation plugin,
 * so the control behavior in simulation matches the real drone.
 *
 * Conventions:
 *   body frame  FLU: x forward, y left, z up
 *   world frame local ENU-like: z up, yaw 0 = initial heading, origin at arm
 *   units       SI (m, m/s, rad, rad/s, m/s^2, Pa, V), unless suffixed
 *   attitude    quaternion, body -> world
 *
 * Threading model: all calls must come from a single thread (the 1 kHz flight
 * loop). The SDK/network side communicates through fc_sdk.h which is pumped
 * from the same thread.
 * SPDX-License-Identifier: MIT */
#ifndef FC_CORE_H
#define FC_CORE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "fc_math.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ inputs */

typedef struct {
    float gyro[3];   /* rad/s, body FLU */
    float accel[3];  /* m/s^2 specific force, body FLU (level at rest: +g on z) */
} fc_imu_t;

typedef struct {
    int16_t dx;      /* raw accumulated flow counts since previous sample */
    int16_t dy;
    uint8_t quality; /* sensor surface quality (PMW3901 squal), 0..255 */
} fc_flow_t;

/* ------------------------------------------------------------------ states */

typedef enum {
    FC_ST_IDLE = 0,    /* on ground, motors off */
    FC_ST_TAKEOFF,
    FC_ST_FLYING,
    FC_ST_LANDING,
    FC_ST_FLIP,
    FC_ST_EMERGENCY,   /* motors cut until reset via fc_cmd_reset() */
} fc_state_t;

typedef enum {
    FC_CMD_NONE = 0,
    FC_CMD_RUNNING,
    FC_CMD_DONE,
    FC_CMD_ERROR,
} fc_cmd_status_t;

/* Telemetry in Tello-state-packet units (see docs/sdk_reference.md). */
typedef struct {
    int pitch_deg, roll_deg, yaw_deg;
    int vgx_cms, vgy_cms, vgz_cms;   /* world-frame velocity, cm/s, Tello axes (x fwd, y left, z up) */
    int templ_c, temph_c;
    int tof_cm;                      /* raw ToF range */
    int h_cm;                        /* fused height above ground */
    int bat_pct;
    float baro_m;                    /* barometric altitude, relative */
    int time_s;                      /* motor-on time */
    float agx_mg, agy_mg, agz_mg;    /* body accel in 0.001 g */
    fc_state_t state;
    float px_m, py_m, pz_m;          /* fused local position (extension) */
} fc_telemetry_t;

/* ------------------------------------------------------------- parameters */

typedef struct {
    /* estimator */
    float ahrs_kp, ahrs_ki;
    float gyro_lpf_hz, accel_lpf_hz;
    float flow_cpr;                 /* flow counts per radian of image motion */
    float flow_sign_x, flow_sign_y; /* +-1 board-mounting signs */
    float flow_kv;                  /* velocity correction gain per sample */
    float flow_qual_min;
    /* rate loop (rad/s err -> normalized torque) */
    float rate_rp_kp, rate_rp_ki, rate_rp_kd;
    float rate_yaw_kp, rate_yaw_ki;
    float dterm_lpf_hz;
    /* attitude loop (rad err -> rad/s) */
    float att_kp, att_yaw_kp;
    /* velocity loop (m/s err -> m/s^2) */
    float vel_xy_kp, vel_xy_ki;
    float vel_z_kp, vel_z_ki;
    /* position loop (m err -> m/s) */
    float pos_xy_kp, pos_z_kp;
    /* limits */
    float tilt_max_deg;
    float vmax_xy, vmax_up, vmax_down;  /* m/s */
    float yaw_rate_max_dps;
    float rate_max_dps;
    /* flight behavior */
    float speed_cms;                /* Tello "speed" setting, 10..100 cm/s */
    float takeoff_height_m, takeoff_vz, land_vz;
    float hover_thr;                /* nominal hover throttle 0..1 */
    float rc_vmax_xy, rc_vmax_z;    /* full-stick rc velocity, m/s */
    /* flips */
    float flip_rate_dps, flip_min_bat_pct, flip_enable;
    /* battery */
    float vbat_full, vbat_empty;
    float bat_low_pct, bat_crit_pct;
    /* safety */
    float cmd_timeout_s;            /* no SDK traffic -> auto land (Tello: 15 s) */
    float tilt_kill_deg;            /* crash detector */
} fc_params_t;

/* --------------------------------------------------------------- internals */

typedef struct {
    fcq_t q;
    fcv3_t err_int;
    bool init;
} fc_ahrs_t;

typedef struct {            /* vertical KF: x = [z, vz, accel_bias] */
    float z, vz, ab;
    float P[3][3];
    bool init;
} fc_kfz_t;

typedef struct {            /* horizontal velocity/position estimator */
    float vx, vy;           /* world frame, m/s */
    float px, py;           /* integrated local position, m */
    float unhealthy_s;      /* time since last accepted flow sample */
} fc_hest_t;

typedef struct {
    float kp, ki, kd;
    float i, i_limit;
    float out_limit;
    fc_lpf1_t dlpf;
    float prev_meas;
    bool has_prev;
} fc_pid_t;

typedef enum {
    FC_MCMD_NONE = 0,
    FC_MCMD_TAKEOFF,
    FC_MCMD_LAND,
    FC_MCMD_GOTO,       /* waypoint segment(s): go / move / curve */
    FC_MCMD_ROTATE,
    FC_MCMD_FLIP,
} fc_mcmd_t;

typedef struct {
    fc_mcmd_t active;
    fc_cmd_status_t status;
    uint32_t seq;               /* increments on each accepted motion command */
    /* waypoint executor (up to 2 chained segments for curve) */
    fcv3_t seg_start[2], seg_end[2];
    int seg_count, seg_idx;
    float seg_progress_m;
    float speed_ms;
    /* rotate */
    float yaw_target, yaw_dir;
    /* flip */
    int flip_axis;              /* 0=roll,1=pitch */
    float flip_dir;             /* +-1 */
    int flip_phase;
    float flip_t, flip_angle;
    /* rc */
    float rc[4];                /* lr, fb, ud, yaw in -1..1 */
    float rc_age_s;
    bool rc_active;
} fc_cmdr_t;

/* ------------------------------------------------------------------- core */

typedef struct fc_core_s {
    fc_params_t par;

    /* estimators */
    fc_ahrs_t ahrs;
    fc_kfz_t kfz;
    fc_hest_t hest;
    fc_lpf1_t gyro_f[3], accel_f[3];
    fcv3_t gyro, accel;             /* filtered body-frame samples */
    fcv3_t accel_w;                 /* world specific force minus gravity */

    /* sensor health */
    float tof_m, tof_age_s;
    bool tof_valid;
    float baro_alt_m, baro_off;     /* raw baro altitude and offset vs fused z */
    bool baro_ref_set;
    float baro_ref;
    float flow_dt_acc;
    float vbat, bat_pct;

    /* control */
    fc_pid_t pid_rate[3];           /* x=roll,y=pitch,z=yaw */
    fc_pid_t pid_vel[3];            /* world x,y,z */
    fcv3_t pos_sp;
    float yaw_sp;
    fcv3_t vel_sp, vel_ff;
    float yaw_rate_sp_ext;          /* from rc */
    fcq_t att_sp;                   /* derived each att tick */
    fcv3_t rate_sp;
    float torque[3], thrust;
    float motors[4];

    /* commander / state machine */
    fc_state_t state;
    fc_cmdr_t cmdr;
    float state_t;                  /* time in current state, s */
    float flight_time_s;
    float land_still_s;
    float sdk_traffic_age_s;
    bool low_bat_land;

    /* timing */
    uint32_t tick;                  /* imu ticks since init */
    float t;                        /* core time, s */
} fc_core_t;

/* ------------------------------------------------------------------- API */

void fc_core_init(fc_core_t *fc);
void fc_params_defaults(fc_params_t *p);

/* Sensor inputs. imu_update is the heartbeat (call at ~1 kHz); all control
 * loops are decimated from it. Others may be called at their natural rate. */
void fc_core_imu_update(fc_core_t *fc, const fc_imu_t *imu, float dt);
void fc_core_flow_update(fc_core_t *fc, const fc_flow_t *flow, float dt);
void fc_core_tof_update(fc_core_t *fc, float range_m, bool valid);
void fc_core_baro_update(fc_core_t *fc, float pressure_pa);
void fc_core_battery_update(fc_core_t *fc, float volts);

/* Outputs */
void fc_core_get_motors(const fc_core_t *fc, float m[4]); /* 0..1 duty */
void fc_core_get_telemetry(fc_core_t *fc, fc_telemetry_t *t);
static inline fc_state_t fc_core_state(const fc_core_t *fc) { return fc->state; }

/* Commands (called by the SDK layer; thread = flight loop).
 * Motion commands return the sequence number (>0) when accepted, 0 on error.
 * Completion is polled via fc_cmd_status(). */
uint32_t fc_cmd_takeoff(fc_core_t *fc);
uint32_t fc_cmd_land(fc_core_t *fc);
uint32_t fc_cmd_go(fc_core_t *fc, float x_cm, float y_cm, float z_cm, float speed_cms);
uint32_t fc_cmd_curve(fc_core_t *fc, float x1, float y1, float z1,
                      float x2, float y2, float z2, float speed_cms); /* cm */
uint32_t fc_cmd_rotate(fc_core_t *fc, float deg_cw);
uint32_t fc_cmd_flip(fc_core_t *fc, char dir); /* 'l','r','f','b' */
void fc_cmd_rc(fc_core_t *fc, float lr, float fb, float ud, float yw); /* -100..100 */
void fc_cmd_stop(fc_core_t *fc);
void fc_cmd_emergency(fc_core_t *fc);
void fc_cmd_reset(fc_core_t *fc);   /* leave EMERGENCY back to IDLE */
int  fc_set_speed(fc_core_t *fc, float cms);
void fc_note_sdk_traffic(fc_core_t *fc);
fc_cmd_status_t fc_cmd_status(const fc_core_t *fc, uint32_t seq);

/* Parameter table access (for "param" SDK extension and sim configs) */
int fc_param_count(void);
const char *fc_param_name(int idx);
bool fc_param_set(fc_core_t *fc, const char *name, float v);
bool fc_param_get(const fc_core_t *fc, const char *name, float *out);

#ifdef __cplusplus
}
#endif
#endif /* FC_CORE_H */
