/* Flight-mode manager + command-source arbitration. See fc_mode.h for the
 * rules. Runs from the 100 Hz commander tick (fc_mode_step), before the
 * state machine, so a mode/arm decision applies on the same tick.
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "fc_core/fc_core.h"
#include "fc_internal.h"

#define CRSF_TIMEOUT_S 0.3f
#define STICK_DEADBAND 0.06f

void fc_input_crsf(fc_core_t *fc, const float *ch, int nch)
{
    fc_modes_t *m = &fc->modes;
    if (nch > 16) nch = 16;
    for (int i = 0; i < nch; i++)
        m->ch[i] = fc_clampf(ch[i], -1.0f, 1.0f);
    m->crsf_age_s = 0.0f;
    m->crsf_ever = true;
}

fc_mode_t fc_mode_get(const fc_core_t *fc) { return fc->modes.mode; }

const char *fc_mode_name(fc_mode_t m)
{
    switch (m) {
    case FC_MODE_MANUAL: return "manual";
    case FC_MODE_STABILIZED: return "stab";
    case FC_MODE_SWARM: return "swarm";
    default: return "prog";
    }
}

bool fc_mode_parse(const char *s, fc_mode_t *out)
{
    if (!strcmp(s, "prog") || !strcmp(s, "program")) *out = FC_MODE_PROGRAM;
    else if (!strcmp(s, "manual")) *out = FC_MODE_MANUAL;
    else if (!strcmp(s, "stab") || !strcmp(s, "stabilized")) *out = FC_MODE_STABILIZED;
    else if (!strcmp(s, "swarm")) *out = FC_MODE_SWARM;
    else return false;
    return true;
}

static bool radio_live(const fc_modes_t *m)
{
    return m->crsf_ever && m->crsf_age_s < CRSF_TIMEOUT_S;
}

/* Smooth hand-over: catch the drone wherever it is. */
static void mode_transition(fc_core_t *fc, fc_mode_t to)
{
    fc_modes_t *m = &fc->modes;
    if (to == m->mode) return;
    if (fc->cmdr.active == FC_MCMD_GOTO || fc->cmdr.active == FC_MCMD_ROTATE)
        fc_cmd_stop(fc);                     /* cancel scripted motion */
    fc_cmd_rc(fc, 0, 0, 0, 0);               /* clear any SDK stick stream */
    if (fc->state == FC_ST_FLYING)
        fc_ctl_reset(fc);                    /* PIDs + setpoints = here, now */
    m->mode = to;
    m->thr_low_s = 0.0f;
}

bool fc_mode_request(fc_core_t *fc, fc_mode_t want)
{
    fc_modes_t *m = &fc->modes;
    if (want == FC_MODE_MANUAL && !radio_live(m))
        return false;                        /* no sticks -> no acro */
    m->sdk_request = want;
    /* With no radio (or CH6 low) the request applies on the next mode step;
     * apply immediately too so `mode x` + `mode ?` round-trips. */
    if (!radio_live(m) || m->ch[5] < -0.33f)
        mode_transition(fc, want);
    return true;
}

static void step_failsafe(fc_core_t *fc)
{
    fc_modes_t *m = &fc->modes;
    if (radio_live(m)) { m->failsafed = false; return; }
    if (!m->crsf_ever || m->failsafed) return;
    m->failsafed = true;
    bool airborne = (fc->state == FC_ST_TAKEOFF || fc->state == FC_ST_FLYING ||
                     fc->state == FC_ST_FLIP);
    if (m->mode == FC_MODE_MANUAL) {
        /* no position hold to fall back on: cut, per the FPV convention */
        if (fc->state != FC_ST_IDLE) fc_cmd_emergency(fc);
        m->mode = m->sdk_request == FC_MODE_MANUAL ? FC_MODE_PROGRAM : m->sdk_request;
    } else if (m->mode == FC_MODE_STABILIZED && airborne) {
        fc_cmd_land(fc);                     /* it can hold: bring it down */
    }
    /* PROGRAM/SWARM drones are not radio-owned: the LoRa link rules them */
}

static void step_arming(fc_core_t *fc)
{
    fc_modes_t *m = &fc->modes;
    bool armed = m->ch[4] > 0.25f;
    if (armed && !m->armed_sw) {             /* rising edge */
        if (fc->state == FC_ST_EMERGENCY) fc_cmd_reset(fc);
        if (m->mode == FC_MODE_MANUAL && fc->state == FC_ST_IDLE &&
            m->ch[2] < -0.9f) {              /* throttle low: direct arm */
            fc_ctl_reset(fc);
            fc_cmdr_force_state(fc, FC_ST_FLYING);
        }
    }
    if (!armed && m->armed_sw) {             /* falling edge: cut + idle */
        if (fc->state != FC_ST_IDLE) {
            fc_cmd_emergency(fc);
            fc_cmd_reset(fc);
        }
    }
    m->armed_sw = armed;
}

static float deadband(float v)
{
    if (fabsf(v) < STICK_DEADBAND) return 0.0f;
    return v;
}

static void step_stabilized_sticks(fc_core_t *fc, float dt)
{
    fc_modes_t *m = &fc->modes;
    if (!m->armed_sw) return;
    /* takeoff: armed on the ground, throttle pushed up */
    if (fc->state == FC_ST_IDLE && m->ch[2] > 0.3f) {
        fc_cmd_takeoff(fc);
        return;
    }
    if (fc->state != FC_ST_FLYING) return;
    /* sticks = velocity commands; center throttle = hold height */
    fc_cmd_rc(fc,
              deadband(m->ch[0]) * 100.0f,   /* roll  -> lr (right +) */
              deadband(m->ch[1]) * 100.0f,   /* pitch -> fb (fwd +)   */
              deadband(m->ch[2]) * 100.0f,   /* thr   -> ud           */
              deadband(m->ch[3]) * 100.0f);  /* yaw   -> yw (cw +)    */
    /* full-low throttle held 2 s = land */
    if (m->ch[2] < -0.9f) {
        m->thr_low_s += dt;
        if (m->thr_low_s > 2.0f) { fc_cmd_land(fc); m->thr_low_s = 0.0f; }
    } else {
        m->thr_low_s = 0.0f;
    }
}

void fc_mode_step(fc_core_t *fc, float dt)
{
    fc_modes_t *m = &fc->modes;
    m->crsf_age_s += dt;

    step_failsafe(fc);
    if (!radio_live(m)) return;

    /* CH6 3-pos: high MANUAL, mid STABILIZED, low = defer to SDK request */
    fc_mode_t want;
    if (m->ch[5] > 0.33f) want = FC_MODE_MANUAL;
    else if (m->ch[5] > -0.33f) want = FC_MODE_STABILIZED;
    else want = m->sdk_request;
    mode_transition(fc, want);
    m->acro = m->ch[6] > 0.0f;

    step_arming(fc);
    if (m->mode == FC_MODE_STABILIZED)
        step_stabilized_sticks(fc, dt);
    /* radio keeps the link watchdog fed: sticks are traffic */
    fc_note_sdk_traffic(fc);
}
