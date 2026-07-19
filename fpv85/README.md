# Fr4n8-001 (fpv85) — the outdoor micro-FPV (85 mm class, 2S brushless)

The first **outdoor** Stratos Drones model: a true FPV micro — radio control
(ExpressLRS), analog 5.8 GHz video, brushless 2S — built on the exact same
open DNA as the Fr4n7-001: one repo, full code + CAD + firmware + hardware +
PCB, permissive licences, sim-first. Its 2" big sibling is
[`../fpv2/`](../fpv2/) (Fr4n9-001) — **same design language, same shared
AIO board**, two sizes.

## Inspirations (credit where due)

- The owner's reference photos of an **"Eagle-class" 84 × 83 × 32 mm micro
  FPV** (overall footprint, H≈32 with canopy, and the **2S 14000KV**
  motor class) and of a **white side-plate toothpick canopy** — used as
  *visual/measurement references only*; every line of geometry here is our
  own parametric OpenSCAD (clean-room, like the Avata/Fr4n6 case).
- The **whoop-AIO stack convention** (25.5 × 25.5 M2 pattern, canopy screwed
  on the same stack) and the open **BLHeli_S / Bluejay + ExpressLRS + analog
  VTX** ecosystem — the "meilleure solution optimum existante" for a
  from-scratch outdoor micro.

What we deliberately do differently: the flight controller stays **our
ESP32-P4 + C6 + `fc_core`** (fully programmable, Tello-SDK compatible, Wi-Fi
H.264 as a bonus link) instead of a Betaflight F4 — one firmware family
across every Stratos model.

## Positioning

| | Fr4n7-001 (indoor) | **Fr4n8-001 (this)** |
|---|---|---|
| Class | Tello-class 118 mm, ducts | **85 mm-class toothpick, open props** |
| Wheelbase / props | 118 mm / 3" (76 mm) | **65 mm / 40 mm (1.6") tri-blade** |
| Motors | 8520 brushed | **0802-class brushless ~14000KV** |
| ESC | 4× low-side FET (on board) | **4× integrated BLHeli_S/Bluejay ESC** (shared AIO) |
| Battery | 1S 1100 (Tello pack) | **2S 450 mAh XT30** |
| Control | Wi-Fi (Tello SDK 2.0) | **ELRS radio (CRSF)** + Wi-Fi SDK kept |
| FPV video | Wi-Fi H.264 720p | **analog 5.8 GHz (nano cam + VTX)** + Wi-Fi bonus |
| Use | indoor, position hold (ToF+flow) | **outdoor** (IMU+baro; drift accepted) |
| AUW target | 92 g | **60-75 g** |
| Board | `hardware/pcb/` 38×74 | **`hardware/pcb_fpv/` 32×32 AIO (shared with fpv2)** |

## Target specifications (v0 charter)

- **Frame**: printed unibody plate (PLA-CF/PETG), wheelbase **65 mm**,
  overall ≈ **84 × 84 mm** (0.707·65 + 40), motor pods 3×M1.4 on Ø6.6,
  whoop 25.5×25.5 AIO mount, feet, octagonal canopy on the stack
  (camera 15° + VTX bay + RX shelf), H ≈ 32 mm with antenna.
- **Propulsion**: 0802 ~14000KV 2S, 40 mm tri-blade → thrust ≈ 35-45 g/motor
  (TUNE) → T/W ≥ 2 at 70 g.
- **Electronics**: STRATOS FPV AIO (shared) — see
  [`../hardware/pcb_fpv/`](../hardware/pcb_fpv/).
- **Radio**: any ExpressLRS RX on the CRSF socket (420 kbaud).
- **Video**: analog nano cam → 25-400 mW VTX (SmartAudio), all goggles.
- **Firmware**: `fc_core` unchanged; `outputs_dshot.c` + `crsf_task.c`
  **specified, not implemented** — see [`DESIGN.md`](DESIGN.md).

## Repository layout (this folder)

```
fpv85/
  README.md            this charter
  DESIGN.md            decisions + weight budget + DShot/CRSF firmware spec
  ROADMAP.md           M0 -> M4
  cad/                 frame.scad (plate + canopy), stl/, preview/
  viz/                 browser viewer + PLAYGROUND simulator (keyboard flight)
  hardware/README.md   shared AIO pointer + module BOM (RX/VTX/cam/motors)
  firmware/README.md   shared-verbatim vs specified-not-implemented
  sim/README.md        SDF parameter targets (Gazebo port = M3)
```

**See it in 3-D** — open [`viz/drone_viewer.html`](viz/) (self-contained;
`?playground=1` = the browser flight simulator).

## Status

**M0 — concept & scaffold (this commit).** Charter, clean-room CAD v0
(frame + canopy, printable), viewer + playground, shared AIO board at M0,
firmware specs written. **Not printed, not flown — see the TUNE tags and
`hardware/pcb_fpv/KNOWN_GAPS.md` before building.**
