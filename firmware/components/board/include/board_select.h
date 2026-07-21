/* board_select.h — one firmware, several boards.
 *
 * Default = the Fr4n7 main board (brushed, Wi-Fi only). Build the STRATOS
 * TINYHOOP AIO (Fr4n10: DShot ESCs, CRSF socket, SX1262 LoRa) with:
 *
 *   idf.py build -DSDKCONFIG_DEFAULTS="sdkconfig.defaults" \
 *          -DCMAKE_C_FLAGS="-DSTRATOS_BOARD_TINYHOOP"
 *
 * The feature flags below are what the tasks/drivers actually test — new
 * boards add a pinmap + a block here, nothing else.
 * SPDX-License-Identifier: MIT */
#ifndef BOARD_SELECT_H
#define BOARD_SELECT_H

#ifdef STRATOS_BOARD_TINYHOOP
#include "board_pinmap_tinyhoop.h"
#define BOARD_NAME       "tinyhoop-mk1"
#define BOARD_HAS_DSHOT  1   /* outputs_dshot.c instead of LEDC motors */
#define BOARD_HAS_CRSF   1   /* crsf_task on PIN_CRSF_RX/TX */
#define BOARD_HAS_LORA   1   /* sx1262.c + lora_task */
#else
#include "board_pinmap.h"
#define BOARD_NAME       "fr4n7"
#define BOARD_HAS_DSHOT  0
#define BOARD_HAS_CRSF   0
#define BOARD_HAS_LORA   0
#ifndef VBAT_DIVIDER
#define VBAT_DIVIDER     2.0f   /* 100k/100k on the Fr4n7 board */
#endif
#endif

#endif /* BOARD_SELECT_H */
