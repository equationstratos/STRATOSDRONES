/* fc_crsf.h — platform-free CRSF (ExpressLRS) byte-stream parser.
 *
 * The firmware's crsf_task pumps raw UART bytes (420 kbaud 8N1) in here;
 * the parser resynchronizes on garbage, checks CRC8 (DVB-S2, poly 0xD5)
 * and decodes RC_CHANNELS_PACKED (type 0x16: 16 channels x 11 bits).
 * Also builds the battery telemetry downlink frame (type 0x08).
 *
 * Frame on the wire:  [addr 0xC8] [len] [type] [payload...] [crc8]
 * with len = 1 (type) + payload + 1 (crc), and crc over type+payload.
 * Channel range: 172..1811, center 992 (TICKS_TO_US convention).
 * SPDX-License-Identifier: MIT */
#ifndef FC_CRSF_H
#define FC_CRSF_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CRSF_SYNC_FC        0xC8
#define CRSF_TYPE_CHANNELS  0x16
#define CRSF_TYPE_LINK      0x14
#define CRSF_TYPE_BATTERY   0x08
#define CRSF_MAX_FRAME      64

typedef struct {
    /* parser state */
    uint8_t buf[CRSF_MAX_FRAME];
    int pos;                 /* bytes collected of the current frame */
    /* last decoded channels */
    uint16_t ch_raw[16];     /* 172..1811 */
    bool fresh;              /* a channels frame landed since last _norm */
    /* link statistics (type 0x14), when the RX sends them */
    int8_t rssi_dbm;
    uint8_t lq_pct;
    /* counters */
    uint32_t frames, crc_errors;
} fc_crsf_t;

void fc_crsf_init(fc_crsf_t *c);

/* Feed raw bytes; returns how many RC_CHANNELS frames were decoded. */
int fc_crsf_input(fc_crsf_t *c, const uint8_t *data, size_t n);

/* Normalized channels: (raw - 992) / 819.5 clamped to -1..+1.
 * Clears the fresh flag. */
void fc_crsf_norm(fc_crsf_t *c, float out[16]);

uint8_t fc_crsf_crc8(const uint8_t *p, size_t n);

/* Battery telemetry frame (FC -> RX -> handset): returns bytes written. */
size_t fc_crsf_build_battery(uint8_t out[CRSF_MAX_FRAME],
                             float volts, float amps,
                             uint32_t mah_used, uint8_t pct);

#ifdef __cplusplus
}
#endif
#endif /* FC_CRSF_H */
