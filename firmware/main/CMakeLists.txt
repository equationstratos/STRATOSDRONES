idf_component_register(
    SRCS app_main.c flight_task.c net_task.c wifi_link.c video_task.c
    INCLUDE_DIRS .
    REQUIRES fc_core drivers board nvs_flash esp_wifi esp_netif esp_event lwip esp_timer
)
