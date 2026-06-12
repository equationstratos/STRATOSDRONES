# Contributing to STRATOSDRONE

## Clean-room policy (important)

STRATOSDRONE is MIT (code) / CERN-OHL-P (hardware) / CC-BY (docs). Several
excellent open-source flight stacks we admire — Crazyflie firmware, ESP-Drone,
Betaflight, Paparazzi — are **GPL-licensed**. To keep this project's licensing
intact:

- You may study their *published behavior*, papers, datasheets and documentation
  as algorithmic references (e.g. Mahony 2008 for the AHRS, the PX4Flow paper
  for optical-flow velocity estimation).
- You may **not** copy, transcribe or closely paraphrase GPL source code into
  this repository. Re-implement from first principles.
- Register init sequences taken from component datasheets/app-notes are facts,
  not creative works — they are fine (cite the datasheet section in a comment).

## Code style

- `fc_core/` is pure C99: no heap, no globals, no OS calls, one `fc_core_t`
  per drone instance. Everything must build for both host (tests/sim) and
  ESP-IDF without `#ifdef` forests.
- Keep simulation and firmware behavior identical: any control/estimation
  change must keep `ctest` green in `fc_core/` and the headless Gazebo
  mission test passing in `sim/`.
- SI units internally; Tello wire units only at the SDK boundary.

## Tests

```bash
cd fc_core && cmake -B build && cmake --build build && ctest --test-dir build
cd sim && cmake -B build && cmake --build build && pytest tests/
```

The SIL flight test (`fc_core/test/test_sil_flight.c`) is the tuning bench:
it must take off, hover within a 25 cm band, fly a 1 m `go`, rotate and land
on the 6-DOF plant before any controller change is merged.

## Hardware changes

Run ERC/DRC (`kicad-cli` 8) before pushing, keep the JLCPCB BOM/CPL exports in
sync with the schematic, and never change the motor connector pinout or the
battery polarity footprint without flagging it loudly in the PR description.
