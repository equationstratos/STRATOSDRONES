/* CRSF parser tests: CRC8 DVB-S2, channel unpacking, resync on garbage,
 * chunked input, battery telemetry frame.
 * SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <string.h>
#include "fc_core/fc_crsf.h"
#include "test_util.h"

/* pack 16 x 11-bit channels little-endian, like the RX does */
static void pack_channels(const uint16_t ch[16], uint8_t out[22])
{
    memset(out, 0, 22);
    int bit = 0;
    for (int i = 0; i < 16; i++) {
        uint32_t v = ch[i] & 0x7FF;
        int byte = bit >> 3, off = bit & 7;
        out[byte] |= (uint8_t)(v << off);
        out[byte + 1] |= (uint8_t)(v >> (8 - off));
        if (off > 5) out[byte + 2] |= (uint8_t)(v >> (16 - off));
        bit += 11;
    }
}

static size_t build_channels_frame(const uint16_t ch[16], uint8_t out[32])
{
    out[0] = CRSF_SYNC_FC;
    out[1] = 24;               /* type + 22 + crc */
    out[2] = CRSF_TYPE_CHANNELS;
    pack_channels(ch, &out[3]);
    out[25] = fc_crsf_crc8(&out[2], 23);
    return 26;
}

int main(void)
{
    fc_crsf_t c;
    fc_crsf_init(&c);

    /* defaults: centered sticks, throttle low */
    float norm[16];
    fc_crsf_norm(&c, norm);
    CHECK_NEAR(norm[0], 0.0f, 0.01);
    CHECK_NEAR(norm[2], -1.0f, 0.01);

    /* --- decode a clean frame --- */
    uint16_t ch[16];
    for (int i = 0; i < 16; i++) ch[i] = 992;
    ch[0] = 1811;   /* full right */
    ch[2] = 172;    /* throttle low */
    ch[4] = 1792;   /* armed */
    uint8_t fr[32];
    size_t n = build_channels_frame(ch, fr);
    CHECK(fc_crsf_input(&c, fr, n) == 1);
    CHECK(c.frames == 1);
    CHECK(c.fresh);
    CHECK(c.ch_raw[0] == 1811);
    CHECK(c.ch_raw[2] == 172);
    CHECK(c.ch_raw[4] == 1792);
    CHECK(c.ch_raw[7] == 992);
    fc_crsf_norm(&c, norm);
    CHECK_NEAR(norm[0], 1.0f, 0.01);
    CHECK_NEAR(norm[2], -1.0f, 0.01);
    CHECK_NEAR(norm[7], 0.0f, 0.01);
    CHECK(!c.fresh);

    /* --- resync through garbage + byte-by-byte input --- */
    uint8_t junk[7] = {0x00, 0xFF, 0x12, 0xC8, 0x01, 0xEE, 0x55};
    fc_crsf_input(&c, junk, sizeof(junk));
    ch[1] = 500;
    n = build_channels_frame(ch, fr);
    int got = 0;
    for (size_t i = 0; i < n; i++)
        got += fc_crsf_input(&c, &fr[i], 1);
    CHECK(got == 1);
    CHECK(c.ch_raw[1] == 500);

    /* --- corrupted CRC is counted and dropped --- */
    n = build_channels_frame(ch, fr);
    fr[10] ^= 0x40;
    uint32_t frames_before = c.frames;
    CHECK(fc_crsf_input(&c, fr, n) == 0);
    CHECK(c.frames == frames_before);
    CHECK(c.crc_errors == 1);

    /* --- two frames in one buffer --- */
    uint8_t two[64];
    ch[1] = 992;
    size_t n1 = build_channels_frame(ch, two);
    ch[1] = 1200;
    size_t n2 = build_channels_frame(ch, two + n1);
    CHECK(fc_crsf_input(&c, two, n1 + n2) == 2);
    CHECK(c.ch_raw[1] == 1200);

    /* --- link statistics frame --- */
    uint8_t lk[16];
    lk[0] = CRSF_SYNC_FC;
    lk[1] = 12;                /* type + 10 + crc */
    lk[2] = CRSF_TYPE_LINK;
    uint8_t pl[10] = {70, 0, 95, 0, 0, 3, 0, 0, 0, 0}; /* rssi 70 -> -70 dBm, lq 95 */
    memcpy(&lk[3], pl, 10);
    lk[13] = fc_crsf_crc8(&lk[2], 11);
    fc_crsf_input(&c, lk, 14);
    CHECK(c.rssi_dbm == -70);
    CHECK(c.lq_pct == 95);

    /* --- battery telemetry builder round-trips its own CRC --- */
    uint8_t bat[CRSF_MAX_FRAME];
    size_t bn = fc_crsf_build_battery(bat, 7.4f, 3.2f, 250, 87);
    CHECK(bn == 12);
    CHECK(bat[0] == CRSF_SYNC_FC);
    CHECK(bat[1] == 10);
    CHECK(bat[2] == CRSF_TYPE_BATTERY);
    CHECK(bat[3] == 0 && bat[4] == 74);      /* 7.4 V -> 74 dV big-endian */
    CHECK(bat[10] == 87);
    CHECK(fc_crsf_crc8(&bat[2], 9) == bat[11]);

    TEST_END();
}
