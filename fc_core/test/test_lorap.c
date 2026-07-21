/* LoRa fleet-protocol tests: CRC16 anchor, encode/decode round-trips,
 * corruption rejection, payload packing — plus the golden header/payload
 * bytes mirrored by stratospy/lora.py (keep both in sync!).
 * SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <string.h>
#include "fc_core/fc_lorap.h"
#include "test_util.h"

int main(void)
{
    /* --- CRC16-CCITT anchor: the standard "123456789" check value --- */
    CHECK(lorap_crc16((const uint8_t *)"123456789", 9) == 0x29B1);

    /* --- CMD_LINE round-trip --- */
    lorap_frame_t f, g;
    memset(&f, 0, sizeof(f));
    f.type = LORAP_CMD_LINE;
    f.swarm_id = 7;
    f.src = LORAP_ADDR_GROUND;
    f.dst = 3;
    f.seq = 42;
    const char *cmd = "go 100 0 50 60";
    f.len = (uint8_t)strlen(cmd);
    memcpy(f.payload, cmd, f.len);
    uint8_t buf[LORAP_MAX_FRAME];
    size_t n = lorap_encode(buf, &f);
    CHECK(n == (size_t)LORAP_HDR_LEN + f.len + 2);
    CHECK(lorap_decode(buf, n, &g));
    CHECK(g.type == LORAP_CMD_LINE);
    CHECK(g.swarm_id == 7 && g.src == 0 && g.dst == 3 && g.seq == 42);
    CHECK(g.len == f.len && memcmp(g.payload, cmd, f.len) == 0);

    /* --- golden header bytes (mirrored in stratospy/lora.py tests) --- */
    CHECK(buf[0] == 0x53);                     /* 'S' */
    CHECK(buf[1] == 0x12);                     /* ver 1, type CMD_LINE=2 */
    CHECK(buf[2] == 0x07 && buf[3] == 0x00 && buf[4] == 0x03 && buf[5] == 0x2A);
    CHECK(buf[6] == f.len);

    /* --- corruption: flip one byte anywhere -> reject --- */
    for (size_t i = 0; i < n; i++) {
        uint8_t save = buf[i];
        buf[i] ^= 0x5A;
        CHECK(!lorap_decode(buf, n, &g));
        buf[i] = save;
    }
    CHECK(lorap_decode(buf, n, &g));           /* restored: fine again */
    CHECK(!lorap_decode(buf, n - 1, &g));      /* truncated */

    /* --- broadcast + empty payload (SWARM_ABORT) --- */
    memset(&f, 0, sizeof(f));
    f.type = LORAP_SWARM_ABORT;
    f.src = LORAP_ADDR_GROUND;
    f.dst = LORAP_BROADCAST;
    n = lorap_encode(buf, &f);
    CHECK(n == LORAP_HDR_LEN + 2);
    CHECK(lorap_decode(buf, n, &g));
    CHECK(g.dst == LORAP_BROADCAST && g.len == 0);

    /* --- oversized payload refused --- */
    f.len = LORAP_MAX_PAYLOAD + 1;
    CHECK(lorap_encode(buf, &f) == 0);

    /* --- telemetry pack/unpack, negative values included --- */
    lorap_telem_t t = {
        .state = 2, .mode = 3,
        .x_cm = 123, .y_cm = -45, .z_cm = 180, .yaw_deg = -90,
        .vbat_mv = 7412, .bat_pct = 87, .rssi_dbm = -70, .flags = 1,
    };
    uint8_t pl[LORAP_TELEM_LEN];
    lorap_pack_telem(pl, &t);
    /* golden payload bytes (little-endian; mirrored in python) */
    const uint8_t expect[LORAP_TELEM_LEN] = {
        0x02, 0x03, 0x7B, 0x00, 0xD3, 0xFF, 0xB4, 0x00,
        0xA6, 0xFF, 0xF4, 0x1C, 0x57, 0xC6,
    };
    CHECK(memcmp(pl, expect, LORAP_TELEM_LEN) == 0);
    lorap_telem_t u;
    lorap_unpack_telem(pl, &u);
    CHECK(u.state == 2 && u.mode == 3);
    CHECK(u.x_cm == 123 && u.y_cm == -45 && u.z_cm == 180);
    CHECK(u.yaw_deg == -90);
    CHECK(u.vbat_mv == 7412 && u.bat_pct == 87);
    CHECK(u.rssi_dbm == -70 && u.flags == 1);

    /* --- u64 helper (time beacons) --- */
    uint8_t b8[8];
    lorap_pack_u64(b8, 1752998400123ULL);
    CHECK(lorap_unpack_u64(b8) == 1752998400123ULL);
    lorap_pack_u64(b8, 0);
    CHECK(lorap_unpack_u64(b8) == 0);

    /* --- chunk capacity sanity --- */
    CHECK(LORAP_KEYS_PER_CHUNK == 4);
    CHECK(LORAP_MAX_PAYLOAD == 55);

    TEST_END();
}
