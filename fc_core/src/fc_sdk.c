/* fc_sdk.c — Tello SDK 2.0 command parsing and replies. See fc_sdk.h.
 * Wire behavior references: Ryze "Tello SDK 2.0 User Guide" (public PDF).
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "fc_core/fc_sdk.h"

#define MAX_TOK 12

static void reply(fc_sdk_t *s, const char *msg)
{
    if (s->plat && s->plat->send_reply)
        s->plat->send_reply(s->user, msg);
}

static int tokenize(char *line, char *tok[], int max)
{
    int n = 0;
    char *p = line;
    while (n < max) {
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '\0') break;
        tok[n++] = p;
        while (*p && *p != ' ' && *p != '\t') p++;
        if (*p) *p++ = '\0';
    }
    return n;
}

static bool parse_f(const char *t, float *out)
{
    char *end;
    float v = strtof(t, &end);
    if (end == t || *end != '\0') return false;
    *out = v;
    return true;
}

/* start tracking a motion command; replies are deferred to fc_sdk_poll() */
static void defer(fc_sdk_t *s, uint32_t seq)
{
    if (seq == 0) {
        reply(s, "error");
        return;
    }
    s->pending = true;
    s->pending_seq = seq;
}

static bool range_ok(float v, float lo, float hi)
{
    return v >= lo && v <= hi;
}

static void handle_move(fc_sdk_t *s, const char *dir, float d)
{
    if (!range_ok(d, 20, 500)) { reply(s, "error"); return; }
    float x = 0, y = 0, z = 0;
    if (!strcmp(dir, "forward")) x = d;
    else if (!strcmp(dir, "back")) x = -d;
    else if (!strcmp(dir, "left")) y = d;
    else if (!strcmp(dir, "right")) y = -d;
    else if (!strcmp(dir, "up")) z = d;
    else if (!strcmp(dir, "down")) z = -d;
    defer(s, fc_cmd_go(s->fc, x, y, z, s->fc->par.speed_cms));
}

static void handle_ext(fc_sdk_t *s, char *tok[], int n)
{
    if (n >= 5 && !strcmp(tok[1], "led")) {
        float r, g, b;
        if (parse_f(tok[2], &r) && parse_f(tok[3], &g) && parse_f(tok[4], &b) &&
            range_ok(r, 0, 255) && range_ok(g, 0, 255) && range_ok(b, 0, 255)) {
            if (s->plat->set_led)
                s->plat->set_led(s->user, (uint8_t)r, (uint8_t)g, (uint8_t)b);
            reply(s, "led ok");
            return;
        }
    } else if (n >= 2 && !strcmp(tok[1], "version?")) {
        reply(s, FC_SDK_VERSION_STR);
        return;
    }
    reply(s, "error");
}

void fc_sdk_init(fc_sdk_t *s, fc_core_t *fc, const fc_sdk_platform_t *plat, void *user)
{
    memset(s, 0, sizeof(*s));
    s->fc = fc;
    s->plat = plat;
    s->user = user;
    s->video_height = 720;
}

