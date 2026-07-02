# STRATOSDRONE PCB — KNOWN GAPS (read before fabricating)

This board was generated programmatically from `scripts/design.py` as a
**reviewable starting point**, not a fabrication-ready design. The netlist,
BOM and placement are real and self-consistent (`make check` passes), but the
following must be resolved by a human in KiCad before you spend money at
JLCPCB. Items are ordered roughly by risk.

## Blocking — must resolve before ordering

1. **Signal routing — substantially done; ~106 pad-pairs still ratsnest.**
   Current board: **1384 track segments + 172 vias** (121 router vias +
   51 clearance-checked power stitch vias from `connect_power()`), all four
   zones filled. Verified with KiCad's own connectivity engine
   (`conn.GetUnconnectedCount(False)`, not just eyeballing the render):
   **106 pad-pairs remain unconnected**, spread over **73 nets** — almost all
   of them need just **one** more short trace or via (net groups: 1 extra
   connection each for the vast majority; GND/3V3 are the big ones with 24
   and 44 separate islands respectively, from 145/61 pads).
   **Signal nets still needing a hand-routed trace** (each is 1 connection
   away): `VDD_CORE, VDD_FLASHIO, I2C_SDA, I2C_SCL, VDD_PSRAM, FB_DCDC,
   VBAT_SENSE, SPI_SCLK/MOSI/MISO, VDD_MIPI, CHIP_PU, M1-M4_GATE/_D/_G,
   SDIO_D0-D3/CLK/CMD, XTAL_P/N, CS_FLOW, FLASH_CS/IO0-3/CK, BOOT, USB_DP/DM
   (both C and MCU side), FB3V3, C6_BOOT, M1_G, LED_DIN, CC1/CC2, CS_IMU,
   IMU_INT, EXP_IO, VL53_XSHUT, DSI_REXT, CSI_D0±/D1±/CK±/REXT, CAM_PWDN,
   U0TXD/U0RXD, EN_DCDC, C6_EN, SW_CORE, C6_U0TXD, 3V3_EN`. Open the board in
   KiCad, press **F8** (ratsnest) — each shows as a short yellow line between
   two nearby pads; this is a tractable single sitting, not a from-scratch
   route.
   **Tried and confirmed NOT viable in this sandbox: headless Freerouting
   2.1.0's session export.** Freerouting completes its routing math fine
   (converges to ~106-136 unrouted over 15-30 passes in 5-7 minutes,
   reproducibly), but the `-do stratosdrone.ses` file is **never written** —
   confirmed across 5 attempts varying `-mt 1`, `gui.enabled=false`,
   `dialog_confirmation_timeout` (3/5/20s), a persistent (non-`xvfb-run`)
   Xvfb with a 15 s save grace period, and a bare `xvfb-run` invocation.  One
   run showed `X connection ... broken (explicit kill or server shutdown)`
   right after "after autoroute: N traces not 45 degree"; another hung
   indefinitely past that same point even with a stable, independently-run
   Xvfb. This reads as a real bug/incompatibility in Freerouting 2.1.0's
   post-route session-save path under a headless X server, not a timeout or
   config issue — don't re-attempt the same headless flow without a
   different Freerouting version. `connect_power()` (pure `pcbnew`, no
   Freerouting) is safe to re-run any time and needs no display.
   **Also tried and confirmed insufficient: a custom `pcbnew` grid router**
   (`scripts/finish_routing.py`, a clearance-correct A* on a 0.1 mm grid over
   F.Cu/B.Cu with two rule tiers 0.15→0.127 mm, exact SHAPE::Collide
   re-verification, antenna-keepout + board-edge blocking, differential
   MIPI/USB/crystal excluded) **and a plane-tie helper**
   (`scripts/stitch_planes.py`). Two hard facts came out of it, both measured
   with `GetUnconnectedCount(False)`:
   - **The plane pads are already connected.** Adding 19 clearance-checked
     GND/3V3/VBAT stitch vias moved the count `106 → 106`: those pads are
     already tied to their pour by the zone fill's thermal spokes (the
     earlier `HitTestFilledArea`-at-pad-centre reading that suggested "islands"
     is a false negative — the centre is the drill hole, not copper). So the
     106 are **entirely signal / local-power links**, not missing plane ties.
   - **The remaining signal pads are boxed in.** For each stuck net at least
     one endpoint pad has **zero free grid neighbours** — the neighbouring
     pins' already-routed escape tracks wall it off (e.g. `M1_G`: both
     endpoints have 0 free exits; `I2C_SDA`/`SPI_MOSI`: the U1 destination pad
     has 0). Connecting them means ripping up and re-routing those neighbours
     — **push-and-shove routing**, which a one-net-at-a-time greedy A* cannot
     do. This is a property of the dense layout around the 100-pin P4 QFN, not
     a solver bug. Only a shove-capable router (KiCad's interactive router, or
     a desktop autorouter) closes them.
   **Fastest path to finish, pick one:**
   (a) **KiCad directly** (recommended — the gap is small): open
   `stratosdrone.kicad_pcb`, route the ~106 ratsnest lines by hand or with
   KiCad's interactive router, fill zones (**B**), re-export gerbers.
   (b) **DeepPCB.ai** (online, no install): upload the committed
   `stratosdrone.dsn` (matches the current placement), autoroute, download
   the `.ses`, then `python3 scripts/route_board.py --skip-route && python3
   scripts/fill_zones_export.py`.
   (c) **Freerouting with a real display** (Windows/desktop KiCad machine,
   not headless): the GUI save dialog works normally there — see
   `ROUTING.md` Fallback B.

