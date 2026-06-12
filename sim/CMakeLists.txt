# STRATOSDRONE simulation targets.
#
#   sitl_runner       always built (POSIX only, no dependencies)
#   StratosFcSystem   Gazebo Harmonic (gz-sim8) plugin — built when gz-sim8 is
#                     found; otherwise skipped with a notice
#   gz_video_bridge   gz camera -> H.264 (x264) -> UDP 11111 Tello video bridge
cmake_minimum_required(VERSION 3.16)
project(stratos_sim CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
add_compile_options(-Wall -Wextra)

set(FC_CORE_BUILD_TESTS OFF)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../fc_core fc_core)

# SIL plant is reused by both the SITL runner and (as ground truth checks) tests
add_library(sil_plant STATIC ${CMAKE_CURRENT_SOURCE_DIR}/../fc_core/test/sil_plant.c)
target_include_directories(sil_plant PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../fc_core/test)
target_link_libraries(sil_plant PUBLIC fc_core)

add_executable(sitl_runner sitl/sitl_runner.c)
target_link_libraries(sitl_runner PRIVATE fc_core sil_plant)

# ---------------------------------------------------------------- Gazebo
find_package(gz-sim8 QUIET)
if(gz-sim8_FOUND)
    message(STATUS "gz-sim8 found — building Gazebo plugin")
    add_library(StratosFcSystem SHARED gazebo/StratosFcSystem.cc)
    target_link_libraries(StratosFcSystem PRIVATE fc_core gz-sim8::gz-sim8)

    find_library(X264_LIB x264)
    if(X264_LIB)
        add_executable(gz_video_bridge gazebo/gz_video_bridge.cc)
        target_link_libraries(gz_video_bridge PRIVATE gz-sim8::gz-sim8 ${X264_LIB})
    else()
        message(STATUS "libx264 not found — gz_video_bridge skipped")
    endif()
else()
    message(STATUS "gz-sim8 NOT found — Gazebo plugin skipped (SITL still available)")
endif()
