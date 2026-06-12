/* Flight state machine + command executor (Tello SDK semantics).
 * Runs at 100 Hz from the IMU tick. Motion commands complete asynchronously;
 * the SDK layer polls fc_cmd_status() to send the deferred "ok".
 * SPDX-License-Identifier: MIT */
#include "fc_core/fc_core.h"
#include "fc_internal.h"

static void enter_state(fc_core_t *fc, fc_state_t st)
{
    fc->state = st;
    fc->state_t = 0.0f;
    fc->land_still_s = 0.0f;
}

static void finish_cmd(fc_core_t *fc, fc_cmd_status_t st)
{
    fc->cmdr.status = st;
    fc->cmdr.active = FC_MCMD_NONE;
}

static uint32_t accept_cmd(fc_core_t *fc, fc_mcmd_t kind)
{
    fc->cmdr.active = kind;
    fc->cmdr.status = FC_CMD_RUNNING;
    fc->cmdr.seq++;
    return fc->cmdr.seq;
}

fc_cmd_status_t fc_cmd_status(const fc_core_t *fc, uint32_t seq)
{
    if (seq == 0 || seq > fc->cmdr.seq) return FC_CMD_NONE;
    if (seq < fc->cmdr.seq) return FC_CMD_DONE; /* superseded => had completed */
    return fc->cmdr.status;
}

void fc_note_sdk_traffic(fc_core_t *fc) { fc->sdk_traffic_age_s = 0.0f; }

/* ------------------------------------------------------------- commands */

uint32_t fc_cmd_takeoff(fc_core_t *fc)
{
    if (fc->state != FC_ST_IDLE) return 0;
    if (fc->bat_pct > 0.5f && fc->bat_pct < fc->par.bat_crit_pct) return 0;
    /* local frame origin = takeoff point */
    fc->hest.px = fc->hest.py = 0.0f;
    fc->hest.vx = fc->hest.vy = 0.0f;
    fc_ctl_reset(fc);
    fc->pos_sp.z = fc->par.takeoff_height_m;
    enter_state(fc, FC_ST_TAKEOFF);
    return accept_cmd(fc, FC_MCMD_TAKEOFF);
}

uint32_t fc_cmd_land(fc_core_t *fc)
{
    if (fc->state == FC_ST_IDLE || fc->state == FC_ST_EMERGENCY) return 0;
    enter_state(fc, FC_ST_LANDING);
    fc->pos_sp.x = fc->hest.px;
    fc->pos_sp.y = fc->hest.py;
    return accept_cmd(fc, FC_MCMD_LAND);
}

/* x fwd, y left, z up in the current heading frame, like the Tello SDK. */
static fcv3_t body_cm_to_world(const fc_core_t *fc, float x_cm, float y_cm, float z_cm)
{
    float cy = cosf(fc->yaw_sp), sy = sinf(fc->yaw_sp);
    float x = x_cm * 0.01f, y = y_cm * 0.01f, z = z_cm * 0.01f;
    return fcv3(cy * x - sy * y, sy * x + cy * y, z);
}

uint32_t fc_cmd_go(fc_core_t *fc, float x_cm, float y_cm, float z_cm, float speed_cms)
{
    if (fc->state != FC_ST_FLYING || fc->cmdr.active != FC_MCMD_NONE) return 0;
    fcv3_t cur = fcv3(fc->hest.px, fc->hest.py, fc->kfz.z);
    fc->cmdr.seg_start[0] = cur;
    fc->cmdr.seg_end[0] = fcv3_add(cur, body_cm_to_world(fc, x_cm, y_cm, z_cm));
    fc->cmdr.seg_count = 1;
    fc->cmdr.seg_idx = 0;
    fc->cmdr.seg_progress_m = 0.0f;
    fc->cmdr.speed_ms = fc_clampf(speed_cms, 10.0f, 100.0f) * 0.01f;
    return accept_cmd(fc, FC_MCMD_GOTO);
}

uint32_t fc_cmd_curve(fc_core_t *fc, float x1, float y1, float z1,
                      float x2, float y2, float z2, float speed_cms)
{
    /* v1: polyline through the intermediate point (documented approximation) */
    if (fc->state != FC_ST_FLYING || fc->cmdr.active != FC_MCMD_NONE) return 0;
    fcv3_t cur = fcv3(fc->hest.px, fc->hest.py, fc->kfz.z);
    fcv3_t p1 = fcv3_add(cur, body_cm_to_world(fc, x1, y1, z1));
    fcv3_t p2 = fcv3_add(cur, body_cm_to_world(fc, x2, y2, z2));
    fc->cmdr.seg_start[0] = cur;  fc->cmdr.seg_end[0] = p1;
    fc->cmdr.seg_start[1] = p1;   fc->cmdr.seg_end[1] = p2;
    fc->cmdr.seg_count = 2;
    fc->cmdr.seg_idx = 0;
    fc->cmdr.seg_progress_m = 0.0f;
    fc->cmdr.speed_ms = fc_clampf(speed_cms, 10.0f, 60.0f) * 0.01f;
    return accept_cmd(fc, FC_MCMD_GOTO);
}