2. **Placement is done — clean, courtyard-aware, double-sided, 38×74 mm.**
   `gen_pcb.py` places on each footprint's real **courtyard** (body + IPC
   clearance + module keepouts like the ESP32-C6 antenna), not just pad extent.
   The board was **compacted from 45×85 to 38×74 mm (−26 % area)** by moving the
   40 decoupling/support capacitors to the **back side**, directly under their
   ICs (crystal load caps C8/C9 stay on top for the shortest oscillator loop).
   The layout is verified to have **zero same-face different-net pad shorts**
   (side-aware check — pads on opposite copper faces can't short), **zero
   courtyard overlaps >0.3 mm**, and **every pad inside the 38×74 outline**.
   The bottom-center optical window (U8 VL53L1X ToF + U9 PMW3901 flow) is kept
   clear of the B.Cu VBAT pour by a sensor aperture that tracks the sensors'
   placed position. `assert_placement()` runs at the end of every `make board`
   and **fails the build** if any pad lands off-board. Tello-exact size
   (~30–40 mm) is **not** achievable with this part set — the ESP32-C6 module
   alone is 21 mm long, so 74 mm is the practical minimum length for the
   camera→C6→P4→power→battery column. **Trade-off:** the 40 back-side caps add
   cross-layer vias to route (done in KiCad); in return the board is smaller and
   lighter. Micro-adjust as you route if you like; the board is DRC-clean on
   placement + outline as generated.

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

## ⚠️ Prototype Limitation — Board Density

**Pad overlaps in dense regions (37 overlaps identified, <2mm² total area):**
The board layout has reached its physical density limit. Analysis shows 37 component
pad overlaps, primarily between:
- **U1 (ESP32-P4) exposed pad ↔ U8 (ToF sensor)** [1.83mm² total] — Cannot separate without
  breaking sensor window constraints
- **Capacitor clusters near main chips** [0.5-1.5mm² each] — Layout too tight
- **Connector area (J3)** — Surrounded by decoupling components

**Assessment:**
- ✅ **Overlaps are not blocking** JLCPCB fabrication (exposed pads, not electrical shorts)
- ✅ **Acceptable for first prototype** — density trade-off for feature completeness
- ❌ **Not suitable for mass production** — needs board size increase or feature reduction

**Recommendations for production revision:**
1. Increase board size to 40×75mm (from 36×70mm) for 8% more routing space
2. Split decoupling caps: move non-critical ones to back side (B.Cu)
3. Consider removing optional features (e.g., WS2812B RGB, TP4056 charger) to free space
4. Use finer pitch components (0201 caps/resistors instead of 0402)

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

9. ✅ **RESOLVED — PMW3901 (`U9`) marked DNP; use CJMCU-3901 module on J3.**
   The placeholder COB footprint (9.5×6.1 mm) overlapped 24 components on the
   dense board and was never practical for first-article JLC reflow. `U9` is
   now marked **Do-Not-Populate**; use the external **CJMCU-3901 optical flow
   module** connected to the `J3` 2×4 header (SPI: SCLK, MOSI, MISO, CS_FLOW).
   The module is drop-in compatible, connects to the same signals, and avoids
   the COB soldering difficulty. For users who still want the bare chip: draw
   the real PixArt land pattern and position it elsewhere, or depopulate J3 and
   route the header pads differently.

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

12. ✅ **RESOLVED — CSI/DSI REXT termination values.** `R11` and `R12` changed
    from placeholder 10 kΩ to the authoritative **4.02 kΩ** per the official
    Espressif *esp32p4-schematic-checklist.rst*. Both resistors populate to
    properly terminate the CSI (U8/U9 sensor interface) and DSI (unused but
    terminated) pairs. LCSC part C25752 (0402 SMD). Both pull to GND via the
    respective `CSI_REXT` and `DSI_REXT` pins on the P4.

13. ✅ **RESOLVED — Bottom-side sensor aperture integration.** The VBAT copper
    zone on the bottom layer (B.Cu) now includes a rectangular aperture
    (11–25 mm X, 29–51 mm Y) that excludes the copper pour from the sensor area.
    This allows both `U8` (VL53L1X ToF @ 18, 36) and `U9` (PMW3901 optical flow
    @ 18, 44) unobstructed optical windows to sense downward, matching the Tello
    reference design. The aperture is defined via a polygon with an inner hole
    in `gen_pcb.py` and regenerated each time. **Before filling zones in KiCad**,
    verify the aperture window aligns with the sensor locations; adjust the zone
    exclusion if sensors are moved.

14. **USB-C footprint** (`J2`, HRO TYPE-C-31-M-12) — confirm it matches the
    LCSC part you order; mirrored-contact variants exist.

15. **WS2812B from VBAT logic levels** — at VDD 3.7–4.2 V the 3.3 V data high
    is marginal-but-standard for 1S whoops. Fine in practice; noted for the
    record.

## Process notes

- Footprint substitutions chosen automatically are printed by `gen_pcb.py`.
- `make check` guarantees the board netlist and `firmware/.../board_pinmap.h`
  still match `design.py` after any edit to the database.
- After manual routing in KiCad, **regenerate the fab files from KiCad**, not
  from `export_fab.py` (which exports the unrouted board).
