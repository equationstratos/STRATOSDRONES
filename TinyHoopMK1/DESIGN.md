# Fr4n10-001 (TinyHoop MK1) — design notes

## 1. Why this model

The fpv85/fpv2 pair proved the outdoor-FPV recipe (ELRS + analog + brushless)
but gave up two things: **position hold** (flow/ToF removed) and a
**no-Wi-Fi PC link**. The TinyHoop MK1 brings both back, because its job is
different: it must fly **drone-show style** — hover in place, hold a slot in
a formation, execute a pre-programmed figure in sync with its siblings —
while staying a real FPV quad a pilot can seize at any moment.

Decisions:

- **Frame = JeNo Pocket V2 design, kept** (user brief), as a clean-room
  parametric OpenSCAD re-creation (CC-BY-4.0 attribution in the README);
  carbon is the real material (DXF), print is the prototype path (STL).
- **Piloting = ExpressLRS** (CRSF, 420 kbaud). Non-negotiable latency +
  failsafe. A PC can pilot "through the radio" by driving an ELRS TX module
  with CRSF over USB — same link, no Wi-Fi.
- **Fleet link = LoRa SX1262, EU868**, *not* Wi-Fi, *not* ELRS: ELRS binds
  1 TX ↔ 1 RX and has no fleet addressing; the show needs broadcast + a
  shared clock + per-drone telemetry. LoRa gives km-class range at the low
  data rates a *pre-uploaded* show actually needs.
- **Stabilized = PMW3901 + VL53L1X** (the proven Fr4n7 pair, footprints
  already verified on `hardware/pcb/`), GPS/compass connector reserved for
  outdoor absolute positioning (M4).

## 2. Geometry (from WE are FPV's published numbers, clean-room)

| Quantity | Value |
|---|---|
| props | **2.5" (Ø63.5 mm) — Gemfan 2520 tri-blade** (Avan Rush option) |
| wheelbase | **~115 mm `TUNE`** (wide-X: front track wider than rear; exact plate outlines are not published as numbers — dry-fit before cutting carbon, M1) |
| plates | bottom **3 mm** carbon (Classic / X-Core / Tank), top **2 mm**, camera side plates **2 mm**; printed proto: same outlines at 4 mm / 3 mm `TUNE` |
| main stack | **25.5 × 25.5 mm M2** (holes Ø2.3), standoff heights 14/16/18/20 mm |
| rear stack | **13 × 13 mm** (RX shelf) |
| motor mount | **3× M2 on Ø9.0** (1203-1303 class) |
| camera | O4 Lite native bay **or** 14 mm nano cam, tilt **15-35°** (5° steps) |
| battery | 2S-3S 450-560 mAh XT30 on top, strap slots |

## 3. Weight budget (targets, `TUNE`)

| Item | g |
|---|---|
| frame (carbon, screws) | 25-30 |
| TPU parts | 6-8 |
| 4× 1203 + Gemfan 2520 | 34-38 |
| STRATOS TINYHOOP AIO (populated, with LoRa module) | 9-11 |
| ELRS RX + antenna | 1-2 |
| analog nano cam + VTX + antenna | 6-9 *(or O4 Lite ≈ 9)* |
| 2S 450 / 3S 550 XT30 | 28 / 45 |
| **AUW** | **115-145** |

1203@2S-3S on 2520 tri-blades ≈ 80-120 g/motor `TUNE` → **T/W ≈ 2.5-3.5**.

## 4. The mode manager (fc_core, implemented)

Four modes in `fc_core/src/fc_mode.c`, arbitrated every commander tick:

```
MANUAL      CRSF sticks -> acro rates (or angle, CH7 sub-mode) -> mixer direct
STABILIZED  pos/vel loops + flow/ToF; sticks or SDK `rc` = velocity setpoints
PROGRAM     Tello-SDK verbs (takeoff/land/go/rc/...) — today's default path
SWARM       fc_show keyframe playback -> position setpoints, clock-synced
```

Arbitration rules (in priority order):

1. **CRSF failsafe** (no valid frame 300 ms while radio was live): MANUAL →
   emergency motor cut (no hold to fall back on — the FPV convention);
   radio-owned STABILIZED → auto-land. Non-negotiable outdoors.
2. **CH5 low** (disarm) while the radio is live → motors cut + IDLE, always.
3. **CH6** (3-pos) while the radio is live: **high = MANUAL** (safety pilot
   seizes the drone), **mid = STABILIZED**, **low = defer to the SDK-requested
   mode**. CH7 picks the MANUAL sub-mode (low = angle, high = acro).
4. SDK `mode` verb selects PROGRAM/STABILIZED/SWARM (MANUAL is refused
   without a live radio); a live radio's CH6 high/mid outranks it.
5. Default (no radio ever seen, no verb) = **PROGRAM** ≡ the exact behavior
   every existing model, test and sim has today.

MANUAL bypasses the position/velocity loops entirely (rate/angle inner loops
+ throttle direct); STABILIZED/PROGRAM/SWARM all run the existing
position-leash plumbing (`run_rc` / `run_goto`) fed by different sources.

## 5. Show format + executor (implemented)

A show is a per-drone list of time-stamped keyframes:

```
{t_ms, x_cm, y_cm, z_cm, yaw_deg}     (≤ 256 keyframes on-board)
```

`fc_show.c` interpolates between keyframes with cosine easing, emitting
position setpoints + velocity feed-forward at the 100 Hz commander tick.
The clock is `local_time + beacon_offset`; `TIME_BEACON` frames (1 Hz from
the dongle) keep the fleet within a few ms. `SWARM_START t0` arms playback
at a common T0; `SWARM_ABORT` (or stick input / CH6) drops to STABILIZED
hold. Figures (circle, spiral, line, polygon, wave) can also be generated
*on-board* by `fc_figures.c` via the `figure` verb — no upload needed for
single-drone practice.

