/* CRSF byte-stream parser + telemetry builder. See fc_crsf.h.
 * Wire format reference: the public CRSF protocol description
 * (github.com/crsf-wg/crsf) and the ExpressLRS docs.
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "fc_core/fc_crsf.h"

uint8_t fc_crsf_crc8(const uint8_t *p, size_t n)
{
    uint8_t crc = 0;
    for (size_t i = 0; i < n; i++) {
        crc ^= p[i];
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0xD5) : (uint8_t)(crc << 1);
    }
    return crc;
}

void fc_crsf_init(fc_crsf_t *c)
{
    memset(c, 0, sizeof(*c));
    for (int i = 0; i < 16; i++) c->ch_raw[i] = 992; /* centers */
    c->ch_raw[2] = 172;                              /* throttle low */
}

static void decode_channels(fc_crsf_t *c, const uint8_t *pl)
{
    uint32_t bits = 0;
    int nbits = 0, ch = 0;
    for (int i = 0; i < 22 && ch < 16; i++) {
        bits |= (uint32_t)pl[i] << nbits;
        nbits += 8;
        while (nbits >= 11 && ch < 16) {
            c->ch_raw[ch++] = (uint16_t)(bits & 0x7FF);
            bits >>= 11;
            nbits -= 11;
        }
    }
    c->fresh = true;
    c->frames++;
}

static void frame_complete(fc_crsf_t *c)
{
    uint8_t len = c->buf[1];                 /* type + payload + crc */
    const uint8_t *body = &c->buf[2];        /* type.. */
    if (fc_crsf_crc8(body, (size_t)len - 1) != c->buf[2 + len - 1]) {
        c->crc_errors++;
        return;
    }
    uint8_t type = c->buf[2];
    const uint8_t *pl = &c->buf[3];
    if (type == CRSF_TYPE_CHANNELS && len == 24) {
        decode_channels(c, pl);
    } else if (type == CRSF_TYPE_LINK && len >= 12) {
        c->rssi_dbm = (int8_t)(-(int)pl[0]); /* uplink RSSI 1, dBm * -1 */
        c->lq_pct = pl[2];
    }
}

int fc_crsf_input(fc_crsf_t *c, const uint8_t *data, size_t n)
{
    uint32_t before = c->frames;
    for (size_t i = 0; i < n; i++) {
        uint8_t byte = data[i];
        if (c->pos == 0) {
            if (byte != CRSF_SYNC_FC) continue;      /* hunt for sync */
            c->buf[c->pos++] = byte;
        } else if (c->pos == 1) {
            if (byte < 2 || byte > CRSF_MAX_FRAME - 2) { c->pos = 0; continue; }
            c->buf[c->pos++] = byte;
        } else {
            c->buf[c->pos++] = byte;
            if (c->pos == c->buf[1] + 2) {           /* addr + len + body */
                frame_complete(c);
                c->pos = 0;
            }
        }
    }
    return (int)(c->frames - before);
}

void fc_crsf_norm(fc_crsf_t *c, float out[16])
{
    for (int i = 0; i < 16; i++) {
        float v = ((float)c->ch_raw[i] - 992.0f) / 819.5f;
        out[i] = v < -1.0f ? -1.0f : (v > 1.0f ? 1.0f : v);
    }
    c->fresh = false;
}

size_t fc_crsf_build_battery(uint8_t out[CRSF_MAX_FRAME],
                             float volts, float amps,
                             uint32_t mah_used, uint8_t pct)
{
    uint16_t dv = (uint16_t)(volts * 10.0f + 0.5f);  /* deci-volts, BE */
    uint16_t da = (uint16_t)(amps * 10.0f + 0.5f);
    if (mah_used > 0xFFFFFF) mah_used = 0xFFFFFF;
    uint8_t *p = out;
    *p++ = CRSF_SYNC_FC;
    *p++ = 10;                                       /* type + 8 + crc */
    *p++ = CRSF_TYPE_BATTERY;
    *p++ = (uint8_t)(dv >> 8); *p++ = (uint8_t)dv;
    *p++ = (uint8_t)(da >> 8); *p++ = (uint8_t)da;
    *p++ = (uint8_t)(mah_used >> 16);
    *p++ = (uint8_t)(mah_used >> 8);
    *p++ = (uint8_t)mah_used;
    *p++ = pct;
    *p = fc_crsf_crc8(&out[2], 9);
    return 12;
}
