# fc_core — platform-independent flight control core (host build + tests).
# The ESP-IDF firmware consumes the same sources via firmware/components/fc_core.
cmake_minimum_required(VERSION 3.16)
project(fc_core C)

set(CMAKE_C_STANDARD 99)
add_compile_options(-Wall -Wextra)

add_library(fc_core STATIC
    src/fc_core.c
    src/fc_estimator.c
    src/fc_control.c
    src/fc_commander.c
    src/fc_pid.c
    src/fc_params.c
)
target_include_directories(fc_core PUBLIC include PRIVATE src)
target_link_libraries(fc_core PUBLIC m)

if(PROJECT_IS_TOP_LEVEL OR FC_CORE_BUILD_TESTS)
    enable_testing()
    add_library(sil_plant STATIC test/sil_plant.c)
    target_link_libraries(sil_plant PUBLIC fc_core)
    target_include_directories(sil_plant PUBLIC test)

    foreach(t IN ITEMS test_units test_sil_flight)
        add_executable(${t} test/${t}.c)
        target_link_libraries(${t} PRIVATE fc_core sil_plant)
        add_test(NAME ${t} COMMAND ${t})
    endforeach()
endif()
