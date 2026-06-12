/* fc_math.h — minimal vector/quaternion/filter helpers for the flight core.
 * Pure C99, no dependencies. Frames: body FLU (x fwd, y left, z up),
 * world ENU-like local frame (z up). Quaternion rotates body -> world.
 * SPDX-License-Identifier: MIT */
#ifndef FC_MATH_H
#define FC_MATH_H

#include <math.h>
#include <stdbool.h>

#define FC_G 9.80665f
#define FC_PI 3.14159265358979f
#define FC_DEG2RAD (FC_PI / 180.0f)
#define FC_RAD2DEG (180.0f / FC_PI)

typedef struct { float x, y, z; } fcv3_t;
typedef struct { float w, x, y, z; } fcq_t;

static inline float fc_clampf(float v, float lo, float hi)
{
    return v < lo ? lo : (v > hi ? hi : v);
}

static inline float fc_wrap_pi(float a)
{
    while (a > FC_PI) a -= 2.0f * FC_PI;
    while (a < -FC_PI) a += 2.0f * FC_PI;
    return a;
}

static inline fcv3_t fcv3(float x, float y, float z) { fcv3_t v = {x, y, z}; return v; }
static inline fcv3_t fcv3_add(fcv3_t a, fcv3_t b) { return fcv3(a.x + b.x, a.y + b.y, a.z + b.z); }
static inline fcv3_t fcv3_sub(fcv3_t a, fcv3_t b) { return fcv3(a.x - b.x, a.y - b.y, a.z - b.z); }
static inline fcv3_t fcv3_scale(fcv3_t a, float s) { return fcv3(a.x * s, a.y * s, a.z * s); }
static inline float fcv3_dot(fcv3_t a, fcv3_t b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
static inline fcv3_t fcv3_cross(fcv3_t a, fcv3_t b)
{
    return fcv3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x);
}
static inline float fcv3_norm(fcv3_t a) { return sqrtf(fcv3_dot(a, a)); }

static inline fcq_t fcq_ident(void) { fcq_t q = {1.0f, 0.0f, 0.0f, 0.0f}; return q; }

static inline fcq_t fcq_normalize(fcq_t q)
{
    float n = sqrtf(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
    if (n < 1e-9f) return fcq_ident();
    fcq_t r = {q.w / n, q.x / n, q.y / n, q.z / n};
    return r;
}

static inline fcq_t fcq_mul(fcq_t a, fcq_t b)
{
    fcq_t r;
    r.w = a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z;
    r.x = a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y;
    r.y = a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x;
    r.z = a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w;
    return r;
}

/* Rotate body-frame vector into world frame (q is body->world attitude). */
static inline fcv3_t fcq_rotate(fcq_t q, fcv3_t v)
{
    /* v' = v + 2*qv x (qv x v + w*v) */
    fcv3_t qv = fcv3(q.x, q.y, q.z);
    fcv3_t t = fcv3_scale(fcv3_cross(qv, v), 2.0f);
    return fcv3_add(v, fcv3_add(fcv3_scale(t, q.w), fcv3_cross(qv, t)));
}

/* Rotate world-frame vector into body frame. */
static inline fcv3_t fcq_rotate_inv(fcq_t q, fcv3_t v)
{
    fcq_t qc = {q.w, -q.x, -q.y, -q.z};
    return fcq_rotate(qc, v);
}

/* Integrate quaternion with body angular rate omega (rad/s) over dt. */
static inline fcq_t fcq_integrate(fcq_t q, fcv3_t omega, float dt)
{
    fcq_t w = {0.0f, omega.x, omega.y, omega.z};
    fcq_t qd = fcq_mul(q, w);
    q.w += 0.5f * qd.w * dt;
    q.x += 0.5f * qd.x * dt;
    q.y += 0.5f * qd.y * dt;
    q.z += 0.5f * qd.z * dt;
    return fcq_normalize(q);
}

/* ZYX euler (roll about x, pitch about y, yaw about z), radians. */
static inline void fcq_to_euler(fcq_t q, float *roll, float *pitch, float *yaw)
{
    *roll = atan2f(2.0f * (q.w * q.x + q.y * q.z), 1.0f - 2.0f * (q.x * q.x + q.y * q.y));
    float s = 2.0f * (q.w * q.y - q.z * q.x);
    *pitch = asinf(fc_clampf(s, -1.0f, 1.0f));
    *yaw = atan2f(2.0f * (q.w * q.z + q.x * q.y), 1.0f - 2.0f * (q.y * q.y + q.z * q.z));
}

static inline fcq_t fcq_from_euler(float roll, float pitch, float yaw)
{
    float cr = cosf(roll * 0.5f), sr = sinf(roll * 0.5f);
    float cp = cosf(pitch * 0.5f), sp = sinf(pitch * 0.5f);
    float cy = cosf(yaw * 0.5f), sy = sinf(yaw * 0.5f);
    fcq_t q;
    q.w = cr * cp * cy + sr * sp * sy;
    q.x = sr * cp * cy - cr * sp * sy;
    q.y = cr * sp * cy + sr * cp * sy;
    q.z = cr * cp * sy - sr * sp * cy;
    return q;
}

/* cos of tilt angle = world-z component of body-z axis. 1 = level, 0 = knife edge. */
static inline float fcq_tilt_cos(fcq_t q)
{
    return 1.0f - 2.0f * (q.x * q.x + q.y * q.y);
}

/* First-order low-pass filter. */
typedef struct { float y; float alpha; bool init; } fc_lpf1_t;

static inline void fc_lpf1_setup(fc_lpf1_t *f, float cutoff_hz, float sample_hz)
{
    if (cutoff_hz <= 0.0f || cutoff_hz >= sample_hz * 0.5f) {
        f->alpha = 1.0f; /* passthrough */
    } else {
        float c = 2.0f * FC_PI * cutoff_hz / sample_hz;
        f->alpha = c / (c + 1.0f);
    }
    f->y = 0.0f;
    f->init = false;
}

static inline float fc_lpf1_step(fc_lpf1_t *f, float x)
{
    if (!f->init) { f->y = x; f->init = true; }
    f->y += f->alpha * (x - f->y);
    return f->y;
}

#endif /* FC_MATH_H */
