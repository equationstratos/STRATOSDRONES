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

2. **Placement is done; refine as you route.** `gen_pcb.py` now does
   anchor-based placement with collision avoidance: decoupling caps ring the
   P4, each FET has its gate resistors + flyback at its corner, crystal caps
   sit on the crystal, and the layout is verified to have **zero
   copper-pad overlaps**. The bottom-center window (U8 VL53L1X + U9 PMW3901)
   is kept clear. You may still want to micro-adjust during routing (e.g. tuck
   a cap to the exact power pin it serves), but the board is routable as
   generated.

3. ✅ **RESOLVED — ESP32-P4 core DC-DC topology + values.** The previous
   revision was **chip-fatal in three ways**, all confirmed against the official
   *ESP32-P4 Hardware Design Guidelines* (`esp32p4-ldo-dcdc.inc`) and its
   TLV62569 rev-3.0 reference schematic: (a) the CPU core pins `VDD_HP_0/2/3`
   were tied directly to `3V3`, i.e. ~2.75× overvoltage on the core — instant
   dead chip; (b) `EN_DCDC` was hard-tied to `3V3` instead of driving a DC-DC
   enable; (c) there was **no external DC-DC at all** — `L2`/`C5` were bare
   passives on a meaningless `VDD_DCDCC` switch-node net, and `FB_DCDC` was
   shorted onto `VDD_CORE`. Per the guideline, `VDD_HP` is **not** self-generated:
   it requires an external buck whose `EN`/`FB` are driven by the P4's own
   `EN_DCDC`/`FB_DCDC` pins, while `VDD_DCDCC`/`VDD_LDO` are ordinary 3.0–3.6 V
   supply *inputs*. Implemented the Espressif-verified **TLV62569** reference
   circuit exactly: `U10` (TLV62569DBVR, C141836, SOT-23-5) with VIN←3V3 (`C36`),
   `SW`→`L2` 2.2 µH (Sunlord SWPA3015S2R2MT, C43389, 3×3 mm/2 A)→`VDD_CORE`,
   `C5` 22 µF output, divider `R30`/`R31` (top→`FB_DCDC`, bottom→GND) with
   feed-forward `C37` across `R30`, `EN_DCDC`→`U10.EN`, `FB_DCDC`→`U10.FB`. The
   core pins `VDD_HP_0/2/3` now tie to the regulated `VDD_CORE` rail and
   `VDD_DCDCC` to `3V3`. Divider is `453k/453k` (vs the reference 499k/499k): the
   **1:1 ratio is what sets the output**, so this reproduces Espressif's intended
   core voltage *by construction* (`Vout = 2·Vfb`) using a part already on this
   board; input cap is 10 µF (vs 4.7 µF) and feed-forward cap 20 pF (vs
   22 pF), both electrically non-critical. Per the guideline the FB resistor and
   capacitor are populated (required for chip rev v3.0+). Verified pad-by-pad in
   `pcbnew`: all seven new/repurposed parts and all four P4 core pins map to the
   intended nets, no orphan `VDD_DCDCC` net remains.

4. ✅ **RESOLVED — `VDD_MIPI_DPHY` source + the whole internal-LDO rail block.**
   Investigating the MIPI supply surfaced a cluster of latent power bugs around
   the P4's internal LDO outputs, all now fixed against the official ESP32-P4
   schematic checklist (`schematic-checklist-esp32p4.rst`) and the ESP32-P4-
   Function-EV-Board reference. The P4 has four internal LDOs whose **outputs**
   (`VDDO_FLASH`, `VDDO_PSRAM`, `VDDO_3`, `VDDO_4`) the previous revision tied
   straight to `3V3` — which both fights the regulators and, for PSRAM, put
   **3.3 V on the 1.95 V-max `VDD_PSRAM_0/1` pins** (would damage the in-package
   PSRAM). Fixes: (a) `VDDO_3` (a configurable 0.5–2.7 V LDO) now feeds
   `VDD_MIPI_DPHY` on the `VDD_MIPI` rail — firmware sets LDO channel 3 to 2.5 V;
   decoupled with 1 µF + 0.1 µF (`C7`/`C42`; the checklist's extra 10 nF HF cap
   is noted but omitted for lack of a verified 0402 part). (b) `VDDO_PSRAM` (1.8 V)
   now ties to `VDD_PSRAM_0/1` on a dedicated `VDD_PSRAM` rail (1 µF + 0.1 µF).
   (c) `VDDO_FLASH` (default 3.3 V) ties to `VDD_FLASH_IO` **and** the external
   flash VCC on a shared `VDD_FLASHIO` rail (1 µF + 0.1 µF; flash-IO pull-ups
   `R13–R15` re-referenced to it). (d) `VDDO_4` (unused) left unconnected. Also
   confirmed the **NRW32 = in-package PSRAM only, NO in-package flash** (the
   reference board pairs the very same `ESP32-P4NRW32X` with an external
   GD25Q128), so the on-board W25Q128 boot flash is correct, not a bus conflict.
   **Bonus — full pinout audit:** the entire 105-pin P4 map was diffed against
   Espressif's official KiCad symbol (`espressif/kicad-libraries`); every signal
   matches (incl. `VDDO_FLASH`=71, `VDD_DCDCC`=77, `FB_DCDC`=78, `GND`=EP pin
   105, no `VDD_HP_1`), so the DC-DC fix in item 3 is on the correct pads. All
   rails re-verified pad-by-pad in `pcbnew`.

