# Fr4n6-001 — the big brother (5" FPV-class, brushless)

The second Stratos Drones model: a **larger, brushless, FPV-style development
quad** built on the exact same open DNA as the Fr4n7-001 — one repo, full
code + CAD + firmware + hardware + PCB, permissive licences, sim-first.

Where the Fr4n7-001 is a Tello-class 92 g indoor micro, the Fr4n6-001 is a
**5-inch, 4S–6S, ~600 g** platform you can fly outdoors, carry payloads on,
and hack at every layer — while keeping the same brain, the same Tello SDK
2.0 wire protocol, the same Python/DroneBlocks-style scripting, the same
Gazebo twin, and the same swarm story.

## Inspirations (credit where due)

- **[DroneBlocks DEXI](https://droneblocks.io/program/dexi-5-px4-stem-drone-kit/)**
  ([PX4 showcase](https://px4.io/project/dexi/)) — the benchmark for an
  *educational* 5" dev drone: solder-free modular build, optical-flow +
  ToF indoor positioning, onboard companion computer + camera + GPIO,
  curriculum-first. Fr4n6-001 adopts: the 5" educational-dev positioning,
  flow+ToF indoor stack, guarded/ducted printable frame options, a
  companion-computer bay, and 2207-class motors
  ([DEXI-5 motors: 22×7 mm stator, 1980 KV](https://droneblocks.io/product/dexi-5-motor-set/)).
- **[Bitcraze Crazyflie Bolt 1.1](https://www.bitcraze.io/products/crazyflie-bolt-1-1/)**
  ([datasheet](https://www.bitcraze.io/documentation/hardware/crazyflie_bolt_1_1/crazyflie_bolt_1_1-datasheet.pdf))
  — the benchmark for an *open flight controller* for brushless builds:
  tiny FC+PDB running the exact same firmware as its micro sibling,
  DSHOT-capable outputs for external ESCs, 1S–4S input, and an
  auto-detected expansion-deck connector. Fr4n6-001 adopts: **one firmware
  across both models** (our `fc_core`), the FC+PDB-for-external-ESC board
  concept, wide battery input, and a deck-style expansion connector.

What we deliberately do differently from both: **no separate autopilot +
radio MCU pair, no mandatory companion computer**. The ESP32-P4 + ESP32-C6
combo already proven on the Fr4n7-001 does flight, Wi-Fi 6 and hardware
H.264 video on its own — the companion computer (CM4/Jetson) becomes an
*optional deck*, not a requirement.

## Positioning

| | Fr4n7-001 | **Fr4n6-001** |
|---|---|---|
| Class | Tello-class micro, indoor | 5" FPV-class dev quad, indoor + outdoor |
| Props / motors | 3" · 8520 brushed | **5" · 2207 brushless ~1750–1980 KV** |
| ESC | on-board MOSFETs | **external 4-in-1 (30.5×30.5), DSHOT600** |
| Battery | 1S Li-ion | **4S LiPo (default) · 2S–6S tolerated · 6S Li-ion endurance option** |
| AUW | ~92 g | **~550–700 g** (config-dependent) |
| Brain | ESP32-P4 + ESP32-C6 | **same** |
| Flight code | `fc_core` (C99) | **same core, new output + power backends** |
| Protocol | Tello SDK 2.0 wire-compatible + extensions | **same** (same apps, same swarm scripts) |
| Camera | OV5647 CSI → HW H.264 720/1080p Wi-Fi | same, + **20×20 FPV bay** (analog/HD option) |
| Positioning | PMW3901 flow + VL53L1X ToF | same indoor stack + **GPS/compass port** outdoor |
| Expansion | — | **Stratos Deck connector** (I2C/SPI/2×UART/GPIO/5V/VBAT, EEPROM auto-detect) + companion bay |
| Frame | printed clamshell | **printed 5" frame, optional printed ducts/guards, optional carbon plates** |
| Sim | Gazebo Harmonic twin, same `fc_core` | same plugin, Fr4n6 mass/thrust model |

## Target specifications (v0 charter — see `DESIGN.md` for rationale)

- **Frame**: 5" props, ~220 mm wheelbase, X layout; printable one-piece
  bottom frame (PETG/PA-CF) with optional printed prop ducts (DEXI-style)
  and optional 2 mm carbon top/bottom plate upgrade; 30.5×30.5 mm FC
  mount, 16×16 mm M3 motor mounts, 20×20 mm FPV cam/VTX bay.
- **Motors**: 2207 1750 KV (4S) / 1300 KV (6S endurance) — DEXI-5 class.
- **ESC**: any standard 30.5×30.5 4-in-1, BLHeli_32/AM32, ≥45 A burst,
  DSHOT600.
- **Board (the "Stratos Bolt")**: ESP32-P4 (flight + CSI camera + H.264)
  + ESP32-C6 (Wi-Fi 6), ICM-42688-P + SPL06-001, PMW3901 + VL53L1X down
  bay, 2–6S VBAT input with current/voltage telemetry, 4-in-1 ESC socket
  (8-pin harness: VBAT, GND, 4×DSHOT, telem, current), 5 V/3 A companion
  rail, GPS+compass UART/I2C port, Stratos Deck connector, USB-C, WS2812
  ring output (DEXI-style LED ring option).
- **Battery**: 4S 1500–2200 mAh LiPo default; 6S 4000 mAh Li-ion pack
  option for endurance (DEXI-style).
- **AUW targets**: ≤650 g (4S sport) / ≤850 g (6S endurance + companion).
- **Firmware**: same `fc_core`; new `outputs_dshot` backend, scaled
  parameter set (`firmware/params_fr4n6.md`), same SDK verbs — a
  `03_swarm.py` script must fly a mixed Fr4n7 + Fr4n6 swarm unmodified.
- **Sim**: same Gazebo plugin; `sim/` carries the Fr4n6 mass/inertia/
  thrust parameters so missions transfer 1:1.

## Repository layout (this folder)

```
fr4n6/
  README.md          this charter
  DESIGN.md          architecture & decisions (electronics, firmware, CAD, sim)
  ROADMAP.md         milestones M0–M4
  hardware/          block diagram, part selection, PCB plan (KiCad to come)
  cad/               parametric OpenSCAD frame → STL (+ preview renders)
  firmware/          fc_core integration notes + Fr4n6 parameter preset
  sim/               Gazebo model parameters for the 5" airframe
```

## Status

**M0 — concept & scaffold (this commit).** The charter, architecture,
part selection, printable frame v0 and parameter preset are in. Next:
KiCad board bring-up (`ROADMAP.md`).
