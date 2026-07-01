/* Video pipeline — core 1. MIPI-CSI camera (OV5647 via esp_video) ->
 * ESP32-P4 hardware H.264 encoder (esp_h264) -> raw Annex-B over UDP to
 * <client>:11111 — the exact Tello wire format (djitellopy-compatible).
 *
 * NOTE bring-up: exact V4L2 format negotiation (stride/alignment) and the
 * encoder input format are validated on hardware; see docs/bringup.md
 * "camera pipeline" — this file is written against esp_video 1.x and
 * esp_h264 1.1.x APIs and may need small adjustments with other versions.
 *
 * NOTE versions: firmware/main/idf_component.yml pins
 * espressif/esp_cam_sensor below 1.0.0 (the 1.0.0 release's published
 * sdkconfig.rename breaks kconfgen — a registry-side bug, not this repo's),
 * which resolves esp_video 0.8.x + esp_h264 1.1.x. This file therefore
 * avoids newer-only conveniences (e.g. ESP_H264_ENC_HW_CFG_DEFAULT, added
 * after 1.1.x) and sticks to the API surface common to 1.1.x and current.
 * Once esp_cam_sensor 1.0.0 is fixed upstream, the pins can move forward
 * without touching this file.
 * SPDX-License-Identifier: MIT */
#include <fcntl.h>
#include <string.h>
#include <sys/ioctl.h>
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "lwip/sockets.h"

#include "esp_h264_enc_single_hw.h"
#include "esp_video_init.h"
#include "linux/videodev2.h"

#include "stratos.h"

static const char *TAG = "video";

#define VIDEO_DEV "/dev/video0"
#define NAL_CHUNK 1460

_Atomic bool g_video_on = false;
_Atomic int g_video_height = 720;

static void send_au(int sock, uint32_t ip, const uint8_t *data, size_t len)
{
    struct sockaddr_in dst = {
        .sin_family = AF_INET,
        .sin_port = htons(11111),
        .sin_addr.s_addr = ip,
    };
    for (size_t off = 0; off < len; off += NAL_CHUNK) {
        size_t n = len - off > NAL_CHUNK ? NAL_CHUNK : len - off;
        sendto(sock, data + off, n, 0, (struct sockaddr *)&dst, sizeof(dst));
    }
}

static void video_task(void *arg)
{
    (void)arg;
    const esp_video_init_csi_config_t csi = {
        .sccb_config = {.init_sccb = false, .i2c_handle = NULL /* shared bus set in app_main */},
        .reset_pin = -1,
        .pwdn_pin = -1,
    };
    const esp_video_init_config_t vcfg = {.csi = &csi};
    if (esp_video_init(&vcfg) != ESP_OK) {
        ESP_LOGE(TAG, "esp_video_init failed (no camera?) — video disabled");
        vTaskDelete(NULL);
    }

    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    int fd = -1;
    esp_h264_enc_handle_t enc = NULL;
    esp_h264_enc_in_frame_t in_frame = {0};
    esp_h264_enc_out_frame_t out_frame = {0};
    int cur_h = 0;
    uint8_t *out_buf = NULL;

    for (;;) {
        if (!atomic_load(&g_video_on)) {
            if (fd >= 0) { close(fd); fd = -1; }
            if (enc) { esp_h264_enc_close(enc); esp_h264_enc_del(enc); enc = NULL; }
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }

        const int h = atomic_load(&g_video_height);
        const int w = (h == 1080) ? 1920 : 1280;
        if (fd < 0 || h != cur_h) {
            if (fd >= 0) close(fd);
            if (enc) { esp_h264_enc_close(enc); esp_h264_enc_del(enc); enc = NULL; }
            fd = open(VIDEO_DEV, O_RDWR);
            if (fd < 0) { vTaskDelay(pdMS_TO_TICKS(500)); continue; }
            struct v4l2_format fmt = {
                .type = V4L2_BUF_TYPE_VIDEO_CAPTURE,
                .fmt.pix = {.width = w, .height = h,
                            .pixelformat = V4L2_PIX_FMT_YUV420},
            };
            if (ioctl(fd, VIDIOC_S_FMT, &fmt) != 0) {
                ESP_LOGE(TAG, "S_FMT %dx%d failed", w, h);
                close(fd); fd = -1;
                vTaskDelay(pdMS_TO_TICKS(500));
                continue;
            }
            /* No ESP_H264_ENC_HW_CFG_DEFAULT(): the esp_h264 1.1.x that the
             * esp_cam_sensor <1.0.0 pin resolves (see idf_component.yml)
             * predates that macro — explicit init works there and on newer. */
            esp_h264_enc_cfg_hw_t cfg = {0};
            cfg.gop = 30;
            cfg.fps = 30;
            cfg.res.width = w;
            cfg.res.height = h;
            cfg.rc.bitrate = (h == 1080) ? 4 * 1000 * 1000 : 2 * 1000 * 1000;
            cfg.rc.qp_min = 10; /* bitrate-driven RC over the full QP range */
            cfg.rc.qp_max = 51;
            cfg.pic_type = ESP_H264_RAW_FMT_I420;
            if (esp_h264_enc_hw_new(&cfg, &enc) != ESP_H264_ERR_OK ||
                esp_h264_enc_open(enc) != ESP_H264_ERR_OK) {
                ESP_LOGE(TAG, "h264 hw encoder open failed");
                vTaskDelay(pdMS_TO_TICKS(500));
                continue;
            }
            if (!out_buf) out_buf = heap_caps_malloc(256 * 1024, MALLOC_CAP_SPIRAM);
            cur_h = h;
            ESP_LOGI(TAG, "streaming %dx%d@30 H.264 -> :11111", w, h);
        }

        /* capture one frame (read() path of esp_video VFS) */
        static uint8_t *frame;
        const size_t fsize = (size_t)w * h * 3 / 2;
        if (!frame) frame = heap_caps_malloc((size_t)1920 * 1080 * 3 / 2, MALLOC_CAP_SPIRAM);
        ssize_t r = read(fd, frame, fsize);
        if (r <= 0) { vTaskDelay(pdMS_TO_TICKS(5)); continue; }

        in_frame.raw_data.buffer = frame;
        in_frame.raw_data.len = fsize;
        out_frame.raw_data.buffer = out_buf;
        out_frame.raw_data.len = 256 * 1024;
        if (esp_h264_enc_process(enc, &in_frame, &out_frame) == ESP_H264_ERR_OK &&
            out_frame.length > 0) {
            uint32_t ip = atomic_load(&g_client_ip);
            if (ip) send_au(sock, ip, out_buf, out_frame.length);
        }
    }
}

void video_task_start(void)
{
    xTaskCreatePinnedToCore(video_task, "video", 8192, NULL, 5, NULL, 1);
}
