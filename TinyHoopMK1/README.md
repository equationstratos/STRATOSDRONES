# Fr4n10-001 (TinyHoop MK1) — the programmable 2.5" FPV with swarm & show modes

The **TinyHoop MK1** is the first Stratos Drones model built for *drone-show*
work as much as for FPV: a 2.5" wide-X quad — ExpressLRS radio, analog 5.8 GHz
**or** DJI O4 Lite video, 2S-3S brushless — that is also **fully programmable**
(Python SDK), **position-holding** (optical flow + ToF, GPS-ready), and
**swarm-capable** over a dedicated **LoRa 868 MHz** ground link. No Wi-Fi
needed in the field: the PC talks to the fleet by radio.

Same open DNA as every other model: one repo, full code + CAD + firmware +
hardware + PCB, permissive licences, sim-first.

## Inspirations (credit where due)

- The **JeNo Pocket V2** frame by **WE are FPV**
  (https://www.printables.com/model/1704840-jeno-pocket-v2 — licence
  **CC-BY-4.0**): the wide-X 2.5" geometry, the 25.5 × 25.5 mm M2 main stack
  + 13 × 13 mm rear RX stack, the three bottom-plate personalities
  (Classic / X-Core / Tank), 3 mm bottom + 2 mm top/camera carbon plates,
  9 mm motor mounts (1203-1303 class), camera tilt 15-35°, O4-Lite-native
  camera bay. **The frame keeps their design** — per the user's brief. Two
  forms live here: the **genuine WE are FPV STEP** (CC-BY-4.0) in
  [`cad/frame_jeno/`](cad/frame_jeno/), which the 3-D viewer renders for full
  fidelity; and a **clean-room parametric OpenSCAD variant**
  ([`cad/frame.scad`](cad/frame.scad)) re-drawn from public specs and
  re-branded STRATOS, for printing/cutting the Stratos version. Attribution +
  licence in [`cad/frame_jeno/ATTRIBUTION.md`](cad/frame_jeno/ATTRIBUTION.md).
  Thank you WE are FPV — go download (and buy plates for) the original.
- The **drone-show pattern** (pre-uploaded time-stamped choreographies +
  one broadcast clock) and the **ExpressLRS + analog/O4 + BLHeli_S**
  outdoor micro ecosystem, as on fpv85/fpv2.

What we deliberately do differently: the flight controller stays **our
ESP32-P4 + C6 + `fc_core`** — one firmware family across every Stratos
model — now with a **mode manager** (see below) and a **LoRa fleet link**
instead of Wi-Fi for field programmability.

## The four flight modes

| Mode | What it does | Who commands |
|---|---|---|
| **MANUAL** | true FPV: acro or angle, DShot, failsafe cut | ELRS radio (CRSF) — and a PC driving an ELRS TX module also works |
| **STABILIZED** | position hold on flow+ToF (GPS later): hovers in place, flies figures, still steerable | radio sticks *or* PC over LoRa — both while stabilized |
| **PROGRAM** | Tello-style SDK verbs, mission scripts | Python (`stratospy`) over **LoRa** (Wi-Fi stays a lab bonus) |
| **SWARM** | time-synced choreography playback (drone-show formations) | pre-uploaded show + LoRa broadcast start/abort/clock |

Radio CH6 selects MANUAL/STABILIZED/SWARM when the radio link is live; the
SDK `mode` verb selects the rest; **CH5 disarm and CRSF failsafe always
win**. The safety pilot can grab any drone out of a show at any time.

## Positioning