5. **ESP32-P4 strapping pins UNVERIFIED.** `BOOT_STRAP` is assumed to be
   GPIO35 and `SW2`/`R10` hang off it. Confirm the real download/boot strap
   pins and their required idle levels from the datasheet; add pulls so the
   chip boots from flash by default.

6. **Camera FFC pinout + CSI lane order/polarity UNVERIFIED.** `J4` uses an
   assumed Raspberry-Pi 15-pin camera pinout, and the CSI data/clock pair
   polarity (`CSI_D0P/N`, `CSI_D1P/N`, `CSI_CKP/N`) is a guess. Verify against
   both the RPi camera connector spec and the P4 CSI requirements; a swapped
   pair or polarity means no image.

7. ✅ **RESOLVED — TP4056 charger pinout + PROG rate.** `U4`'s pin map had two
   real bugs: pin 6 (`STDBY`, open-collector) was shorted straight to `VBAT`
   instead of being the status output, and pin 8 (`CE`, enable input) was
   aliased to `STDBY_N` instead of being driven at all. Re-verified the full
   pinout against the Nanjing Top Power TP4056-42-ESOP8 datasheet pin table
   and an independent KiCad symbol (1 TEMP, 2 PROG, 3 GND, 4 VCC, 5 BAT,
   6 STDBY, 7 CHRG, 8 CE, EP=GND); fixed pin 6 → `STDBY_N`, pin 8 → tied to
   `VBUS` (always-enabled charging, matching the standard no-software-control
   reference circuit). `R3` = 1.2 kΩ on `PROG` gives `1200/R(kΩ) = 1.0 A`,
   an appropriate ≈0.9 C rate for the 1S 1100 mAh pack in the BOM. Grounding
   `TEMP` to disable the NTC is correct per datasheet. Remaining by-design
   caveat (not a gap): there is **no load-share** — the board runs from the
   battery, and `D2` (DNP) is bench-power-only and must not be populated with
   a battery installed. Add a proper power-path FET if USB-powered bench
   operation while charging is wanted.

## High — verify, likely small fixes

