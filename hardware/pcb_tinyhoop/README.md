# STRATOS TINYHOOP AIO — the programmable/swarm 2.5" board (M0, concept)

The all-in-one flight controller for the **TinyHoop MK1** (Fr4n10-001), on the
**whoop-standard 25.5 × 25.5 mm M2 mount** so it drops into the JeNo-Pocket-V2
frame. It is the [STRATOS FPV AIO](../pcb_fpv/) plus the pieces the show/swarm
mission needs — defined by *importing* that verified design database and
layering deltas, so the shared 90 % stays a single source of truth.

Same **PCB-as-code pipeline** as every Stratos board: everything comes from
`scripts/design.py` — edit → `make`.

| | FPV AIO (`../pcb_fpv/`) | **TINYHOOP AIO (this)** |
|---|---|---|
| Size / mount | 32×32, 25.5×25.5 | **34×34, 25.5×25.5** |
| Battery | 2S XT30 | **2S-3S XT30** (VBAT divider /5) |
| Motors | 4× ESC (0802/1102 class) | **4× ESC, FET re-rated for 1203-1303 up to 3S (VERIFY)** |
| Radio | Wi-Fi + CRSF socket | **+ SX1262 LoRa 868 (E22 module, optional)** |
| Position hold | removed | **PMW3901 flow + VL53L1X ToF re-added** |
| GPS | — | **J15 UART + compass connector** |
| FPV video | analog 5.8G bay | **analog bay + O4 Lite (power off LiPo)** |
| Brain | ESP32-P4 + C6 | **identical** (same fc_core, SDK, programmability) |

## Regenerate

```bash
cd hardware/pcb_tinyhoop
python3 scripts/design.py       # pure python — self-check (runs anywhere)
make pinmap                     # pure python — writes the firmware header
make board fab check            # needs KiCad (pcbnew + kicad-cli):
                                #   CI runs these in kicad/kicad:8.0 and uploads
                                #   the jlcpcb-tinyhoop artifact, or run on desktop
```

`design.py` self-checks the netlist (172 components, 175 nets — the FPV AIO
base plus the flow/ToF/LoRa/GPS deltas and the /5 divider). `make pinmap`
writes `firmware/components/board/include/board_pinmap_tinyhoop.h`, the header
the `-DSTRATOS_BOARD_TINYHOOP` firmware build consumes. The `.kicad_pcb` is
**not committed** — it is produced by the CI `board-tinyhoop` job or `make
board` on a machine with KiCad, exactly like the other boards.

## Ordering flow (A → Z)

1. Work through **[`KNOWN_GAPS.md`](KNOWN_GAPS.md)** — the SX1262 module pad
   map and the ESC FET current rating are **fab-blocking** VERIFYs, on top of
   everything inherited from the FPV AIO ledger.
2. `make board` (CI or desktop) → open in KiCad, route (the placer leaves
   ratsnest, as on the other boards), `make fab`.
3. Upload `jlcpcb/gerbers.zip` + `bom.csv` + `cpl.csv` to JLCPCB (4-layer,
   1.6 mm). The SX1262 module (U12) is DNP by default — populate it only on
   swarm builds.
4. Off-board modules (see [`../../TinyHoopMK1/hardware/README.md`](../../TinyHoopMK1/hardware/README.md)):
   ELRS RX, analog VTX + nano cam **or** DJI O4 Lite, 4 motors, props, 2S-3S
   pack, optional GPS, and the ground LoRa dongle.

## Status

**M0 — design database + generators.** The netlist is complete and
self-checked; board geometry, routing, DRC and fab exports come from the
KiCad stage. **Not fabricated, not flight-validated.**
