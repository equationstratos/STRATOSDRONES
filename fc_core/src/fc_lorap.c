/* STRATOS LoRa fleet protocol: framing, CRC, payload packing.
 * Byte-for-byte mirrored by stratospy/lora.py — keep the golden fixture in
 * test_lorap.c in sync with any change here.
 * SPDX-License-Identifier: MIT */
#include <string.h>
#include "fc_core/fc_lorap.h"

uint16_t lorap_crc16(const uint8_t *p, size_t n)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < n; i++) {
        crc ^= (uint16_t)p[i] << 8;
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021)
                                 : (uint16_t)(crc << 1);
    }
    return crc;
}

size_t lorap_encode(uint8_t out[LORAP_MAX_FRAME], const lorap_frame_t *f)
{
    if (f->len > LORAP_MAX_PAYLOAD || f->type > 0x0F) return 0;
    out[0] = LORAP_MAGIC;
    out[1] = (uint8_t)((LORAP_VERSION << 4) | f->type);
    out[2] = f->swarm_id;
    out[3] = f->src;
    out[4] = f->dst;
    out[5] = f->seq;
    out[6] = f->len;
    memcpy(&out[7], f->payload, f->len);
    uint16_t crc = lorap_crc16(out, (size_t)LORAP_HDR_LEN + f->len);
    out[7 + f->len] = (uint8_t)(crc >> 8);
    out[8 + f->len] = (uint8_t)crc;
    return (size_t)LORAP_HDR_LEN + f->len + 2;
}

bool lorap_decode(const uint8_t *in, size_t n, lorap_frame_t *f)
{
    if (n < LORAP_HDR_LEN + 2 || n > LORAP_MAX_FRAME) return false;
    if (in[0] != LORAP_MAGIC) return false;
    if ((in[1] >> 4) != LORAP_VERSION) return false;
    uint8_t len = in[6];
    if (len > LORAP_MAX_PAYLOAD || (size_t)LORAP_HDR_LEN + len + 2 != n) return false;
    uint16_t crc = ((uint16_t)in[7 + len] << 8) | in[8 + len];
    if (crc != lorap_crc16(in, (size_t)LORAP_HDR_LEN + len)) return false;
    f->type = in[1] & 0x0F;
    f->swarm_id = in[2];
    f->src = in[3];
    f->dst = in[4];
    f->seq = in[5];
    f->len = len;
    memcpy(f->payload, &in[7], len);
    return true;
}

static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }

void lorap_pack_telem(uint8_t payload[LORAP_TELEM_LEN], const lorap_telem_t *t)
{
    payload[0] = t->state;
    payload[1] = t->mode;
    put16(&payload[2], (uint16_t)t->x_cm);
    put16(&payload[4], (uint16_t)t->y_cm);
    put16(&payload[6], (uint16_t)t->z_cm);
    put16(&payload[8], (uint16_t)t->yaw_deg);
    put16(&payload[10], t->vbat_mv);
    payload[12] = t->bat_pct;
    /* rssi travels as a 7-bit negative magnitude (0..-127 dBm) */
    int mag = t->rssi_dbm <= 0 ? -t->rssi_dbm : 0;
    if (mag > 127) mag = 127;
    payload[13] = (uint8_t)(mag | ((t->flags & 1) << 7));
}

void lorap_unpack_telem(const uint8_t payload[LORAP_TELEM_LEN], lorap_telem_t *t)
{
    t->state = payload[0];
    t->mode = payload[1];
    t->x_cm = (int16_t)get16(&payload[2]);
    t->y_cm = (int16_t)get16(&payload[4]);
    t->z_cm = (int16_t)get16(&payload[6]);
    t->yaw_deg = (int16_t)get16(&payload[8]);
    t->vbat_mv = get16(&payload[10]);
    t->bat_pct = payload[12];
    /* rssi is stored as a 7-bit negative magnitude */
    t->rssi_dbm = (int8_t)-(payload[13] & 0x7F);
    t->flags = (payload[13] >> 7) & 1;
}

void lorap_pack_u64(uint8_t out[8], uint64_t v)
{
    for (int i = 0; i < 8; i++) out[i] = (uint8_t)(v >> (8 * i));
}

uint64_t lorap_unpack_u64(const uint8_t in[8])
{
    uint64_t v = 0;
    for (int i = 7; i >= 0; i--) v = (v << 8) | in[i];
    return v;
}
