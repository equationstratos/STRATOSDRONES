# STRATOSDRONE PCB — KNOWN GAPS (read before fabricating)

This board was generated programmatically from `scripts/design.py` as a
**reviewable starting point**, not a fabrication-ready design. The netlist,
BOM and placement are real and self-consistent (`make check` passes), but the
following must be resolved by a human in KiCad before you spend money at
JLCPCB. Items are ordered roughly by risk.

## Blocking — must resolve before ordering

1. **Signal routing is not done.** `gen_pcb.py` places footprints, assigns
   every net, and pours GND/3V3/VBAT planes, but the signal nets are left as
   ratsnest. Open `stratosdrone.kicad_pcb` in KiCad, finish routing, fill
   zones (hotkey **B**), then re-export gerbers. The gerbers in `jlcpcb/` are
   preliminary (unrouted) and will not produce a working board.

2. **Placement needs cleanup.** Auto-flowed passives currently overlap the
   MCU region. Re-place the decoupling near their power pins, keep the IMU
   (U6) away from motor-current copper, and keep the bottom-center 16 mm
   window (U8 VL53L1X + U9 PMW3901) clear of other parts and vias.

3. **ESP32-P4 core DC-DC topology + values UNVERIFIED.** `L2`/`C5` on
   `VDD_DCDCC`/`FB_DCDC`/`EN_DCDC` are placeholders. Replicate the exact
   inductor/cap network and feedback from the official *ESP32-P4 Hardware
   Design Guidelines* and the ESP32-P4-Function-EV-Board reference schematic.
   Wrong topology here = dead chip.

4. **`VDD_MIPI_DPHY` (2.5 V) source UNRESOLVED.** It is decoupled (`C7`) but
   not connected to a supply. The P4 likely feeds it from an internal LDO
   output — confirm which pin/rail on the Function-EV schematic and wire it.
   Leaving it unpowered breaks the camera (and possibly boot).

5. **ESP32-P4 strapping pins UNVERIFIED.** `BOOT_STRAP` is assumed to be
   GPIO35 and `SW2`/`R10` hang off it. Confirm the real download/boot strap
   pins and their required idle levels from the datasheet; add pulls so the
   chip boots from flash by default.

6. **Camera FFC pinout + CSI lane order/polarity UNVERIFIED.** `J4` uses an
   assumed Raspberry-Pi 15-pin camera pinout, and the CSI data/clock pair
   polarity (`CSI_D0P/N`, `CSI_D1P/N`, `CSI_CKP/N`) is a guess. Verify against
   both the RPi camera connector spec and the P4 CSI requirements; a swapped
   pair or polarity means no image.

7. **TP4056 charger + power path.** Confirm the TP4056 pinout (`U4`), the
   1.2 k PROG → ~1 A rate for your cell, and that grounding `TEMP` correctly
   disables the NTC. There is **no load-share**: the board runs from the
   battery; `D2` (DNP) is bench-power-only and must not be populated with a
   battery installed. Add a proper power-path FET if you want USB-powered
   bench operation while charging.

## High — verify, likely small fixes

8. **LGA/QFN sensor pad maps.** The pad→signal maps for `U6` (ICM-42688-P,
   on a generic DHVQFN-14 footprint), `U7` (SPL06-001), and `U8` (VL53L1X, on
   a placeholder `ST_VL53L0X` footprint) are reasoned but **not** checked pad
   by pad against datasheets, and the footprints themselves are approximate.
   Replace with the exact manufacturer land patterns and re-verify every pad.

9. **PMW3901 (`U9`) is a placeholder footprint** (`lib/strat.pretty/`). The
   COB land pattern is invented. Either draw the real PixArt land pattern, or
   leave `U9` unpopulated and use the `J3` 2×4 header with a CJMCU-3901 module
   (recommended for a first build — JLC reflow of the bare COB is unproven).

10. **Buck (`U5` SY8089) pinout + inductor.** Confirm the SOT-23-5 pin order
    and that `L1` (2.2 µH, 0805) meets the 2 A rating; the FB divider
    (`R4`/`R5`) targets ~3.42 V — retune to 3.30 V if desired.

11. **Crystal load caps (`C8`/`C9` = 10 pF)** are nominal; set them for the
    actual 40 MHz crystal's CL.

12. **CSI/DSI REXT values (`R11`/`R12` = 10 k)** are placeholders — use the
    guideline value. DSI is otherwise unused; terminate per the guideline.

13. **USB-C footprint** (`J2`, HRO TYPE-C-31-M-12) — confirm it matches the
    LCSC part you order; mirrored-contact variants exist.

14. **WS2812B from VBAT logic levels** — at VDD 3.7–4.2 V the 3.3 V data high
    is marginal-but-standard for 1S whoops. Fine in practice; noted for the
    record.

## Process notes

- Footprint substitutions chosen automatically are printed by `gen_pcb.py`.
- `make check` guarantees the board netlist and `firmware/.../board_pinmap.h`
  still match `design.py` after any edit to the database.
- After manual routing in KiCad, **regenerate the fab files from KiCad**, not
  from `export_fab.py` (which exports the unrouted board).