8. ✅ **LGA/QFN sensor pad maps — all three RESOLVED.** All sensor pad→signal
   maps (`U6`, `U7`, `U8`) are now re-verified pad-by-pad against datasheets
   and/or real reference designs using the same footprints. `U7` and `U8`
   already use KiCad's official manufacturer land patterns; only `U6` still
   sits on a generic substitute footprint (geometry only, netlist is correct
   — see its sub-bullet).
   - ✅ **`U8` VL53L1X — RESOLVED.** Moved to KiCad's official
     `Sensor_Distance:ST_VL53L1x` land pattern and rewired pad-by-pad to the ST
     datasheet (1 AVDDVCSEL=3V3, 2 AVSSVCSEL=GND, 3/4/6/12 GND, 5 XSHUT,
     7 GPIO1=INT, 8 DNC floating, 9 SDA, 10 SCL, 11 AVDD=3V3). The previous
     map used the wrong `ST_VL53L0X` footprint and had supply/I²C pins on the
     wrong pads. *Still TODO: confirm LCSC C2970716 part rotation for the JLC
     CPL.*
   - ✅ **`U6` ICM-42688-P — RESOLVED (pinout; footprint geometry still
     generic).** The previous map had the chip's two real power pins
     backwards: `VDDIO` (real pin 5) and `VDD` (real pin 8) were both tied to
     **GND**, so the IMU could never power up at all, while the host's
     SPI_SCLK/SPI_MOSI/CS_IMU nets were wired to reserved/no-connect pads (2,
     3, 1) and the chip's real `AP_CS`/`AP_SCLK`/`AP_SDI` pins (12/13/14) were
     tied to GND/3V3/GND instead of the host signals. Re-verified the full
     14-pin LGA pinout against the TDK InvenSense DS-000347 pin table and an
     independent, manufacturer/IPC-7351B-tagged KiCad symbol (1 AP_SDO/AP_AD0,
     2/3/7/10/11 RESV, 4 INT1, 5 VDDIO, 6 GND, 8 VDD, 9 INT2/FSYNC/CLKIN,
     12 AP_CS, 13 AP_SCLK, 14 AP_SDI) and rewired every pad: SPI_MISO->1,
     IMU_INT->4, 3V3->5/8, GND->2/3/6/7/9/10/11, CS_IMU->12, SPI_SCLK->13,
     SPI_MOSI->14, and the footprint's pad 15 (generic exposed/heatsink pad,
     not present on the real LGA-14) grounded as the conservative default
     for unused copper. *Still TODO: replace the generic DHVQFN-14 substitute
     with the real LGA-14 land pattern (pad geometry only, not netlist).*
   - ✅ **`U7` SPL06-001 — RESOLVED.** Re-verified pad-by-pad against a real
     reference design using the *identical* official KiCad footprint
     (iNavFlight/hardware `BARO1/SPL06.kicad_pcb`): 1 GND, 2 SDO (addr
     select), 3 SDA, 4 SCL, 5 CSB, 6 VDDIO, 7 GND, 8 VDD. The previous map
     had real pin 6 (`VDDIO`) tied to **GND** (IO supply dead), real pin 3
     (`SDA`) hard-wired straight to 3V3 (a bus short the instant anything
     pulled the shared SDA line low), and the host's `I2C_SDA` net wired to
     real pin 1 (`GND`) — shorting the shared I²C bus to ground through this
     chip, which would have broken every other device on that bus, not just
     this sensor. Fixed: GND->1/2/7, `I2C_SDA`->3, `I2C_SCL`->4, 3V3->5/6/8
     (`SDO` tied low for the documented 0x76 address; `CSB` tied high for
     I2C mode). Footprint (`Package_LGA:Bosch_LGA-8_2x2.5mm_P0.65mm_
     ClockwisePinNumbering`) is KiCad's official land pattern and matches
     the reference design, so no geometry concern here.

9. **PMW3901 (`U9`) is a placeholder footprint** (`lib/strat.pretty/`). The
   COB land pattern is invented. Either draw the real PixArt land pattern, or
   leave `U9` unpopulated and use the `J3` 2×4 header with a CJMCU-3901 module
   (recommended for a first build — JLC reflow of the bare COB is unproven).

10. ✅ **RESOLVED — Buck (`U5` SY8089) pinout + inductor.** SOT-23-5 pinout
    (1 EN, 2 GND, 3 LX/SW, 4 IN/VIN, 5 FB) confirmed against the Silergy
    application note — matched the existing map exactly, no rewiring needed.
    `L1`'s value field said "2.2 µH" but the chosen LCSC part (`C408412`) is
    actually a Sunlord MWSA0503S-100MT, **10 µH** (2.8 A min saturation) —
    JLCPCB assembly stuffs whatever the LCSC code resolves to regardless of
    the printed value, so the real board would have shipped with 10 µH
    either way. Corrected the value field to match; 10 µH is higher than the
    ~2.2–4.7 µH typical for this IC class at 2A/~1.5 MHz (lower ripple,
    slower transient response) but not a stability or current-rating issue
    — swap for a 2.2–3.3 µH/≥2.5 A 0805 part if faster transient response is
    wanted. FB divider (`R4`=453k/`R5`=100k) computes to 0.6×(1+453/100) =
    **3.318 V**, not the ~3.42 V this item previously claimed (stale note) —
    already within 0.5% of the 3.30 V target, no retune needed.

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
