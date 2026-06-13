/* Motor PWM (LEDC), battery ADC, WS2812 status LEDs.
 * SPDX-License-Identifier: MIT */
#include "driver/ledc.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "led_strip.h"
#include "board_pinmap.h"
#include "drivers.h"
#include "esp_log.h"

static const char *TAG = "outputs";

/* ---------------- motors: 4x LEDC @ 20 kHz, 12-bit ---------------- */
static const int k_motor_gpio[4] = {PIN_MOTOR_1, PIN_MOTOR_2, PIN_MOTOR_3, PIN_MOTOR_4};

esp_err_t motors_init(void)
{
    const ledc_timer_config_t tcfg = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_12_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = 20000,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_RETURN_ON_ERROR(ledc_timer_config(&tcfg), TAG, "timer");
    for (int i = 0; i < 4; i++) {
        const ledc_channel_config_t ccfg = {
            .gpio_num = k_motor_gpio[i],
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel = LEDC_CHANNEL_0 + i,
            .timer_sel = LEDC_TIMER_0,
            .duty = 0,
            .hpoint = 0,
        };
        ESP_RETURN_ON_ERROR(ledc_channel_config(&ccfg), TAG, "chan");
    }
    ESP_LOGI(TAG, "motors armed-capable (20 kHz)");
    return ESP_OK;
}

void motors_write(const float duty[4])
{
    for (int i = 0; i < 4; i++) {
        float d = duty[i];
        if (d < 0.0f) d = 0.0f;
        if (d > 1.0f) d = 1.0f;
        ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0 + i, (uint32_t)(d * 4095.0f));
        ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0 + i);
    }
}

void motors_kill(void)
{
    const float z[4] = {0, 0, 0, 0};
    motors_write(z);
}

/* ---------------- battery ADC (100k/100k divider) ---------------- */
static adc_oneshot_unit_handle_t s_adc;
static adc_cali_handle_t s_cali;
static bool s_cali_ok;

esp_err_t vbat_init(void)
{
    const adc_oneshot_unit_init_cfg_t ucfg = {.unit_id = VBAT_ADC_UNIT};
    ESP_RETURN_ON_ERROR(adc_oneshot_new_unit(&ucfg, &s_adc), TAG, "adc unit");
    const adc_oneshot_chan_cfg_t ccfg = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_RETURN_ON_ERROR(adc_oneshot_config_channel(s_adc, VBAT_ADC_CHANNEL, &ccfg),
                        TAG, "adc chan");
    const adc_cali_curve_fitting_config_t cal = {
        .unit_id = VBAT_ADC_UNIT,
        .chan = VBAT_ADC_CHANNEL,
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    s_cali_ok = adc_cali_create_scheme_curve_fitting(&cal, &s_cali) == ESP_OK;
    return ESP_OK;
}

float vbat_read(void)
{
    int raw = 0, mv = 0;
    if (adc_oneshot_read(s_adc, VBAT_ADC_CHANNEL, &raw) != ESP_OK) return 0.0f;
    if (s_cali_ok && adc_cali_raw_to_voltage(s_cali, raw, &mv) == ESP_OK)
        return (float)mv * 2.0f / 1000.0f; /* 100k/100k divider */
    return (float)raw / 4095.0f * 3.3f * 2.0f;
}

/* ---------------- WS2812B-2020 x2 ---------------- */
static led_strip_handle_t s_strip;

esp_err_t leds_init(void)
{
    const led_strip_config_t scfg = {
        .strip_gpio_num = PIN_WS2812,
        .max_leds = 2,
    };
    const led_strip_rmt_config_t rcfg = {.resolution_hz = 10 * 1000 * 1000};
    ESP_RETURN_ON_ERROR(led_strip_new_rmt_device(&scfg, &rcfg, &s_strip), TAG, "strip");
    led_strip_clear(s_strip);
    return ESP_OK;
}

void leds_set(uint8_t r, uint8_t g, uint8_t b)
{
    if (!s_strip) return;
    led_strip_set_pixel(s_strip, 0, r, g, b);
    led_strip_set_pixel(s_strip, 1, r, g, b);
    led_strip_refresh(s_strip);
}
