/* fc_lorap.h — the STRATOS LoRa fleet protocol (framing + payloads).
 *
 * Pure C framing/parse shared verbatim by the drone firmware (lora_task via
 * sx1262.c), the ground dongle bridge, and mirrored byte-for-byte by
 * stratospy/lora.py (validated against the same golden fixture in
 * fc_core/test/test_lorap.c).
 *
 * Frame (max 64 B on air):
 *   'S' | ver:4 type:4 | swarm_id | src | dst | seq | len | payload<=55 | crc16
 * crc16 = CCITT (poly 0x1021, init 0xFFFF) over bytes 0..6+len.
 * Addresses: 0 = ground dongle, 1..250 = drones, 0xFF = broadcast.
 *
 * Types:
 *   ACK/NAK        payload = [acked_seq]
 *   CMD_LINE       one SDK ASCII line (no NUL) -> drone replies RESP_LINE
 *   RESP_LINE      SDK reply text
 *   TELEM          14 B binary (lorap_telem_t), 2 Hz per drone in the TDMA
 *                  slot drone_id * LORAP_SLOT_MS after each beacon
 *   SHOW_CHUNK     [first_idx u16][count u8][count x 12 B keyframes]
 *   TIME_BEACON    [epoch_ms u64] or [epoch_ms u64][t0_ms u64]
 *   SWARM_START    [t0_ms u64] (broadcast, repeat x3)
 *   SWARM_ABORT    empty (broadcast, repeat x3)
 *
 * LoRa is the command/telemetry/choreography channel, NOT a piloting
 * channel — shows are pre-uploaded, the air is mostly beacons. Practical
 * ceiling ~6 drones per channel at 2 Hz telemetry inside EU868 duty limits.
 * SPDX-License-Identifier: MIT */
#ifndef FC_LORAP_H
#define FC_LORAP_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define LORAP_MAGIC        'S'
#define LORAP_VERSION      1
#define LORAP_MAX_FRAME    64
#define LORAP_HDR_LEN      7
#define LORAP_MAX_PAYLOAD  (LORAP_MAX_FRAME - LORAP_HDR_LEN - 2)  /* 55 */
#define LORAP_ADDR_GROUND  0x00
#define LORAP_BROADCAST    0xFF
#define LORAP_SLOT_MS      40         /* TDMA telemetry slot per drone id */

typedef enum {
    LORAP_ACK = 0,
    LORAP_NAK = 1,
    LORAP_CMD_LINE = 2,
    LORAP_RESP_LINE = 3,
    LORAP_TELEM = 4,
    LORAP_SHOW_CHUNK = 5,
    LORAP_TIME_BEACON = 6,
    LORAP_SWARM_START = 7,
    LORAP_SWARM_ABORT = 8,
} lorap_type_t;

typedef struct {
    uint8_t type;                     /* lorap_type_t */
    uint8_t swarm_id;                 /* fleet selector (channel-sharing) */
    uint8_t src, dst;
    uint8_t seq;
    uint8_t len;
    uint8_t payload[LORAP_MAX_PAYLOAD];
} lorap_frame_t;

/* 14-byte packed telemetry (little-endian) */
typedef struct {
    uint8_t state;                    /* fc_state_t */
    uint8_t mode;                     /* fc_mode_t */
    int16_t x_cm, y_cm, z_cm;
    int16_t yaw_deg;                  /* cw-positive */
    uint16_t vbat_mv;
    uint8_t bat_pct;
    int8_t rssi_dbm;                  /* CRSF uplink rssi (0 if no radio) */
    uint8_t flags;                    /* bit0: show armed/playing */
} lorap_telem_t;
#define LORAP_TELEM_LEN 14

uint16_t lorap_crc16(const uint8_t *p, size_t n);

/* Returns total frame length written to out (>= LORAP_HDR_LEN + 2), or 0. */
size_t lorap_encode(uint8_t out[LORAP_MAX_FRAME], const lorap_frame_t *f);
/* Strict parse of one frame; false on magic/version/len/crc mismatch. */
bool lorap_decode(const uint8_t *in, size_t n, lorap_frame_t *f);

/* payload helpers (little-endian, no struct punning) */
void lorap_pack_telem(uint8_t payload[LORAP_TELEM_LEN], const lorap_telem_t *t);
void lorap_unpack_telem(const uint8_t payload[LORAP_TELEM_LEN], lorap_telem_t *t);
void lorap_pack_u64(uint8_t out[8], uint64_t v);
uint64_t lorap_unpack_u64(const uint8_t in[8]);

/* SHOW_CHUNK: how many 12-B keyframes fit per frame (with the 3-B header) */
#define LORAP_KEYS_PER_CHUNK ((LORAP_MAX_PAYLOAD - 3) / 12)

#ifdef __cplusplus
}
#endif
#endif /* FC_LORAP_H */
