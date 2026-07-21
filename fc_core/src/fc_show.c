/* Choreography executor: keyframe interpolation on the fleet clock.
 * fc_show_step runs every commander tick (100 Hz) — it always advances the
 * local clock, and drives the setpoints only while FLYING in SWARM mode.
 * SPDX-License-Identifier: MIT */
#include "fc_core/fc_core.h"
#include "fc_internal.h"

void fc_show_clear(fc_core_t *fc)
{
    fc->show.count = 0;
    fc->show.armed = false;
    fc->show.playing = false;
}

bool fc_show_add_key(fc_core_t *fc, uint32_t t_ms,
                     float x_cm, float y_cm, float z_cm, float yaw_deg)
{
    fc_show_t *s = &fc->show;
    if (s->count >= FC_SHOW_MAX_KEYS) return false;
    if (s->count > 0 && t_ms <= s->keys[s->count - 1].t_ms) return false;
    if (fabsf(x_cm) > 30000.0f || fabsf(y_cm) > 30000.0f ||
        fabsf(z_cm) > 30000.0f) return false;
    fc_show_key_t *k = &s->keys[s->count++];
    k->t_ms = t_ms;
    k->x_cm = (int16_t)x_cm;
    k->y_cm = (int16_t)y_cm;
    k->z_cm = (int16_t)z_cm;
    k->yaw_deg = (int16_t)yaw_deg;
    return true;
}

int fc_show_count(const fc_core_t *fc) { return fc->show.count; }

void fc_show_time_sync(fc_core_t *fc, double epoch_ms)
{
    fc->show.clock_off_ms = epoch_ms - fc->show.local_ms;
    fc->show.clock_synced = true;
}

double fc_show_epoch_ms(const fc_core_t *fc)
{
    return fc->show.local_ms + fc->show.clock_off_ms;
}

bool fc_show_start(fc_core_t *fc, double t0_epoch_ms)
{
    fc_show_t *s = &fc->show;
    if (s->count == 0) return false;
    s->t0_ms = (t0_epoch_ms <= 0.0) ? fc_show_epoch_ms(fc) : t0_epoch_ms;
    s->armed = true;
    s->playing = false;
    return true;
}

void fc_show_stop(fc_core_t *fc)
{
    fc_show_t *s = &fc->show;
    if (s->armed || s->playing) fc_cmd_stop(fc); /* park the setpoint here */
    s->armed = false;
    s->playing = false;
}

bool fc_show_playing(const fc_core_t *fc)
{
    return fc->show.playing || fc->show.armed;
}

/* keyframe -> world setpoint (same local frame as `go`: origin at arm) */
static void key_pos(const fc_show_key_t *k, fcv3_t *p)
{
    *p = fcv3(k->x_cm * 0.01f, k->y_cm * 0.01f, k->z_cm * 0.01f);
}

static void drive(fc_core_t *fc, double tau_ms)
{
    fc_show_t *s = &fc->show;
    /* before the first key: ease from wherever we are (hold + let the
     * position loop pull toward key 0 when its time comes) */
    if (tau_ms <= s->keys[0].t_ms) {
        fcv3_t p0;
        key_pos(&s->keys[0], &p0);
        fc->pos_sp = p0;
        fc->vel_ff = fcv3(0, 0, 0);
        fc->yaw_sp = fc_wrap_pi(-s->keys[0].yaw_deg * FC_DEG2RAD);
        return;
    }
    /* past the last key: done — hold it */
    if (tau_ms >= s->keys[s->count - 1].t_ms) {
        fcv3_t pe;
        key_pos(&s->keys[s->count - 1], &pe);
        fc->pos_sp = pe;
        fc->vel_ff = fcv3(0, 0, 0);
        fc->yaw_sp = fc_wrap_pi(-s->keys[s->count - 1].yaw_deg * FC_DEG2RAD);
        s->playing = false;
        return;
    }
    int i = 0;
    while (i + 1 < s->count && s->keys[i + 1].t_ms < tau_ms) i++;
    const fc_show_key_t *a = &s->keys[i], *b = &s->keys[i + 1];
    float T = (float)(b->t_ms - a->t_ms);
    float u = fc_clampf(((float)(tau_ms - a->t_ms)) / T, 0.0f, 1.0f);
    float e = 0.5f - 0.5f * cosf(FC_PI * u);           /* cosine easing */
    float de = 0.5f * FC_PI * sinf(FC_PI * u) / (T * 0.001f); /* d(e)/dt, 1/s */
    fcv3_t pa, pb;
    key_pos(a, &pa);
    key_pos(b, &pb);
    fcv3_t d = fcv3_sub(pb, pa);
    fc->pos_sp = fcv3_add(pa, fcv3_scale(d, e));
    fc->vel_ff = fcv3_scale(d, de);
    /* yaw: shortest arc, cw-positive keys -> internal ccw-positive */
    float ya = -a->yaw_deg * FC_DEG2RAD, yb = -b->yaw_deg * FC_DEG2RAD;
    fc->yaw_sp = fc_wrap_pi(ya + fc_wrap_pi(yb - ya) * e);
}

void fc_show_step(fc_core_t *fc, float dt)
{
    fc_show_t *s = &fc->show;
    s->local_ms += (double)dt * 1000.0;
    if (!s->armed && !s->playing) return;

    /* a live pilot yanking the sticks aborts the choreography */
    const fc_modes_t *m = &fc->modes;
    if (m->crsf_ever && m->crsf_age_s < 0.3f &&
        (fabsf(m->ch[0]) > 0.4f || fabsf(m->ch[1]) > 0.4f ||
         fabsf(m->ch[3]) > 0.4f)) {
        fc_show_stop(fc);
        return;
    }

    double epoch = fc_show_epoch_ms(fc);
    if (s->armed && epoch >= s->t0_ms) {
        s->armed = false;
        s->playing = true;
    }
    if (!s->playing) return;
    if (fc->modes.mode != FC_MODE_SWARM || fc->state != FC_ST_FLYING)
        return;                    /* clock runs; motion waits */
    drive(fc, epoch - s->t0_ms);
}