void fc_sdk_handle_line(fc_sdk_t *s, const char *line_in)
{
    char line[128];
    size_t len = strlen(line_in);
    if (len >= sizeof(line)) { reply(s, "error"); return; }
    memcpy(line, line_in, len + 1);
    /* strip trailing CR/LF */
    while (len && (line[len - 1] == '\r' || line[len - 1] == '\n'))
        line[--len] = '\0';

    char *tok[MAX_TOK];
    int n = tokenize(line, tok, MAX_TOK);
    if (n == 0) return;
    fc_note_sdk_traffic(s->fc);

    const char *c = tok[0];

    if (!strcmp(c, "command")) { s->sdk_mode = true; reply(s, "ok"); return; }
    if (!s->sdk_mode) return; /* Tello ignores everything before "command" */

    /* --- no-reply commands (keep client response queues aligned) --- */
    if (!strcmp(c, "rc")) {
        if (n == 5) {
            float a, b, cc, d;
            if (parse_f(tok[1], &a) && parse_f(tok[2], &b) &&
                parse_f(tok[3], &cc) && parse_f(tok[4], &d))
                fc_cmd_rc(s->fc, a, b, cc, d);
        }
        return;
    }
    if (!strcmp(c, "emergency")) { fc_cmd_emergency(s->fc); return; }

    /* --- immediate replies --- */
    if (!strcmp(c, "stop")) { fc_cmd_stop(s->fc); reply(s, "ok"); return; }
    if (!strcmp(c, "streamon")) {
        s->stream_on = true;
        if (s->plat->video_ctrl) s->plat->video_ctrl(s->user, true, s->video_height);
        reply(s, "ok");
        return;
    }
    if (!strcmp(c, "streamoff")) {
        s->stream_on = false;
        if (s->plat->video_ctrl) s->plat->video_ctrl(s->user, false, s->video_height);
        reply(s, "ok");
        return;
    }
    if (!strcmp(c, "speed") && n == 2) {
        float v;
        if (parse_f(tok[1], &v) && fc_set_speed(s->fc, v) == 0) reply(s, "ok");
        else reply(s, "error");
        return;
    }
    if (!strcmp(c, "video") && n == 2) { /* STRATOS extension */
        float h;
        if (parse_f(tok[1], &h) && ((int)h == 720 || (int)h == 1080)) {
            s->video_height = (int)h;
            if (s->stream_on && s->plat->video_ctrl)
                s->plat->video_ctrl(s->user, true, s->video_height);
            reply(s, "ok");
        } else reply(s, "error");
        return;
    }
    if (!strcmp(c, "param") && n >= 2) { /* STRATOS extension */
        size_t l = strlen(tok[1]);
        if (n == 2 && l > 1 && tok[1][l - 1] == '?') {
            tok[1][l - 1] = '\0';
            float v;
            if (fc_param_get(s->fc, tok[1], &v)) {
                char b[48];
                snprintf(b, sizeof(b), "%g", (double)v);
                reply(s, b);
            } else reply(s, "error");
        } else if (n == 3) {
            float v;
            if (parse_f(tok[2], &v) && fc_param_set(s->fc, tok[1], v)) reply(s, "ok");
            else reply(s, "error");
        } else reply(s, "error");
        return;
    }
    if (!strcmp(c, "wifi") && n == 3) {
        bool ok = s->plat->wifi_config ?
                  s->plat->wifi_config(s->user, tok[1], tok[2], false) : true;
        reply(s, ok ? "ok" : "error");
        return;
    }
    if (!strcmp(c, "ap") && n == 3) {
        bool ok = s->plat->wifi_config ?
                  s->plat->wifi_config(s->user, tok[1], tok[2], true) : true;
        reply(s, ok ? "ok" : "error");
        return;
    }
    if (!strcmp(c, "mon") || !strcmp(c, "moff") || !strcmp(c, "mdirection")) {
        reply(s, "ok"); /* mission pads not supported in v1; harmless ok */
        return;
    }
    if (!strcmp(c, "EXT")) { handle_ext(s, tok, n); return; }

    /* --- STRATOS mode / show / figure extensions --- */
    if (!strcmp(c, "mode") && n == 2) {
        if (!strcmp(tok[1], "?")) {
            reply(s, fc_mode_name(fc_mode_get(s->fc)));
            return;
        }
        fc_mode_t want;
        if (fc_mode_parse(tok[1], &want) && fc_mode_request(s->fc, want))
            reply(s, "ok");
        else reply(s, "error");
        return;
    }
    if (!strcmp(c, "timesync") && n == 2) {
        char *end;
        double ms = strtod(tok[1], &end); /* epoch ms: needs double precision */
        if (end != tok[1] && *end == '\0' && ms >= 0.0) {
            fc_show_time_sync(s->fc, ms);
            reply(s, "ok");
        } else reply(s, "error");
        return;
    }
    if (!strcmp(c, "show") && n >= 2) {
        if (!strcmp(tok[1], "clear") && n == 2) {
            fc_show_clear(s->fc);
            reply(s, "ok");
        } else if (!strcmp(tok[1], "count?") && n == 2) {
            char b[16];
            snprintf(b, sizeof(b), "%d", fc_show_count(s->fc));
            reply(s, b);
        } else if (!strcmp(tok[1], "key") && n == 7) {
            float t, x, y, z, yw;
            if (parse_f(tok[2], &t) && parse_f(tok[3], &x) &&
                parse_f(tok[4], &y) && parse_f(tok[5], &z) &&
                parse_f(tok[6], &yw) && t >= 0 &&
                fc_show_add_key(s->fc, (uint32_t)t, x, y, z, yw))
                reply(s, "ok");
            else reply(s, "error");
        } else if (!strcmp(tok[1], "start") && n == 3) {
            char *end;
            double t0 = strtod(tok[2], &end); /* epoch ms (0 = now) */
            if (end != tok[2] && *end == '\0' && fc_show_start(s->fc, t0))
                reply(s, "ok");
            else reply(s, "error");
        } else if (!strcmp(tok[1], "stop") && n == 2) {
            fc_show_stop(s->fc);
            reply(s, "ok");
        } else reply(s, "error");
        return;
    }
    if (!strcmp(c, "figure") && n >= 2) {
        float p[5];
        bool ok = true;
        int np = n - 2;
        if (np > 5) { reply(s, "error"); return; }
        for (int i = 0; i < np && ok; i++) ok = parse_f(tok[i + 2], &p[i]);
        if (!ok) { reply(s, "error"); return; }
        if (!strcmp(tok[1], "circle") && np == 3)
            ok = fc_figure_circle(s->fc, p[0], p[1], p[2]);
        else if (!strcmp(tok[1], "spiral") && np == 4)
            ok = fc_figure_spiral(s->fc, p[0], p[1], p[2], p[3]);
        else if (!strcmp(tok[1], "line") && np == 4)
            ok = fc_figure_line(s->fc, p[0], p[1], p[2], p[3]);
        else if (!strcmp(tok[1], "poly") && np == 3)
            ok = fc_figure_poly(s->fc, (int)p[0], p[1], p[2]);
        else if (!strcmp(tok[1], "wave") && np == 5)
            ok = fc_figure_wave(s->fc, p[0], p[1], p[2], p[3], p[4]);
        else ok = false;
        reply(s, ok ? "ok" : "error");
        return;
    }

    /* --- read commands --- */
    if (c[strlen(c) - 1] == '?') {
        char b[64];
        if (!strcmp(c, "speed?")) {
            snprintf(b, sizeof(b), "%.1f", (double)s->fc->par.speed_cms);
        } else if (!strcmp(c, "battery?")) {
            snprintf(b, sizeof(b), "%d", (int)s->fc->bat_pct);
        } else if (!strcmp(c, "time?")) {
            snprintf(b, sizeof(b), "%d", (int)s->fc->flight_time_s);
        } else if (!strcmp(c, "wifi?")) {
            snprintf(b, sizeof(b), "%d",
                     s->plat->get_wifi_snr ? s->plat->get_wifi_snr(s->user) : 90);
        } else if (!strcmp(c, "sdk?")) {
            snprintf(b, sizeof(b), "20");
        } else if (!strcmp(c, "mode?")) {
            snprintf(b, sizeof(b), "%s", fc_mode_name(fc_mode_get(s->fc)));
        } else if (!strcmp(c, "sn?")) {
            snprintf(b, sizeof(b), "%s",
                     s->plat->get_sn ? s->plat->get_sn(s->user) : "STRATOS001");
        } else {
            snprintf(b, sizeof(b), "error");
        }
        reply(s, b);
        return;
    }

    /* --- motion commands (deferred replies) --- */
    if (s->pending) { reply(s, "error"); return; } /* one at a time, like Tello */

    if (!strcmp(c, "takeoff")) { defer(s, fc_cmd_takeoff(s->fc)); return; }
    if (!strcmp(c, "land")) { defer(s, fc_cmd_land(s->fc)); return; }
    if ((!strcmp(c, "up") || !strcmp(c, "down") || !strcmp(c, "left") ||
         !strcmp(c, "right") || !strcmp(c, "forward") || !strcmp(c, "back")) && n == 2) {
        float d;
        if (parse_f(tok[1], &d)) handle_move(s, c, d);
        else reply(s, "error");
        return;
    }
    if ((!strcmp(c, "cw") || !strcmp(c, "ccw")) && n == 2) {
        float d;
        if (parse_f(tok[1], &d) && range_ok(d, 1, 360))
            defer(s, fc_cmd_rotate(s->fc, !strcmp(c, "cw") ? d : -d));
        else reply(s, "error");
        return;
    }
    if (!strcmp(c, "flip") && n == 2) {
        defer(s, fc_cmd_flip(s->fc, tok[1][0]));
        return;
    }
    if (!strcmp(c, "go") && n == 5) {
        float x, y, z, v;
        if (parse_f(tok[1], &x) && parse_f(tok[2], &y) &&
            parse_f(tok[3], &z) && parse_f(tok[4], &v) &&
            range_ok(x, -500, 500) && range_ok(y, -500, 500) &&
            range_ok(z, -500, 500) && range_ok(v, 10, 100) &&
            !(x > -20 && x < 20 && y > -20 && y < 20 && z > -20 && z < 20))
            defer(s, fc_cmd_go(s->fc, x, y, z, v));
        else reply(s, "error");
        return;
    }
    if (!strcmp(c, "curve") && n == 8) {
        float p[7];
        bool ok = true;
        for (int i = 0; i < 7; i++) ok = ok && parse_f(tok[i + 1], &p[i]);
        ok = ok && range_ok(p[6], 10, 60);
        for (int i = 0; i < 6 && ok; i++) ok = range_ok(p[i], -500, 500);
        if (ok)
            defer(s, fc_cmd_curve(s->fc, p[0], p[1], p[2], p[3], p[4], p[5], p[6]));
        else reply(s, "error");
        return;
    }

    reply(s, "error");
}

