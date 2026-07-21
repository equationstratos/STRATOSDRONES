/* fc_show.h — time-synced choreography (drone-show) executor.
 *
 * A show is a list of time-stamped keyframes in the drone's local frame
 * (same frame as `go`: origin at arm, x forward at arm heading, cm):
 *
 *     {t_ms, x_cm, y_cm, z_cm, yaw_deg}      (yaw: clockwise-positive,
 *                                              Tello convention, like `cw`)
 *
 * Playback interpolates between keyframes with cosine easing and drives the
 * position setpoints + velocity feed-forward at the 100 Hz commander tick —
 * the exact plumbing `go` uses, so tracking behavior is identical.
 *
 * The fleet clock: every drone keeps `epoch = local + offset`; the ground
 * station broadcasts TIME_BEACON (over LoRa) or the `timesync` verb (UDP/sim)
 * to set the offset. `fc_show_start(t0)` arms playback at a common epoch T0
 * (t0 = 0 means "now"). Keyframe time τ = epoch − T0.
 *
 * Playback only advances while the drone is FLYING in SWARM mode; a live
 * radio stick deflection (>0.4) aborts to a hold, as does fc_show_stop()
 * (the LoRa SWARM_ABORT path). Fly the choreography in the Gazebo sim first.
 * SPDX-License-Identifier: MIT */
#ifndef FC_SHOW_H
#define FC_SHOW_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define FC_SHOW_MAX_KEYS 256

typedef struct {
    uint32_t t_ms;               /* since show T0, strictly increasing */
    int16_t x_cm, y_cm, z_cm;
    int16_t yaw_deg;             /* cw-positive (Tello convention) */
} fc_show_key_t;

typedef struct {
    fc_show_key_t keys[FC_SHOW_MAX_KEYS];
    int count;
    double local_ms;             /* free-running local clock (100 Hz ticks) */
    double clock_off_ms;         /* epoch = local + offset */
    bool   clock_synced;
    bool   armed;                /* waiting for epoch >= t0 */
    bool   playing;
    double t0_ms;                /* show start, epoch ms */
} fc_show_t;

struct fc_core_s;

void fc_show_clear(struct fc_core_s *fc);
bool fc_show_add_key(struct fc_core_s *fc, uint32_t t_ms,
                     float x_cm, float y_cm, float z_cm, float yaw_deg);
int  fc_show_count(const struct fc_core_s *fc);
void fc_show_time_sync(struct fc_core_s *fc, double epoch_ms);
double fc_show_epoch_ms(const struct fc_core_s *fc);
bool fc_show_start(struct fc_core_s *fc, double t0_epoch_ms); /* 0 = now */
void fc_show_stop(struct fc_core_s *fc);                      /* hold here */
bool fc_show_playing(const struct fc_core_s *fc);

/* fc_figures.c — on-board parametric figures. Each clears the show buffer
 * and writes a keyframe path starting from the drone's current position
 * (key 0 at t=0 = "here"), ready for `show start`. Returns false when the
 * parameters don't fit the buffer or the drone has no position estimate. */
bool fc_figure_circle(struct fc_core_s *fc, float r_cm, float period_ms, float turns);
bool fc_figure_spiral(struct fc_core_s *fc, float r_cm, float climb_cm, float period_ms, float turns);
bool fc_figure_line(struct fc_core_s *fc, float dx_cm, float dy_cm, float dz_cm, float dur_ms);
bool fc_figure_poly(struct fc_core_s *fc, int sides, float r_cm, float period_ms);
bool fc_figure_wave(struct fc_core_s *fc, float dx_cm, float dy_cm, float amp_cm, float cycles, float dur_ms);

#ifdef __cplusplus
}
#endif
#endif /* FC_SHOW_H */