uint32_t fc_cmd_rotate(fc_core_t *fc, float deg_cw)
{
    if (fc->state != FC_ST_FLYING || fc->cmdr.active != FC_MCMD_NONE) return 0;
    /* cw seen from above = negative rotation about world +z */
    fc->cmdr.yaw_target = fc->yaw_sp - deg_cw * FC_DEG2RAD;
    fc->cmdr.yaw_dir = (deg_cw >= 0.0f) ? -1.0f : 1.0f;
    return accept_cmd(fc, FC_MCMD_ROTATE);
}

uint32_t fc_cmd_flip(fc_core_t *fc, char dir)
{
    if (fc->state != FC_ST_FLYING || fc->cmdr.active != FC_MCMD_NONE) return 0;
    if (fc->par.flip_enable < 0.5f) return 0;
    if (fc->bat_pct < fc->par.flip_min_bat_pct) return 0;
    if (fc->kfz.z < 0.6f) return 0;
    fc_cmdr_t *c = &fc->cmdr;
    switch (dir) {
    case 'l': c->flip_axis = 0; c->flip_dir = 1.0f; break;   /* roll left  = +x rate */
    case 'r': c->flip_axis = 0; c->flip_dir = -1.0f; break;
    case 'f': c->flip_axis = 1; c->flip_dir = -1.0f; break;  /* nose down = -y rate */
    case 'b': c->flip_axis = 1; c->flip_dir = 1.0f; break;
    default: return 0;
    }
    c->flip_phase = 0;
    c->flip_t = 0.0f;
    c->flip_angle = 0.0f;
    enter_state(fc, FC_ST_FLIP);
    return accept_cmd(fc, FC_MCMD_FLIP);
}

void fc_cmd_rc(fc_core_t *fc, float lr, float fb, float ud, float yw)
{
    fc_cmdr_t *c = &fc->cmdr;
    c->rc[0] = fc_clampf(lr / 100.0f, -1.0f, 1.0f);
    c->rc[1] = fc_clampf(fb / 100.0f, -1.0f, 1.0f);
    c->rc[2] = fc_clampf(ud / 100.0f, -1.0f, 1.0f);
    c->rc[3] = fc_clampf(yw / 100.0f, -1.0f, 1.0f);
    c->rc_age_s = 0.0f;
    c->rc_active = (fabsf(c->rc[0]) > 0.05f || fabsf(c->rc[1]) > 0.05f ||
                    fabsf(c->rc[2]) > 0.05f || fabsf(c->rc[3]) > 0.05f);
}

void fc_cmd_stop(fc_core_t *fc)
{
    if (fc->cmdr.active == FC_MCMD_GOTO || fc->cmdr.active == FC_MCMD_ROTATE)
        finish_cmd(fc, FC_CMD_DONE);
    fc->pos_sp = fcv3(fc->hest.px, fc->hest.py, fc->kfz.z);
    fc->vel_ff = fcv3(0, 0, 0);
}

void fc_cmd_emergency(fc_core_t *fc)
{
    enter_state(fc, FC_ST_EMERGENCY);
    if (fc->cmdr.active != FC_MCMD_NONE) finish_cmd(fc, FC_CMD_ERROR);
    for (int i = 0; i < 4; i++) fc->motors[i] = 0.0f;
}

void fc_cmd_reset(fc_core_t *fc)
{
    if (fc->state == FC_ST_EMERGENCY) enter_state(fc, FC_ST_IDLE);
}

int fc_set_speed(fc_core_t *fc, float cms)
{
    if (cms < 10.0f || cms > 100.0f) return -1;
    fc->par.speed_cms = cms;
    return 0;
}

/* ------------------------------------------------------ 100 Hz executor */

