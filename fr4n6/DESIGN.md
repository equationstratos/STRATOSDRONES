# Fr4n6-001 — design & architecture decisions

This document records *why* the Fr4n6-001 is shaped the way it is. The two
reference platforms are the
[DroneBlocks DEXI](https://droneblocks.io/program/dexi-5-px4-stem-drone-kit/)
(educational 5" PX4 dev drone) and the
[Bitcraze Crazyflie Bolt 1.1](https://www.bitcraze.io/products/crazyflie-bolt-1-1/)
(open FC for brushless builds). Both are excellent; neither is what we're
building. The Fr4n6-001 is **the Stratos stack, scaled up**.

## 1. One brain, one firmware, two drones

**Decision: keep the ESP32-P4 + ESP32-C6 pair and `fc_core`.**

- DEXI splits responsibilities three ways: FMUv6X flight controller (PX4)
  + Raspberry Pi CM4 companion (ROS 2 / DroneBlocks) + Pi camera. Powerful,
  but three firmware worlds to learn.
- The Bolt's genius is the opposite move: *the same firmware as the micro
  Crazyflie*, on a board that drives big ESCs. Buy the small one to learn,
  the big one to carry — nothing to relearn.
- We follow the Bolt: `fc_core` is platform-independent C99 already
  compiled into both the Fr4n7 firmware and the Gazebo plugin. The Fr4n6
  adds **backends**, not a new stack:
  - `outputs_dshot.c` — DSHOT600 on 4 GPIOs via the P4's RMT peripheral
    (replaces the brushed LEDC PWM backend; protocol choice mirrors the
    Bolt's M4 PB9→PB10 rework that exists precisely to allow DSHOT).
  - `power_sense.c` — VBAT divider scaled for 2–6S + shunt current sense
    (INA-style) for battery telemetry and sag compensation.
  - Everything above the mixer — estimator, commander, Tello SDK parser,
    swarm semantics, params — is untouched. `battery?`, `rc`, `go`,
    `curve`, `flip` behave identically on both models.
- The CM4/Jetson class companion becomes an **optional deck** on a 5 V/3 A
  rail + USB/UART, for ROS 2 / vision workloads (DEXI level-III use), not
  a dependency for flight or FPV.

Consequence for users: every script in `sdk/python/examples/` — and the
site playground — flies the Fr4n6 unmodified. A mixed Fr4n7+Fr4n6 swarm is
just `TelloSwarm.fromIps([...])`.

## 2. Electronics — "Stratos Bolt" board concept

Bolt-style: our board is the FC + power backbone; propulsion stays
industry-standard and replaceable.

- **4-in-1 ESC socket** (standard 30.5×30.5 stack, 8-pin harness: VBAT,
  GND, M1–M4 signal, telemetry, current). Rationale: the FPV ecosystem's
  best price/perf and easiest classroom replacement — and it keeps the
  hot, high-current electronics off our board (the Bolt's integrated PDB
  tops out around 8 A/motor; 5" quads want 30–50 A bursts).
- **Wide VBAT input 2–6S** (Bolt is 1S–4S; DEXI runs 6S Li-ion). Buck to
  5 V/3 A (companion + peripherals) and 3V3 rails. Reverse-polarity
  protection, ideal-diode ORing with USB-C.
- **Sensors**: ICM-42688-P (SPI, anti-vibration mounted), SPL06-001 baro
  (foam-covered), PMW3901 + VL53L1X on a downward bay (DEXI's indoor
  positioning stack — proven in our Fr4n7 stack too), QMC/IST8310 compass
  pads + **GPS port** (UART4 + I2C, JST-GH) for outdoor missions.
- **Camera**: same OV5647 MIPI-CSI → P4 hardware H.264 720/1080p over
  Wi-Fi (the Tello-protocol video). A **20×20 bay + 9 V rail pad** accepts
  an analog VTX or HD air unit for "real FPV" — optional, off by default.
- **Stratos Deck connector** (Bolt-inspired): 2×10 header exposing 3V3,
  5 V, VBAT, I2C, SPI, 2×UART, 6×GPIO + a 1-wire/EEPROM pin for
  **deck auto-detection**, mechanically stackable above the board.
- **LED ring output** (WS2812 data + 5 V) for a DEXI-style orientation
  ring in the ducts.
- **USB-C** (P4 native) for flashing/logs; boot/reset buttons; microSD
  pads (blackbox option).

Block diagram and part-by-part selection: `hardware/README.md`.

## 3. Airframe — printable first, carbon optional, ducts optional

- DEXI ships a guarded/ducted 5" airframe aimed at classrooms; the Bolt
  is BYO-frame. We split the difference: a **printable one-piece 220 mm
  X-frame** (PETG / PA-CF) sized for 2207 motors (16×16 M3), with:
  - optional **printed prop ducts** (DEXI-style safety + look) that bolt
    onto the motor pods,
  - optional **2 mm carbon top/bottom plates** using the same hole
    pattern for crash-heavy use (files provided, laser-cut anywhere),
  - 30.5×30.5 FC stack, 20×20 FPV bay behind a tilted (0–25°) camera
    mount, rear battery shelf (strap slots) sized for 4S 1500 LiPo up to
    6S Li-ion brick, downward sensor window ahead of the battery.
- Parametric OpenSCAD (`cad/frame.scad`) exactly like the Fr4n7's CAD:
  every dimension a named parameter, STL exported in CI-able one-liners.

## 4. Simulation & parameters

- Same Gazebo Harmonic plugin (`sim/gazebo/StratosFcSystem.cc`) — it
  already reads mass/inertia/rotor geometry from the SDF. `fr4n6/sim/`
  documents the 5" parameter set (mass ~0.62 kg, arm 110 mm, thrust
  coefficient for 5×4.3×3 props at 4S) so `spawn_swarm.sh` can spawn
  either model.
- `fc_core` parameter preset (`firmware/params_fr4n6.md`): rates, angle
  limits, takeoff height, speeds — set through the existing `param`
  SDK extension, no code fork.

## 5. What stays honest

- This folder starts at **M0 (concept + scaffold)**: charter, part
  selection, printable frame v0, parameter preset. The PCB is *planned*,
  not drawn: the Fr4n7 board taught us the KiCad-generation pipeline
  (`hardware/pcb/scripts/`) and its `KNOWN_GAPS.md` discipline — the
  Fr4n6 board will follow the same route with its own honest ledger.
- Safety scales with the airframe: a 5" quad is not a toy. The frame
  ships duct-first for classroom use, and `docs/safety.md` applies
  doubly here (props-off bring-up, current-limited first spins).

## Sources

- DroneBlocks DEXI — program page: <https://droneblocks.io/program/dexi-5-px4-stem-drone-kit/>
- DEXI on PX4 showcase: <https://px4.io/project/dexi/>
- DEXI-5 motor set (22×7 mm stator, 1980 KV): <https://droneblocks.io/product/dexi-5-motor-set/>
- Crazyflie Bolt 1.1 product page: <https://www.bitcraze.io/products/crazyflie-bolt-1-1/>
- Crazyflie Bolt 1.1 datasheet (STM32F405 + nRF51822, BMI088, DSHOT-capable
  M4 rework, 1S–4S, ~8 A PDB, deck connector):
  <https://www.bitcraze.io/documentation/hardware/crazyflie_bolt_1_1/crazyflie_bolt_1_1-datasheet.pdf>
