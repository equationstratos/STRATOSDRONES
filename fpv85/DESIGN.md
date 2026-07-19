# Fr4n8-001 (fpv85) — design notes

## 1. Outdoor first: what changes vs the indoor models

**Decision: radio + analog video + brushless, keep the Stratos brain.**
Outdoors, Wi-Fi control (latency spikes, ~50-100 m realistic) and brushed
8520s (no wind margin) don't cut it. The proven outdoor stack is
**ExpressLRS (CRSF) + analog 5.8 GHz + brushless 2S** — all off-the-shelf,
all cheap, all long-range. We keep the ESP32-P4 + C6 + `fc_core` brain, so
the drone stays **programmable** (Tello-SDK verbs over Wi-Fi, Python SDK,
missions) *on top of* manual FPV flying.

Position hold: the indoor ToF+flow pair is removed (useless over grass at
speed). Altitude hold = IMU + SPL06 baro; horizontal position drifts —
normal for an FPV quad, flown in acro/angle. GPS is the future outdoor
answer (free UART + I2C remain); out of scope at M0.

## 2. Geometry (from the owner's reference, clean-room)

| Quantity | Value |
|---|---|
| wheelbase | **65 mm** (X layout, motors at ±22.98/±22.98) |
| props | **40 mm (1.6") tri-blade** |
| overall footprint | 0.707·65 + 40 ≈ **86 mm** (ref photo: 84 × 83) |
| height | plate 3 + posts 3.2 + board 1.6 + canopy 17 ≈ 25, **~32 with antenna** (ref: 32) |
| prop plane | z ≈ 13 above plate — clears arms/board/canopy legs; canopy shell is octagonal so its corners stay inside the prop-free centre zone (diagonal half-width ≤ 12.5) |
| motor mount | 3× M1.4 on Ø6.6 (0802 class) `TUNE` |
| AIO mount | 25.5 × 25.5 M2 posts; **canopy legs screw on the same stack** (classic whoop sandwich: screw → canopy leg → board → post) |

## 3. Weight budget (targets, `TUNE`)

| Item | g |
|---|---|
| frame plate + canopy (printed) | 14-18 |
| 4× 0802 14000KV + 40 mm props | 14-16 |
| STRATOS FPV AIO (32×32, populated) | 6-8 |
| ELRS RX + antenna | 1-2 |
| nano cam + VTX (25-400 mW) + antenna | 6-9 |
| 2S 450 mAh + XT30 | 24-28 |
| **AUW** | **65-78** |

0802@2S on 40 mm tri-blades ≈ 35-45 g/motor → **T/W ≈ 2.0-2.6**. Enough for
brisk outdoor cruising; the 2" (fpv2) is the freestyle one.

## 4. The analog FPV chain (zero firmware)

nano cam (5V) → VIDEO net → VTX bay (5V, SmartAudio on GPIO6). The whole
video path is copper on the AIO — works with the ESP32 held in reset. The
P4's own MIPI camera (J4, optional) stays the *digital* eye for the Wi-Fi
H.264 app link; both can coexist (weight decides).

## 5. Firmware — **SPECIFIED, NOT IMPLEMENTED** (deploy-verb precedent)

`fc_core` needs **zero changes**: it already outputs 4 duty floats
(`fc_core_get_motors`, mixer in `fc_control.c:100-126`) and has a manual
stick path (`fc_cmd_rc`, `fc_commander.c:130-140`) fed today by the Tello
`rc` verb (`fc_sdk.c:117-124`). Two platform pieces are new:

### 5a. `outputs_dshot.c` — DShot600 on the P4 RMT

| Layer | File | Change |
|---|---|---|
| Driver | `firmware/components/drivers/outputs_dshot.c` (new) | 4× RMT TX channels on `PIN_MOTOR_1..4` (GPIO45-48 — **same pins as brushed**), DShot600 frames (16 bit + CRC), 8 kHz refresh, arming = 300 zero-throttle frames |
| Wiring | `flight_task.c:128-130` | call `dshot_write(duty)` instead of `motors_write(duty)` (compile-time board select on `board_pinmap_fpv.h`) |
| Fallback | — | BLHeli_S ESCs also take OneShot/PWM: first bench spin can use the existing LEDC driver at 1-2 kHz |

### 5b. `crsf_task.c` — ExpressLRS input

| Layer | File | Change |
|---|---|---|
| UART | new task | UART on GPIO4 (TX) / GPIO5 (RX), **420 kbaud 8N1**, CRSF framing (sync 0xC8, len, type, payload, CRC8-DVB-S2) |
| Channels | type 0x16 (RC_CHANNELS_PACKED) | 16× 11-bit → normalise 172..1811 → −100..+100 → `fc_cmd_rc(lr, fb, ud, yaw)` at each frame (~150 Hz) |
| Arming | CH5 (AUX1) high → `takeoff`-less direct arm (acro) or angle mode CH6 | maps through `fc_commander` states |
| **Failsafe** | no valid frame for 300 ms | `fc_cmd_emergency()` (motors cut) — non-negotiable outdoors |
| Telemetry (later) | CRSF downlink | battery voltage from `VBAT_SENSE` (/3 divider) |

Wi-Fi SDK verbs keep working in parallel (the `rc` verb writes the same
`fc_cmdr_t.rc[4]`); CRSF has priority when frames are live.

## 6. What stays honest

M0: **nothing here has been printed, fabbed or flown.** The ESC stage and
the new-part pin maps are `VERIFY` (fab-blocking) in
[`../hardware/pcb_fpv/KNOWN_GAPS.md`](../hardware/pcb_fpv/KNOWN_GAPS.md).
Thrust/KV numbers are catalogue-class estimates tagged `TUNE`. The playground
in `viz/` is a kinematic browser sim, not a dynamics model.

## Sources

- https://www.expresslrs.org/ (CRSF wiring, 420 kbaud, channel packing)
- https://github.com/bird-sanctuary/bluejay (BLHeli_S-compatible ESC firmware, EFM8)
- https://www.espressif.com/sites/default/files/documentation/esp32-p4_datasheet_en.pdf (RMT, UART, GPIO matrix)
- Fortior FD6288 / AOS AO3400A / Diodes AP63203-AP63205 datasheets (pin maps to VERIFY)