static void run_goto(fc_core_t *fc, float dt)
{
    fc_cmdr_t *c = &fc->cmdr;
    fcv3_t a = c->seg_start[c->seg_idx], b = c->seg_end[c->seg_idx];
    fcv3_t ab = fcv3_sub(b, a);
    float len = fcv3_norm(ab);
    if (len < 1e-3f) {
        c->seg_progress_m = len;
    } else {
        c->seg_progress_m += c->speed_ms * dt;
        if (c->seg_progress_m > len) c->seg_progress_m = len;
        fcv3_t dir = fcv3_scale(ab, 1.0f / len);
        fc->pos_sp = fcv3_add(a, fcv3_scale(dir, c->seg_progress_m));
        bool last = (c->seg_idx == c->seg_count - 1);
        fc->vel_ff = (c->seg_progress_m < len || !last)
                         ? fcv3_scale(dir, c->speed_ms) : fcv3(0, 0, 0);
    }
    if (c->seg_progress_m >= len) {
        if (c->seg_idx + 1 < c->seg_count) {
            c->seg_idx++;
            c->seg_progress_m = 0.0f;
            return;
        }
        fcv3_t err = fcv3_sub(fc->pos_sp, fcv3(fc->hest.px, fc->hest.py, fc->kfz.z));
        if (fcv3_norm(err) < 0.15f) {
            fc->vel_ff = fcv3(0, 0, 0);
            finish_cmd(fc, FC_CMD_DONE);
        }
    }
}

static void run_rotate(fc_core_t *fc, float dt)
{
    fc_cmdr_t *c = &fc->cmdr;
    float rate = fc->par.yaw_rate_max_dps * FC_DEG2RAD * 0.8f;
    float remaining = c->yaw_target - fc->yaw_sp; /* not wrapped: multi-turn support */
    float step = rate * dt * c->yaw_dir;
    if (fabsf(step) >= fabsf(remaining)) {
        fc->yaw_sp = c->yaw_target;
        fc->yaw_sp = fc_wrap_pi(fc->yaw_sp);
        c->yaw_target = fc->yaw_sp;
        float r, p, y;
        fcq_to_euler(fc->ahrs.q, &r, &p, &y);
        if (fabsf(fc_wrap_pi(y - fc->yaw_sp)) < 5.0f * FC_DEG2RAD)
            finish_cmd(fc, FC_CMD_DONE);
    } else {
        fc->yaw_sp += step;
    }
}

static void run_flip(fc_core_t *fc, float dt)
{
    fc_cmdr_t *c = &fc->cmdr;
    float rate = fc->par.flip_rate_dps * FC_DEG2RAD;
    c->flip_t += dt;
    float gyr = (c->flip_axis == 0) ? fc->gyro.x : fc->gyro.y;
    switch (c->flip_phase) {
    case 0: /* thrust boost */
        fc->rate_sp = fcv3(0, 0, 0);
        fc->thrust = 0.85f;
        if (c->flip_t > 0.10f) { c->flip_phase = 1; c->flip_t = 0.0f; }
        break;
    case 1: /* rotate */
        c->flip_angle += gyr * dt;
        fc->thrust = 0.25f;
        fc->rate_sp = fcv3(0, 0, 0);
        if (c->flip_axis == 0) fc->rate_sp.x = c->flip_dir * rate;
        else fc->rate_sp.y = c->flip_dir * rate;
        if (fabsf(c->flip_angle) > 2.0f * FC_PI - 0.6f || c->flip_t > 1.2f) {
            c->flip_phase = 2;
            c->flip_t = 0.0f;
            /* recover: re-enter closed loop at current spot */
            float zsp = fc->pos_sp.z;
            fc_ctl_reset(fc);
            fc->pos_sp.z = zsp;
            enter_state(fc, FC_ST_FLYING);
            finish_cmd(fc, FC_CMD_DONE);
        }
        break;
    default:
        break;
    }
}

