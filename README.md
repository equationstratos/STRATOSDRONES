# STRATOSDRONES

**A fully open-source DJI Tello EDU class drone** — hardware (KiCad PCB you can order assembled from JLCPCB), 3D-printable frame (OpenSCAD), flight firmware (ESP32-P4 + ESP32-C6), Tello SDK 2.0 wire-compatible programming interface, swarming, and a complete Gazebo simulation that speaks the exact same protocol as the real drone.

> Fly your mission scripts against the Gazebo sim today, order the PCB, print the frame, and run the *same unmodified Python code* on the real drone.

## Specs vs DJI Tello EDU

| | DJI Tello EDU | STRATOSDRONES |
|---|---|---|
| Weight / wheelbase | 87 g / 118 mm | ~92 g / 118 mm |
| Motors / props | brushed 8520 / 3" | identical (Tello-compatible props) |
| MCU | proprietary + Myriad 2 | **ESP32-P4** (flight + camera + H.264 hw encoder) + **ESP32-C6** (Wi-Fi 6) |
| Sensors | IMU, baro, ToF, optical flow | ICM-42688-P, SPL06-001, VL53L1X, PMW3901 |
| Camera | 5 MP, 720p30 H.264 | **OV5647 5 MP MIPI-CSI, hardware H.264 720p30 (Tello wire format) + 1080p30 extension** |
| SDK | Tello SDK 2.0 (UDP 8889/8890/11111) | **wire-compatible incl. video** — [djitellopy](https://github.com/damiafuentes/DJITelloPy) works unmodified — plus extensions |
| Swarm | STA mode on shared AP | identical, **plus simulated swarms in Gazebo** |
| Simulation | none | full Gazebo Harmonic model running the *same* flight-control code |
| License | closed | MIT (code), CERN-OHL-P-2.0 (hardware), CC-BY-4.0 (docs) |

## Repository layout

```
fc_core/            Platform-independent flight control core (pure C99, no RTOS deps)
                    — compiled into BOTH the ESP32-P4 firmware and the Gazebo plugin
firmware/           ESP-IDF project for ESP32-P4 (esp32p4 target)
sim/                Gazebo Harmonic plugin, drone SDF model, worlds, swarm launcher
sim/viz/            Self-contained 3-D drone viewer (open drone_viewer.html) generated from the SDF
sdk/python/         stratospy: thin djitellopy add-on for STRATOS extensions + examples
android/            Android ground-control app (Tello SDK 2.0 client — takeoff/land/flip, joysticks, live video)
fr4n6/              Fr4n6-001 — the 5" brushless FPV-class model (charter, CAD, hardware plan; same fc_core)
foldable/           Fr4n7-F — folding-arm variant (spring pivots + latch; button or `deploy`-servo release; CAD + animated viewer)
fpv85/              Fr4n8-001 — outdoor micro FPV, 85 mm class (ELRS radio + analog 5.8G video, 2S brushless; CAD + viewer + playground sim)
fpv2/               Fr4n9-001 — outdoor 2" FPV, 98 mm (same design language + SAME shared AIO board as fpv85)
TinyHoopMK1/        Fr4n10-001 — programmable/swarm 2.5" FPV (JeNo Pocket V2 frame, clean-room): 4 modes (manual/stabilized/program/swarm), ELRS + LoRa 868 fleet link, flow+ToF position hold, analog or DJI O4 Lite video
hardware/pcb/       KiCad project + JLCPCB fab outputs (gerbers, BOM, CPL) + component map
hardware/pcb_fpv/   STRATOS FPV AIO — shared brushless 2S board for fpv85+fpv2 (design.py → CI-generated KiCad board)
hardware/pcb_tinyhoop/ STRATOS TINYHOOP AIO — the TinyHoop MK1 board (FPV AIO + flow/ToF + SX1262 LoRa + GPS, 2S-3S)
sdk/lora_dongle/    ground LoRa dongle (ESP32+SX1262) — transparent fc_lorap bridge for the no-Wi-Fi PC/fleet link
hardware/frame/     Parametric OpenSCAD frames → STL:
                      • frame.scad …        open racing-style X-frame
                      • tello_style/ …      closed Tello-size clamshell body
docs/               Build guide, bring-up, SDK reference, architecture, safety
oasis30/            OASIS 30 — 3" build on the Sub250 OasisFly30 frame: parametric
                    gmsh-OCC model (STEP + printable STL), the printed parts the kit
                    lacks, 3-D viewer + assembly simulator
atelier/            FPV build-workshop site + print posters (buy-the-drone option, FPV league)
```

## Quick start (simulation)

```bash
# Ubuntu 24.04 — install Gazebo Harmonic (see docs/build_guide.md), then:
cd sim && cmake -B build && cmake --build build
./spawn_swarm.sh 1                      # one simulated drone on 127.0.0.2

pip install djitellopy
python sdk/python/examples/01_hover.py  # takeoff → hover → land, via the Tello protocol
python sdk/python/examples/03_swarm.py  # ./spawn_swarm.sh 3 first
```

## Status

- [x] `fc_core` flight control core + host tests (ctest, closed-loop SIL)
- [x] Gazebo Harmonic model + plugin, Tello-protocol UDP endpoint, multi-drone
- [x] Python SDK layer + examples
- [x] KiCad PCB + JLCPCB fab package *(review in KiCad before ordering — see docs/build_guide.md)*
- [x] OpenSCAD frame → STL
- [x] ESP32-P4 firmware tree (flight task, drivers, SDK server, H.264 video)
- [x] TinyHoop MK1 (Fr4n10): 4-mode manager + show/figure executor + CRSF + LoRa protocol in `fc_core` (host-tested); DShot/CRSF/SX1262/LoRa firmware (CI-compiled); STRATOS TINYHOOP AIO board; clean-room JeNo Pocket V2 CAD (STL+DXF); `stratospy.lora` + choreography compiler
- [ ] Hardware bring-up (waiting on first PCB batch — see docs/bringup.md)
- [ ] Real-world flight tuning, camera pipeline validation, 2-drone swarm

## Safety

This is a flying machine with spinning propellers. Read `docs/safety.md` before the first
flight: prop guards on, props off for the first power-up, never hand-catch, lipo handling.

## Licenses

- Code (fc_core, firmware, sim, sdk): [MIT](LICENSE)
- Hardware (hardware/): [CERN-OHL-P-2.0](LICENSES/CERN-OHL-P-2.0.txt)
- Documentation (docs/): [CC-BY-4.0](LICENSES/CC-BY-4.0.txt)

Clean-room policy: Crazyflie / ESP-Drone / Betaflight are used as *algorithmic references
only* (papers, datasheets, published behavior). No GPL code is copied. See CONTRIBUTING.md.