| | Fr4n8-001 (fpv85) | **Fr4n10-001 (this)** |
|---|---|---|
| Class | 85 mm toothpick, printed plate | **2.5" wide-X, carbon (or printed proto)** |
| Wheelbase / props | 85 mm / 40 mm | **~115 mm `TUNE` / 63.5 mm (Gemfan 2520)** |
| Motors | 0802 ~14000KV | **1203-1303, ~8000KV (2S) / ~6000KV (3S)** |
| Battery | 2S 450 XT30 | **2S-3S 450-560 XT30** |
| Control | ELRS + Wi-Fi SDK | **ELRS + LoRa 868 SDK (no-Wi-Fi field link)** |
| FPV video | analog 5.8G | **analog 5.8G bay AND DJI O4 Lite support** |
| Position hold | none (drift accepted) | **flow + ToF restored; GPS connector** |
| Swarm | sim only | **LoRa TDMA fleet link + show executor** |
| AUW target | 67-80 g | **115-145 g `TUNE`** |
| Board | `hardware/pcb_fpv/` 32×32 | **`hardware/pcb_tinyhoop/` 30.5×30.5, 25.5 mount** |

## Target specifications (v0 charter)

- **Frame**: JeNo-Pocket-V2-style wide-X, bottom 3 mm (Classic / X-Core /
  Tank variants), top 2 mm, camera plates 2 mm — **DXF for carbon cutting**
  + **STL for a printable PLA-CF/PETG prototype**; TPU camera mount,
  antenna mounts, arm guards, rear bumper; STRATOS engraving.
- **Propulsion**: 4× 1203-1303 on Gemfan 2520 tri-blades, 2S-3S →
  T/W ≥ 2.5 at 130 g `TUNE`.
- **Electronics**: STRATOS TINYHOOP AIO — see
  [`../hardware/pcb_tinyhoop/`](../hardware/pcb_tinyhoop/): ESP32-P4 + C6,
  4× integrated ESC 15-20 A class, PMW3901 + VL53L1X down-facing, SX1262
  LoRa 868 (castellated module, **optional — leave unsoldered on a solo
  build**), GPS/compass connector, analog VTX bay, O4-Lite 5 V budget.
- **Radio**: any ExpressLRS RX on the CRSF socket (420 kbaud) — rear 13×13
  stack or the socket, both supported.
- **Video**: analog nano cam → 25-400 mW VTX (SmartAudio), **or** DJI O4
  Lite on the native frame mount.
- **Ground**: LoRa dongle = off-the-shelf ESP32+SX1262 board (Heltec LoRa32
  V3 / LilyGO T3S3) + [`../sdk/lora_dongle/`](../sdk/lora_dongle/) bridge;
  Python side in [`../sdk/python/`](../sdk/python/) (`stratospy.lora`,
  `stratospy.show`).
- **Firmware**: `fc_core` mode manager + show executor + CRSF parser + LoRa
  protocol **implemented and host-tested**; ESP-IDF `outputs_dshot.c`,
  `crsf_task.c`, `sx1262.c`, `lora_task.c` **implemented** (CI-compiled).

## Repository layout (this folder)

```
TinyHoopMK1/
  README.md            this charter
  DESIGN.md            geometry + modes + LoRa protocol + show format + weight budget
  ROADMAP.md           M0 -> M4
  cad/                 frame.scad -> stl/ (printable + viewer parts), dxf/ (carbon), preview/
  viz/                 browser viewer + PLAYGROUND simulator
  hardware/README.md   board pointer + RTF module BOM + ready-to-buy fallback
  firmware/README.md   shared-verbatim vs newly-implemented map
  sim/README.md        SDF parameter targets (Gazebo port = M3)
```

**See it in 3-D** — open [`viz/drone_viewer.html`](viz/) (self-contained;
`?playground=1` = the browser flight simulator).

## Status

**M0 — concept & scaffold (this commit).** Charter, clean-room CAD v0
(carbon DXF + printable STL), viewer + playground, TINYHOOP AIO board at M0,
mode manager / show executor / CRSF / LoRa protocol coded with host tests,
firmware tasks written (CI-compiled). **Not printed, not cut, not fabbed,
not flown — see the TUNE tags and `hardware/pcb_tinyhoop/KNOWN_GAPS.md`
before building.**