static void run_rc(fc_core_t *fc, float dt)
{
    fc_cmdr_t *c = &fc->cmdr;
    c->rc_age_s += dt;
    if (c->rc_age_s > 0.5f && c->rc_active) { /* stick stream lost: brake */
        c->rc[0] = c->rc[1] = c->rc[2] = c->rc[3] = 0.0f;
        c->rc_active = false;
        fc_cmd_stop(fc);
    }
    if (!c->rc_active || fc->state != FC_ST_FLYING || fc->cmdr.active != FC_MCMD_NONE)
        return;
    /* slide the position target: velocity control with automatic brake-to-hold */
    float vx_b = c->rc[1] * fc->par.rc_vmax_xy;   /* fb -> body x */
    float vy_b = -c->rc[0] * fc->par.rc_vmax_xy;  /* lr: positive = right = -y */
    float cy = cosf(fc->yaw_sp), sy = sinf(fc->yaw_sp);
    float vx_w = cy * vx_b - sy * vy_b;
    float vy_w = sy * vx_b + cy * vy_b;
    fc->pos_sp.x += vx_w * dt;
    fc->pos_sp.y += vy_w * dt;
    fc->pos_sp.z += c->rc[2] * fc->par.rc_vmax_z * dt;
    /* leash to actual position so the target can't run away */
    fc->pos_sp.x = fc_clampf(fc->pos_sp.x, fc->hest.px - 0.8f, fc->hest.px + 0.8f);
    fc->pos_sp.y = fc_clampf(fc->pos_sp.y, fc->hest.py - 0.8f, fc->hest.py + 0.8f);
    fc->pos_sp.z = fc_clampf(fc->pos_sp.z, fc->kfz.z - 0.6f, fc->kfz.z + 0.6f);
    fc->vel_ff = fcv3(vx_w, vy_w, c->rc[2] * fc->par.rc_vmax_z);
    fc->yaw_rate_sp_ext = -c->rc[3] * fc->par.yaw_rate_max_dps * FC_DEG2RAD;
    fc->yaw_sp = fc_wrap_pi(fc->yaw_sp + fc->yaw_rate_sp_ext * dt);
    if (!c->rc_active) fc->yaw_rate_sp_ext = 0.0f;
}

void fc_cmdr_step(fc_core_t *fc, float dt)
{
    fc->sdk_traffic_age_s += dt;
    if (fc->state != FC_ST_IDLE && fc->state != FC_ST_EMERGENCY)
        fc->flight_time_s += dt;
    fc->state_t += dt;

    /* ---- safety ---- */
    float tc = fcq_tilt_cos(fc->ahrs.q);
    float tilt_kill = cosf(fc->par.tilt_kill_deg * FC_DEG2RAD);
    if (fc->state != FC_ST_IDLE && fc->state != FC_ST_FLIP &&
        fc->state != FC_ST_EMERGENCY && tc < tilt_kill) {
        fc_cmd_emergency(fc);
        return;
    }
    bool airborne = (fc->state == FC_ST_TAKEOFF || fc->state == FC_ST_FLYING ||
                     fc->state == FC_ST_FLIP);
    if (airborne && fc->bat_pct > 0.5f && fc->bat_pct < fc->par.bat_crit_pct &&
        fc->state != FC_ST_LANDING) {
        fc->low_bat_land = true;
        fc_cmd_land(fc);
    }
    if (airborne && fc->sdk_traffic_age_s > fc->par.cmd_timeout_s &&
        fc->state != FC_ST_LANDING) {
        fc_cmd_land(fc);
    }

    /* ---- per-state behavior ---- */
    switch (fc->state) {
    case FC_ST_TAKEOFF:
        fc->vel_ff.z = (fc->kfz.z < fc->par.takeoff_height_m - 0.1f)
                           ? fc->par.takeoff_vz * 0.6f : 0.0f;
        if ((fc->kfz.z > fc->par.takeoff_height_m * 0.9f && fabsf(fc->kfz.vz) < 0.3f) ||
            fc->state_t > 6.0f) {
            fc->vel_ff.z = 0.0f;
            enter_state(fc, FC_ST_FLYING);
            if (fc->cmdr.active == FC_MCMD_TAKEOFF) finish_cmd(fc, FC_CMD_DONE);
        }
        break;
    case FC_ST_LANDING: {
        fc->pos_sp.z -= fc->par.land_vz * dt;
        fc->vel_ff.z = -fc->par.land_vz;
        bool ground = (fc->tof_valid && fc->tof_m < 0.06f) || fc->pos_sp.z < -0.5f;
        if (ground && fabsf(fc->kfz.vz) < 0.3f) fc->land_still_s += dt;
        else fc->land_still_s = 0.0f;
        if (fc->land_still_s > 0.4f || fc->state_t > 15.0f) {
            enter_state(fc, FC_ST_IDLE);
            fc->kfz.z = 0.0f; fc->kfz.vz = 0.0f;
            if (fc->cmdr.active == FC_MCMD_LAND) finish_cmd(fc, FC_CMD_DONE);
        }
        break;
    }
    case FC_ST_FLYING:
        switch (fc->cmdr.active) {
        case FC_MCMD_GOTO: run_goto(fc, dt); break;
        case FC_MCMD_ROTATE: run_rotate(fc, dt); break;
        default: break;
        }
        run_rc(fc, dt);
        break;
    case FC_ST_FLIP:
        run_flip(fc, dt);
        break;
    default:
        break;
    }
}
