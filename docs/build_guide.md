# Build guide — from files to a flying drone

Order of operations: **fly the simulator first** (no hardware needed), then
order the PCB, print the frame, assemble, and bring it up.

## 0. Try it in simulation (today, no hardware)

```bash
# host build + flight-core tests
cd fc_core && cmake -B build && cmake --build build && ctest --test-dir build

# SITL drone + a mission, via stock djitellopy
cd ../sim && cmake -B build && cmake --build build --target sitl_runner
pip install djitellopy
python ../sdk/python/examples/01_hover.py
```

For the full Gazebo model and swarms see `sim/` (`spawn_swarm.sh`, the
`sim/tests/`), and the top-level `README.md`.

## 1. Order the PCB (JLCPCB PCBA)

> First read `hardware/pcb/KNOWN_GAPS.md` and close the VERIFY items — the
> generated board is a reviewable starting point, **not** yet fab-ready.

1. `cd hardware/pcb && make` regenerates the board, pinmap, fab files and runs
   the consistency check.
2. Open `stratosdrone.kicad_pcb` in KiCad 8, finish routing, fill zones (**B**),
   run **DRC** to zero errors.
3. Plot gerbers + drill from KiCad; export the BOM/CPL (the committed
   `jlcpcb/bom.csv` and `cpl.csv` are correct for assembly; re-plot the gerbers
   after routing).
4. At JLCPCB: 4-layer, 1.6 mm, JLC04161H-7628 stackup, ENIG; PCBA both sides;
   upload `bom.csv` + `cpl.csv`. See `hardware/pcb/README.md` for the full
   options list and a cost estimate.

You solder the through-hole / hand parts yourself after the PCBA arrives:
the four motor connectors, the battery lead, and the camera FFC (if not
pre-fitted).

## 2. Print the frame

```bash
cd hardware/frame
for f in frame prop_guards canopy; do
  openscad -o stl/$f.stl --export-format binstl $f.scad
done
```

Three parts: `frame.scad` (X-frame with the motor pockets, PCB standoffs and
the under-slung battery bay), `canopy.scad` (top shell with the 10° camera
cradle and LED light pipes), and `prop_guards.scad` (print ×4). PETG or tough
PLA, 4 perimeters on the frame, prop guards in PETG. The motor pockets are an
8.5 mm press fit (tune `motor_fit` in `frame.scad` for your printer). Target
all-up weight ≈ 90 g (95 g hard cap) — weigh as you go.

## 3. Assemble

1. Press the four 8520 motors into the frame pockets (2 CW + 2 CCW, diagonal
   pairs); route the wires through the arm channels.
2. Mount the PCB on the M2 standoffs (36 mm pitch); solder the motor leads to
   the corner pads (VBAT + drain — watch polarity), and the battery JST.
3. Fit the camera module to the canopy cradle (10° up), connect its FFC.
4. Snap on the canopy and (for early flights) the prop guards. Fit props last.

## 4. Bring it up

Follow `docs/bringup.md`: flash the ESP32-P4 and the ESP32-C6 Wi-Fi
co-processor, calibrate, verify motor directions **with props off**, then a
first hover. Read `docs/safety.md` first.
