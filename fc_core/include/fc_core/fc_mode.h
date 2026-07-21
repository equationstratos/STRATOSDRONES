/* fc_mode.h — flight-mode manager + command-source arbitration (TinyHoop MK1).
 *
 * Four modes on one core:
 *   PROGRAM     (default) the Tello-SDK verb path — exactly the behavior every
 *               model had before modes existed. SDK scripts own the drone.
 *   MANUAL      true FPV: CRSF sticks -> angle or acro inner loops, throttle
 *               direct, position/velocity loops bypassed.
 *   STABILIZED  position hold; sticks (or SDK `rc`) become velocity commands
 *               with brake-to-hover. The drone-show "parked" mode.
 *   SWARM       fc_show choreography playback drives the position setpoints.
 *
 * Arbitration (evaluated at the 100 Hz commander tick):
 *   1. CRSF failsafe — radio was live and vanished ≥300 ms: MANUAL -> motor
 *      cut (emergency); radio-owned STABILIZED -> auto-land. Non-negotiable.
 *   2. CH5 (AUX1) low while the radio is live -> disarm, always.
 *   3. CH6 (AUX2, 3-pos) while the radio is live:
 *        high  -> MANUAL          (safety pilot seizes the drone)
 *        mid   -> STABILIZED      (assisted stick flying)
 *        low   -> defer to the SDK-requested mode (PROGRAM/STABILIZED/SWARM)
 *      CH7 (AUX3) selects the MANUAL sub-mode: low = angle, high = acro.
 *   4. No radio ever seen -> SDK request only; default PROGRAM.
 *
 * Channel order is AETR + AUX: ch[0] roll(+right) ch[1] pitch(+nose-down/fwd)
 * ch[2] throttle ch[3] yaw(+right/cw) ch[4..] AUX1.., all normalized -1..+1.
 * SPDX-License-Identifier: MIT */
#ifndef FC_MODE_H
#define FC_MODE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    FC_MODE_PROGRAM = 0,   /* SDK verbs (legacy behavior, the default) */
    FC_MODE_MANUAL,        /* CRSF sticks, angle/acro, no position loops */
    FC_MODE_STABILIZED,    /* position hold + velocity sticks */
    FC_MODE_SWARM,         /* fc_show choreography playback */
} fc_mode_t;

typedef struct {
    fc_mode_t mode;          /* active mode */
    fc_mode_t sdk_request;   /* what the ground station asked for */
    /* CRSF input (normalized -1..+1; fed by fc_input_crsf) */
    float ch[16];
    float crsf_age_s;        /* time since last frame (starts huge) */
    bool  crsf_ever;         /* a frame has been seen since boot */
    bool  failsafed;         /* latched radio-loss reaction */
    bool  armed_sw;          /* last CH5 position (edge detection) */
    bool  acro;              /* MANUAL sub-mode from CH7 */
    float thr_low_s;         /* STABILIZED: throttle-held-low timer (land) */
} fc_modes_t;

struct fc_core_s;

/* One call per decoded RC_CHANNELS frame (~150 Hz from crsf_task, any rate
 * from tests/sim). nch <= 16; missing channels keep their previous value. */
void fc_input_crsf(struct fc_core_s *fc, const float *ch, int nch);

/* SDK `mode` verb. MANUAL is refused without a live radio; MANUAL/STABILIZED/
 * SWARM selected on CH6 by a live radio outrank the request until CH6 goes
 * low. Returns false if refused. */
bool fc_mode_request(struct fc_core_s *fc, fc_mode_t m);

fc_mode_t fc_mode_get(const struct fc_core_s *fc);
const char *fc_mode_name(fc_mode_t m);      /* "prog"|"manual"|"stab"|"swarm" */
bool fc_mode_parse(const char *s, fc_mode_t *out);

#ifdef __cplusplus
}
#endif
#endif /* FC_MODE_H */
