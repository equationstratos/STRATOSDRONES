# Hardware verification ledger

Honest record of what was verified versus assumed while generating the PCB
(`hardware/pcb/`). "Verified" means checked against a datasheet, the Espressif
KiCad library, or an official reference design during development. "Assumed"
means a reasoned engineering choice that a human must confirm before
fabrication — these are the actionable items, cross-referenced in
`hardware/pcb/KNOWN_GAPS.md`.

## Verified

| Item | How |
|---|---|
| ESP32-P4 QFN pad → signal map (104 pins + EP) | Extracted from the official Espressif `ESP32-P4` KiCad symbol (vendored in `lib/`) |
| ESP32-C6-MINI-1 pin → signal map (53 pads) | Extracted from the official Espressif `ESP32-C6-MINI-1` symbol |
| C6 SDIO-slave pins (CLK=GPIO19, CMD=GPIO18, D0–3=GPIO20–23) | ESP32-C6 fixed SDIO-slave assignment; mapped to module pads 24–29 |
| ESP32-P4 has a hardware H.264 encoder (1080p30) + MIPI-CSI + ISP | Espressif ESP32-P4 product page / TRM (June 2026) |
| ESP32-P4NRW32 (32 MB in-package PSRAM) in LCSC stock ~\$4.6 | LCSC C22387510 |
| Firmware GPIO map closes with no pin conflicts | `design.PINMAP` vs the P4 pad map; `check_consistency.py` |
| Board ↔ firmware pinmap consistency | `make check` (board nets == design == `board_pinmap.h`) |
| KiCad 7 footprint format incompatibility (P4 fp was v9) | Downgraded to v7; loads with 113 pads |

## Assumed — confirm before fabrication

| Item | Risk | Where |
|---|---|---|
| ESP32-P4 core DC-DC inductor/cap topology + values (`L2`,`C5`) | **High** — wrong = dead chip | KNOWN_GAPS #3 |
| `VDD_MIPI_DPHY` 2.5 V source (decoupled but unconnected) | **High** | KNOWN_GAPS #4 |
| P4 boot/download strap pins (assumed GPIO35) | **High** | KNOWN_GAPS #5 |
| Camera FFC pinout (assumed RPi 15-pin) + CSI lane order/polarity | **High** | KNOWN_GAPS #6 |
| TP4056 pinout, PROG=1.2 k → ~1 A, TEMP-to-GND disables NTC | Medium | KNOWN_GAPS #7 |
| ICM-42688-P LGA-14 pad map + footprint (generic DHVQFN-14) | Medium | KNOWN_GAPS #8 |
| SPL06-001 LGA-8 pad map (CSB=3V3 I2C, SDO→0x76) | Medium | KNOWN_GAPS #8 |
| VL53L1X 12-pad map + footprint (placeholder `ST_VL53L0X`) | Medium | KNOWN_GAPS #8 |
| PMW3901 COB land pattern (invented placeholder) | Medium — `J3` header fallback provided | KNOWN_GAPS #9 |
| SY8089 SOT-23-5 pinout + `L1` 2.2 µH rating; FB → ~3.42 V | Medium | KNOWN_GAPS #10 |
| 40 MHz crystal load caps (10 pF nominal) | Low | KNOWN_GAPS #11 |
| CSI/DSI REXT values (10 k placeholder) | Low/Medium | KNOWN_GAPS #12 |
| USB-C footprint matches ordered part | Low | KNOWN_GAPS #13 |
| LCSC part numbers for secondary parts (USB-C, JST, FFC, buttons, passives) | Low | `design.py` fields |
| esp-hosted P4↔C6 throughput/latency adequate for H.264 (≈36 Mbps measured vs 2–6 needed) | Low | plan risk #2 |
| 8520 motor thrust/stall at 1S (for T/W and FET sizing) | Low | bench test |

## Components requiring a working internet connection to re-verify at fab time

LCSC stock and exact footprint/pinout for: `J2` USB-C (C165948), `J1` JST-PH
(C160404), `J4` FFC-15 (C2884418), `SW1`/`SW2` buttons (C720477),
`U3` ESP32-C6-MINI-1 (C3013606), `U6` ICM-42688-P (C2840095). Re-pull these
from lcsc.com before placing the JLCPCB order.