void fc_sdk_poll(fc_sdk_t *s)
{
    if (!s->pending) return;
    fc_cmd_status_t st = fc_cmd_status(s->fc, s->pending_seq);
    if (st == FC_CMD_DONE) {
        s->pending = false;
        reply(s, "ok");
    } else if (st == FC_CMD_ERROR || st == FC_CMD_NONE) {
        s->pending = false;
        reply(s, "error");
    }
}

int fc_sdk_state_string(fc_sdk_t *s, char *buf, size_t n)
{
    fc_telemetry_t t;
    fc_core_get_telemetry(s->fc, &t);
    return snprintf(buf, n,
        "pitch:%d;roll:%d;yaw:%d;vgx:%d;vgy:%d;vgz:%d;"
        "templ:%d;temph:%d;tof:%d;h:%d;bat:%d;baro:%.2f;time:%d;"
        "agx:%.2f;agy:%.2f;agz:%.2f;\r\n",
        t.pitch_deg, t.roll_deg, t.yaw_deg,
        t.vgx_cms, t.vgy_cms, t.vgz_cms,
        t.templ_c, t.temph_c, t.tof_cm, t.h_cm, t.bat_pct,
        (double)t.baro_m, t.time_s,
        (double)t.agx_mg, (double)t.agy_mg, (double)t.agz_mg);
}
