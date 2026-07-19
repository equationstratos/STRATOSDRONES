# STRATOS FPV AIO — the shared brushless 2S board (M0, concept)

**One board, two drones.** This is the all-in-one flight controller for the
two outdoor-FPV models — [`fpv85/`](../../fpv85/) (Fr4n8-001, 85 mm-class)
and [`fpv2/`](../../fpv2/) (Fr4n9-001, 2") — on the **whoop-standard
25.5 × 25.5 mm M2 mount** so both printed frames take the same board.

Same **PCB-as-code pipeline** as the Fr4n7 board
([`../pcb/`](../pcb/)): everything is generated from one
`scripts/design.py` (158 components, 157 nets), edit → `make`.

| | Fr4n7 board (`../pcb/`) | **FPV AIO (this)** |
|---|---|---|
| Size / mount | 38×74, 26×62 | **32×32, 25.5×25.5 whoop** |
| Battery | 1S, TP4056 USB-C charge | **2S XT30** (charge off-board) |
| Motors | 4× brushed FET (8520) | **4× integrated brushless ESC** (EFM8BB21 + FD6288T + 6 FET — BLHeli_S/Bluejay) |
| Radio | Wi-Fi only (C6) | Wi-Fi **+ CRSF socket for an ELRS RX** |
| FPV video | Wi-Fi H.264 (P4) | **analog 5.8 GHz bay (VTX + nano cam)** + Wi-Fi H.264 bonus |
| Rails | 3V3 (SY8089, ≤5.5 Vin) | **AP63203 3V3 + AP63205 5V** (wide-Vin) |
| Indoor sensors | ToF + optical flow | **removed** (outdoor build — IMU + baro) |
| Brain | ESP32-P4 + C6 | **identical** (same fc_core, SDK, programmability) |

## Regenerate

```bash
cd hardware/pcb_fpv
python3 scripts/design.py       # pure python — self-check (runs anywhere)
make pinmap schematic           # pure python — out/board_pinmap_fpv.h + .kicad_sch
make board fab check            # needs KiCad (pcbnew + kicad-cli):
                                #   → CI runs these in kicad/kicad:8.0 and uploads
                                #     the jlcpcb-fpv artifact, or run on desktop KiCad
```

The `.kicad_pcb` is **not committed yet** — it is produced by the CI job
(`.github/workflows/hardware.yml`, `board-fpv`) or `make board` on a machine
with KiCad, exactly like the first board was. Then: route (desktop KiCad),
re-export fab, order.

## Ordering flow (A → Z)

1. Work through **[`KNOWN_GAPS.md`](KNOWN_GAPS.md)** — several new-part pin
   maps are `VERIFY` and **fab-blocking**.
2. `make board` (CI or desktop) → open in KiCad, route (the placer leaves
   ratsnest, as on the first board), `make fab`.
3. Upload `jlcpcb/gerbers.zip` + `bom.csv` + `cpl.csv` to JLCPCB (4-layer,
   1.6 mm — 0.8-1.0 mm also fine at this size).
4. Off-board modules per drone (see each model's `hardware/README.md`):
   ELRS RX, analog VTX 25-400 mW, nano camera, 4 motors, props, 2S pack.

## Status

**M0 — design database + generators.** The netlist is complete and
self-checked; the board geometry, routing, DRC and fab exports come from the
KiCad stage. **Not fabricated, not flight-validated.**
