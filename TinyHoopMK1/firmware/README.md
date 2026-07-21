# TinyHoop MK1 — firmware map

The TinyHoop MK1 runs the **same** ESP-IDF firmware tree as every Stratos
model ([`../../firmware/`](../../firmware/)). Nothing is forked — the board
is selected at build time and the new pieces sit behind feature flags in
[`firmware/components/board/include/board_select.h`](../../firmware/components/board/include/board_select.h).

## Build for this board

```bash
cd firmware
idf.py set-target esp32p4
idf.py build -DCMAKE_C_FLAGS="-DSTRATOS_BOARD_TINYHOOP"
```

`STRATOS_BOARD_TINYHOOP` switches the pinmap to
[`board_pinmap_tinyhoop.h`](../../firmware/components/board/include/board_pinmap_tinyhoop.h)
and turns on `BOARD_HAS_DSHOT` / `BOARD_HAS_CRSF` / `BOARD_HAS_LORA`. Without
it you get the default Fr4n7 build (brushed + Wi-Fi), unchanged.

## What is shared verbatim

The entire flight core is reused as-is: `fc_core` (now with the mode
manager, show executor, CRSF parser and LoRa protocol — all host-tested),
`fc_sdk`, the IMU/baro/flow/ToF drivers, the Wi-Fi + video path. The
`flight_task` loop is the same; it only gains a board-selected motor write
(`dshot_write` vs `motors_write`), a CRSF channel drain, and a 10 Hz
telemetry snapshot for the LoRa task.

## What is new (implemented this milestone)

| File | Role |
|---|---|
| `firmware/components/drivers/outputs_dshot.c` | DShot600 ×4 on the P4 RMT (GPIO45-48). At 1 kHz the zero-throttle stream is the BLHeli_S/Bluejay arm sequence. LEDC (`outputs.c`) stays the bench fallback. |
| `firmware/components/drivers/sx1262.c` | SX1262 SPI driver, EU868 fixed profile (869.525 MHz, SF7/BW250/CR4:5). Guarded by `BOARD_HAS_LORA`. |
| `firmware/main/crsf_task.c` | ELRS RX on UART1 @420 kbaud → `fc_crsf` → latest-frame queue → `fc_input_crsf()`. The 300 ms failsafe lives in `fc_mode.c`. |
| `firmware/main/lora_task.c` | SX1262 ↔ `fc_lorap` ↔ SDK verbs. Binary frames (TIME_BEACON, SWARM_START/ABORT, SHOW_CHUNK, CMD_LINE) become the same ASCII lines the Wi-Fi path uses — one command pipeline everywhere. Sends TELEM at 2 Hz and relays replies as RESP_LINE when Wi-Fi has no client. |

## Honesty (M0)

This code **compiles under ESP-IDF in CI but has not run on hardware.** The
RMT bit timings, the SX1262 command sequence and PA config, and the CRSF
UART pin mapping are all `VERIFY` — bench-check them during M2 bring-up
(see [`../ROADMAP.md`](../ROADMAP.md) and
[`../../hardware/pcb_tinyhoop/KNOWN_GAPS.md`](../../hardware/pcb_tinyhoop/KNOWN_GAPS.md)).
The portable logic underneath (`fc_crsf`, `fc_lorap`, mode manager, show
executor) **is** host-tested — see `fc_core/test/test_crsf.c`,
`test_lorap.c`, `test_modes.c`, `test_show.c`.
