# Fr4n8-001 (fpv85) — roadmap

- [x] **M0 — Concept & scaffold** (this commit): charter, clean-room CAD v0
      (plate + canopy), browser viewer + playground simulator, shared FPV AIO
      board at M0 (design.py + generators + CI), DShot/CRSF firmware specs.
- [ ] **M1 — Print & fit**: print plate/canopy, dry-fit motors/board/cam/VTX/RX,
      iterate the TUNE dims (motor circle, cam width, strap slots, feet).
- [ ] **M2 — Board bring-up**: VERIFY pass on pcb_fpv KNOWN_GAPS, CI board →
      route (desktop KiCad) → order → solder → Bluejay flash via C2 pads →
      bench spin (PWM first, then `outputs_dshot.c`).
- [ ] **M3 — Radio + sim**: `crsf_task.c` (ELRS bind, failsafe), Gazebo/SIL
      thrust constants for the 65 mm airframe, `sim/models/stratosdrone_fpv85`.
- [ ] **M4 — Outdoor flights**: line-of-sight hover → FPV goggles → tuned
      rates; publish flight logs + updated weight table.
