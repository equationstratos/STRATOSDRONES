/* Network task — core 1. UDP sockets for the Tello SDK surface:
 *   :8889 in  -> command lines -> flight task queue
 *   :8889 out <- replies (from flight task queue), to last client
 *   :8890 out <- state packets @10 Hz, to last client
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "lwip/sockets.h"

#include "stratos.h"

static const char *TAG = "net";

void net_task(void *arg)
{
    (void)arg;
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(8889),
        .sin_addr.s_addr = htonl(INADDR_ANY),
    };
    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        ESP_LOGE(TAG, "bind 8889 failed");
        vTaskDelete(NULL);
    }
    struct timeval tv = {.tv_sec = 0, .tv_usec = 20000}; /* 20 ms tick */
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    struct sockaddr_in client = {0};
    bool have_client = false;
    ESP_LOGI(TAG, "Tello SDK listening on :8889");

    for (;;) {
        char buf[SDK_LINE_MAX];
        struct sockaddr_in src;
        socklen_t slen = sizeof(src);
        ssize_t r = recvfrom(sock, buf, sizeof(buf) - 1, 0,
                             (struct sockaddr *)&src, &slen);
        if (r > 0) {
            buf[r] = '\0';
            client = src;
            have_client = true;
            atomic_store(&g_client_ip, src.sin_addr.s_addr);
            sdk_msg_t m;
            strlcpy(m.line, buf, sizeof(m.line));
            xQueueSend(g_cmd_queue, &m, 0);
        }

        sdk_msg_t out;
        while (have_client && xQueueReceive(g_reply_queue, &out, 0) == pdTRUE)
            sendto(sock, out.line, strlen(out.line), 0,
                   (struct sockaddr *)&client, sizeof(client));

        while (have_client && xQueueReceive(g_state_queue, &out, 0) == pdTRUE) {
            struct sockaddr_in dst = client;
            dst.sin_port = htons(8890);
            sendto(sock, out.line, strlen(out.line), 0,
                   (struct sockaddr *)&dst, sizeof(dst));
        }
    }
}
