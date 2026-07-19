# STRATOS FPV AIO — known gaps (read BEFORE ordering)

Honest ledger, same discipline as [`../pcb/KNOWN_GAPS.md`](../pcb/KNOWN_GAPS.md).
The board is **M0**: netlist complete + self-checked, geometry not yet
generated in this repo (needs the KiCad CI container or desktop KiCad).

## 1. FAB-BLOCKING — new-part pin maps are architecture-level (VERIFY)

Every part carried over from the Fr4n7 board keeps its **verified** pin map
(ESP32-P4 supply topology, C6 SDIO, IMU, baro, flash, USB, TLV62569 core
buck). Every **new** part's pad numbering was written from the standard
application topology, **not** datasheet-in-hand. Verify each against its
datasheet before `make fab`:

| Part | What to verify |
|---|---|
| U5 **AP63203** / U11 **AP63205** (TSOT-26) | pin order GND/SW/VIN/FB/EN/BST; fixed-output FB pin behaviour; LCSC codes |
| U20-23 **EFM8BB21F16G** (QFN20) | which pads are VDD/GND, the 6 PWM outs, the DShot input pin, C2CK/C2D — cross-check a Bluejay reference ESC schematic |
| U30-33 **FD6288T** (TSSOP20) | full pin table (HIN/LIN/HO/LO/VS/VB/VCC/COM) ; **VCC min ~6 V**: fine at 2S nominal, MARGINAL at the 6.0 V cutoff |
| J5-J8 / J12 **JST-SH** footprints | exact KiCad footprint names resolve (fallback 1.27 headers declared via `fp_alt`) |
| LED1/2 **WS2812B-2020 on 5 V** | data VIH = 0.7·VDD = 3.5 V vs 3.3 V P4 drive — marginal; add a level shifter or run first LED at lower VDD if flicker |

## 2. FAB-BLOCKING — ESC power stage is a NEW sub-design

The 4× integrated ESC (EFM8 + FD6288T + 6× AO3400) is the open architecture
of commercial whoop AIOs, but **this repo has no prior proven instance**.
Before ordering: gate-resistor/dead-time review, FET SOA at 2S stall current,
copper area for phase currents (~5-8 A bursts), bulk capacitance per bridge.
BLHeli_S/Bluejay must be flashed via the C2 pads (TP1-8) at first assembly.

## 3. Placement density 32×32 is UNPROVEN

158 footprints incl. 4 ESC stages on 32×32 (both sides) is tight. The PLACE
anchors are untested in this sandbox (no pcbnew) — the CI `board-fpv` job's
`assert_placement()` is the gate. If it fails: grow `BOARD` to 35 or 36 mm
square (mount pattern unchanged; both frames absorb it).

## 4. Inherited from the Fr4n7 board (unchanged)

* **ESP32-P4 strapping pins UNVERIFIED** (BOOT = GPIO35 assumption).
* **Camera FFC pinout + CSI lane order/polarity UNVERIFIED** (J4 optional).
* Crystal load caps nominal (10 pF) — verify against the chosen crystal.

## 5. 2S bring-up notes

* No on-board charger (deliberate): charge the pack on a USB-C 2S balance
  charger. USB-C here is **data/flash only**.
* VBAT_SENSE divider is /3 (2×100k + 100k): firmware scale differs from Fr4n7.
* FD6288T at 2S cutoff (6.0 V) is at the VCC floor — consider 2S land-voltage
  cutoff ≥6.4 V in firmware.

## 6. Radio & video are module-level (by design)

ELRS RX (CRSF socket J12) and analog VTX/cam (J13/J14 pads) are off-the-shelf
modules — no custom RF on this board. The C6's Wi-Fi antenna keepout at the
FRONT edge must stay copper-free (the generator places U3 antenna-out).

## 7. Firmware is SPECIFIED, NOT IMPLEMENTED

`outputs_dshot.c` (DShot600 on RMT, GPIO45-48) and `crsf_task.c` (UART
GPIO4/5 → `fc_cmd_rc()`, failsafe → `fc_cmd_emergency()`) are specified with
an implementation map in [`../../fpv85/DESIGN.md`](../../fpv85/DESIGN.md).
The board is electrically independent of that work (BLHeli_S ESCs also accept
plain PWM for first bench spins).
