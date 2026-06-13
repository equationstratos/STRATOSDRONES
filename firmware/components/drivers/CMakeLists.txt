idf_component_register(
    SRCS buses.c icm42688.c pmw3901.c vl53l1x.c spl06.c outputs.c
    INCLUDE_DIRS include
    REQUIRES driver esp_adc board fc_core
    PRIV_REQUIRES led_strip
)