The Python side (`stratospy.show`) compiles JSON choreographies (or the
figure DSL) into per-drone keyframe sets, enforces **minimum separation and
vmax** across the fleet, previews in Gazebo (same verbs over UDP), then
uploads over LoRa (`SHOW_CHUNK` + ACK).

SDK verbs (in `fc_sdk.c`, work over Wi-Fi UDP, SITL, Gazebo *and* LoRa —
the SDK layer is transport-free):

```
mode ?  |  mode manual|stab|prog|swarm
show clear | show key <t_ms> <x> <y> <z> <yaw> | show count? | show start <t0_ms> | show stop
figure circle <r_cm> <period_ms> <turns> | figure spiral ... | figure line ... | figure poly ... | figure wave ...
timesync <epoch_ms>
```

## 6. LoRa fleet protocol (implemented: `fc_lorap.c` + `stratospy.lora`)

- **PHY**: SX1262, **EU868**, default channel **869.525 MHz** (10 %
  duty-cycle sub-band, up to 27 dBm — the dongle is the TX-heavy side and
  needs the duty headroom), SF7 / BW250 / CR4:5 ≈ 11 kbps. All params
  compile-time + `param` verbs.
- **Frame** (max 64 B):
  `'S' | ver:4 type:4 | swarm_id | src | dst | seq | len | payload ≤55 | crc16-ccitt`
  — `dst 0xFF` = broadcast, drone ids 1-250, dongle = 0.
- **Types**: `CMD_LINE` (one SDK ASCII line, ACKed) · `RESP_LINE` ·
  `TELEM` (14 B binary: state, mode, x/y/z cm, yaw, vbat, bat %, rssi,
  show flag — 2 Hz per drone, TDMA slot = `drone_id × 40 ms` after each
  beacon) · `SHOW_CHUNK` (4 keyframes of 12 B per frame, ACK + retry) ·
  `TIME_BEACON` (1 Hz: epoch ms u64 [+ T0 u64]) ·
  `SWARM_START` / `SWARM_ABORT` (broadcast, repeated ×3) · `ACK`/`NAK`.
- **Honesty**: LoRa is the *command/telemetry/choreography* channel, **not a
  piloting channel** — piloting stays on ELRS; shows are pre-uploaded so the
  air is mostly beacons. Practical ceiling ≈ **6 drones per channel** at
  2 Hz telemetry within EU duty limits; document per-fleet channel plans
  beyond that.
- Framing/CRC/parse is pure C (`fc_lorap.c`, host-tested); the Python mirror
  (`stratospy/lora.py`) is validated against the **same golden-frames
  fixture** committed in `fc_core/test/`.

## 7. Firmware pieces (implemented, CI-compiled)

| Piece | File | Notes |
|---|---|---|
| DShot600 ×4 | `firmware/components/drivers/outputs_dshot.c` | P4 RMT TX on the motor pins, 16-bit frames + CRC, 8 kHz refresh, 300 zero-throttle frames to arm; LEDC/PWM stays the bench fallback |
| ELRS input | `firmware/main/crsf_task.c` | UART 420 kbaud 8N1, bytes → `fc_crsf` parser → channels queue → `fc_input_crsf()`; **300 ms failsafe → `fc_cmd_emergency()`**; CH5 arm, CH6 mode |
| LoRa radio | `firmware/components/drivers/sx1262.c` | SPI + CS/BUSY/DIO1/RST, EU868 config, IRQ RX |
| Fleet link | `firmware/main/lora_task.c` | `fc_lorap` frames ↔ SDK command queue; TELEM TDMA slot; TIME_BEACON → `fc_show` clock |

The analog FPV chain stays zero-firmware (cam → VTX is copper); the O4 Lite
is its own closed ecosystem (goggles link) — the AIO only feeds it 5 V/2 A
(`KNOWN_GAPS`: budget) or VBAT per DJI's 2S-3S allowance.

## 8. What stays honest

M0: **nothing here has been printed, cut, fabbed or flown.** ESP-IDF code is
CI-compiled, not hardware-tested; the ESC stage, SX1262 pad map and 5 V
budget are `VERIFY` (fab-blocking) in
[`../hardware/pcb_tinyhoop/KNOWN_GAPS.md`](../hardware/pcb_tinyhoop/KNOWN_GAPS.md).
Thrust/KV numbers are catalogue-class estimates tagged `TUNE`. The JeNo
plate outlines are re-drawn from public facts, not measured — dry-fit a
printed plate before cutting carbon.

## Sources

- https://www.printables.com/model/1704840-jeno-pocket-v2 (JeNo Pocket V2,
  WE are FPV, CC-BY-4.0 — 2.5", 25.5×25.5 + 13×13 stacks, 3/2 mm carbon,
  9 mm mounts, 1203-1303, O4-Lite bay, tilt 15-35° — design reference,
  clean-room re-creation)
- https://www.expresslrs.org/ (CRSF wiring, 420 kbaud, channel packing)
- Semtech SX1261/2 datasheet DS.SX1261-2.W.APP (SPI command set, IRQs)
- ETSI EN 300 220-2 (EU 863-870 MHz duty-cycle sub-bands)
- https://github.com/bird-sanctuary/bluejay (ESC firmware, EFM8)
- ESP32-P4 TRM (RMT, UART, GPIO matrix)
