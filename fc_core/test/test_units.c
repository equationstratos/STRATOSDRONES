/* Unit tests: math, AHRS convergence, vertical KF tracking, mixer saturation.
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "fc_core/fc_core.h"
#include "../src/fc_internal.h" /* fc_mixer_run is internal; tested directly */
#include "test_util.h"
#include "sil_plant.h"

static void test_quat(void)
{
    fcq_t q = fcq_from_euler(0.3f, -0.2f, 1.1f);
    float r, p, y;
    fcq_to_euler(q, &r, &p, &y);
    CHECK_NEAR(r, 0.3f, 1e-4);
    CHECK_NEAR(p, -0.2f, 1e-4);
    CHECK_NEAR(y, 1.1f, 1e-4);

    /* rotate world-up into body and back */
    fcv3_t up_b = fcq_rotate_inv(q, fcv3(0, 0, 1));
    fcv3_t up_w = fcq_rotate(q, up_b);
    CHECK_NEAR(up_w.x, 0.0f, 1e-5);
    CHECK_NEAR(up_w.z, 1.0f, 1e-5);

    /* yaw-rate integration: 90 deg about z in 1 s */
    fcq_t qi = fcq_ident();
    for (int i = 0; i < 1000; i++)
        qi = fcq_integrate(qi, fcv3(0, 0, FC_PI / 2.0f), 0.001f);
    fcq_to_euler(qi, &r, &p, &y);
    CHECK_NEAR(y, FC_PI / 2.0f, 0.01);
}

static void test_ahrs(void)
{
    fc_core_t fc;
    fc_core_init(&fc);
    sil_plant_t pl;
    sil_init(&pl, 7);
    /* hold a static 10 deg roll attitude; AHRS must converge from level */
    pl.q = fcq_from_euler(10.0f * FC_DEG2RAD, 0, 0);
    fc_imu_t imu;
    for (int i = 0; i < 5000; i++) {
        sil_get_imu(&pl, &imu);
        fc_core_imu_update(&fc, &imu, 0.001f);
    }
    float r, p, y;
    fcq_to_euler(fc.ahrs.q, &r, &p, &y);
    CHECK_NEAR(r * FC_RAD2DEG, 10.0f, 1.5);
    CHECK_NEAR(p * FC_RAD2DEG, 0.0f, 1.5);
}

static void test_kfz(void)
{
    /* track z = 0.5 + 0.3 sin(2t) from noisy accel + ToF */
    fc_core_t fc;
    fc_core_init(&fc);
    sil_plant_t pl;
    sil_init(&pl, 11);
    float w = 2.0f, sum2 = 0.0f;
    int n = 0;
    for (int i = 0; i < 20000; i++) {
        float t = i * 0.001f;
        float z = 0.5f + 0.3f * sinf(w * t);
        float az = -0.3f * w * w * sinf(w * t);
        fc_imu_t imu = {{0, 0, 0}, {0, 0, FC_G + az + 0.25f * sil_randn(&pl)}};
        fc_core_imu_update(&fc, &imu, 0.001f);
        if (i % 20 == 0)
            fc_core_tof_update(&fc, z + 0.008f * sil_randn(&pl), true);
        if (t > 2.0f) { /* after convergence */
            float e = fc.kfz.z - z;
            sum2 += e * e;
            n++;
        }
    }
    float rmse = sqrtf(sum2 / (float)n);
    printf("kfz rmse=%.4f m\n", rmse);
    CHECK(rmse < 0.05f);
}

static void test_mixer(void)
{
    fc_core_t fc;
    fc_core_init(&fc);
    fc.state = FC_ST_FLYING;

    /* pure hover */
    fc.thrust = 0.5f;
    memset(fc.torque, 0, sizeof(fc.torque));
    fc_mixer_run(&fc);
    for (int i = 0; i < 4; i++) CHECK_NEAR(fc.motors[i], 0.5f, 1e-5);

    /* saturating roll request keeps motors in [0.04, 1] and differential sign */
    fc.thrust = 0.9f;
    fc.torque[0] = 0.8f;
    fc_mixer_run(&fc);
    for (int i = 0; i < 4; i++) CHECK(fc.motors[i] >= 0.04f && fc.motors[i] <= 1.0f);
    /* +roll torque -> left motors (M3 back-left, M4 front-left) higher */
    CHECK(fc.motors[2] > fc.motors[0]);
    CHECK(fc.motors[3] > fc.motors[1]);

    /* idle keeps motors off regardless of demands */
    fc.state = FC_ST_IDLE;
    fc_mixer_run(&fc);
    for (int i = 0; i < 4; i++) CHECK_NEAR(fc.motors[i], 0.0f, 1e-9);
}

int main(void)
{
    test_quat();
    test_ahrs();
    test_kfz();
    test_mixer();
    TEST_END();
}
