/* Tiny assert-and-report test helper. SPDX-License-Identifier: MIT */
#ifndef TEST_UTIL_H
#define TEST_UTIL_H

#include <stdio.h>
#include <math.h>

static int g_fail = 0;

#define CHECK(cond) do { \
    if (!(cond)) { \
        printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        g_fail++; \
    } \
} while (0)

#define CHECK_NEAR(a, b, tol) do { \
    double _a = (a), _b = (b), _t = (tol); \
    if (fabs(_a - _b) > _t) { \
        printf("FAIL %s:%d: %s=%.4f vs %s=%.4f (tol %.4f)\n", \
               __FILE__, __LINE__, #a, _a, #b, _b, _t); \
        g_fail++; \
    } \
} while (0)

#define TEST_END() do { \
    if (g_fail) { printf("%d check(s) FAILED\n", g_fail); return 1; } \
    printf("all checks passed\n"); return 0; \
} while (0)

#endif
