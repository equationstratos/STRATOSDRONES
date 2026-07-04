# Fr4n6-001 — roadmap

- [x] **M0 — Concept & scaffold** (this commit)
  charter (`README.md`), architecture (`DESIGN.md`), part selection and
  block diagram (`hardware/`), printable 5" frame v0 + ducts option
  (`cad/`), `fc_core` parameter preset (`firmware/`), sim parameters
  (`sim/`).
- [ ] **M1 — Airframe validation**
  print frame v0 (PETG + PA-CF), dry-fit 2207 motors / 30.5 stack /
  battery shelf / ducts; iterate `frame.scad`; publish STLs + print
  profiles; optional carbon plate DXFs.
- [ ] **M2 — "Stratos Bolt" board**
  KiCad schematic + layout following the Fr4n7 pipeline
  (`hardware/pcb/scripts/`, generated netlist/BOM/CPL + honest
  `KNOWN_GAPS.md`); DSHOT-on-RMT firmware backend proven on a bench
  ESC; power tree validated 2–6S.
- [ ] **M3 — Sim + firmware parity**
  Fr4n6 SDF model (mass/inertia/rotors), `spawn_swarm.sh --model fr4n6`,
  SITL mission tests green with the Fr4n6 parameter preset; mixed
  Fr4n7+Fr4n6 swarm demo in the site playground.
- [ ] **M4 — First flight program**
  ducts on, props-off bring-up per `docs/safety.md`, current-limited
  hover, tune rates, publish flight logs + updated params.
