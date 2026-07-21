# Fr4n10-001 (TinyHoop MK1) — roadmap

- [x] **M0 — Concept & scaffold** (this commit): charter, clean-room CAD v0
      (carbon DXF + printable STL + TPU), browser viewer + playground,
      TINYHOOP AIO board at M0 (design.py + generators + CI), **implemented**
      fc_core mode manager / show executor / CRSF parser / LoRa protocol
      (host tests green), ESP-IDF dshot/crsf/sx1262/lora tasks (CI-compiled),
      stratospy LoRa transport + show compiler + swarm examples (run in sim).
- [ ] **M1 — Print & fit**: print the plates (proto thicknesses), dry-fit
      motors/board/cam/O4/RX/battery, iterate the TUNE outlines, then cut
      the 3 mm / 2 mm carbon from the DXFs.
- [ ] **M2 — Board bring-up**: VERIFY pass on pcb_tinyhoop KNOWN_GAPS
      (SX1262 pad map, ESC FET SOA at 3S, 5 V budget), CI board → route
      (desktop KiCad) → order → solder → ESC flash → bench spin (PWM first,
      then DShot), flow/ToF sanity on the bench.
- [ ] **M3 — Radio + LoRa + sim**: ELRS bind + failsafe test (props off),
      dongle bridge flashed, `stratospy.lora` end-to-end (mode/telemetry/
      show upload), Gazebo model `sim/models/stratos_tinyhoop` with 2520
      thrust constants, 3-drone show rehearsed in sim then on the bench.
- [ ] **M4 — Flights & shows**: line-of-sight hover (STABILIZED on flow/ToF)
      → FPV manual → single-drone figures → GPS module + outdoor absolute
      positioning → first multi-drone LoRa-synced formation; publish logs +
      updated weight table.
