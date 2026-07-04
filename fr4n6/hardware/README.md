# Fr4n6-001 hardware — "Stratos Bolt" board plan

Bolt-style concept: **our board is the flight controller + power backbone;
propulsion is a standard, replaceable 4-in-1 ESC stack.** One firmware
(`fc_core`) across Fr4n7-001 and Fr4n6-001.

## Block diagram

```
                 2S–6S battery (XT60)
                        │
              ┌─────────┴──────────┐
              │  power tree        │  reverse-pol prot · ideal-diode w/ USB-C
              │  VBAT sense (div)  │  current shunt + amp (telemetry)
              │  buck 5V/3A        │──► companion rail (CM4/Jetson deck, LEDs)
              │  buck/LDO 3V3      │──► logic
              │  9V pad (option)   │──► analog VTX bay
              └─────────┬──────────┘
                        │ VBAT
   ┌────────────────────┼───────────────────────────────┐
   │        4-in-1 ESC socket (30.5×30.5, 8-pin)        │
   │  VBAT GND M1 M2 M3 M4 TLM CUR                      │──► 4 × 2207 motors
   └────────────────────┬───────────────────────────────┘
                        │ M1–M4 = DSHOT600 (P4 RMT)   TLM/CUR → UART/ADC
┌───────────────────────┴────────────────────────────────────────────┐
│                    ESP32-P4  (flight + vision)                     │
│  fc_core 1 kHz · Tello SDK 2.0 UDP · MIPI-CSI OV5647 → HW H.264    │
│  SPI: ICM-42688-P (IMU)  PMW3901 (flow)                            │
│  I2C: SPL06-001 (baro)  VL53L1X (ToF)  compass  deck EEPROM        │
│  UART: GPS port · ESC telemetry · companion                        │
│  RMT: DSHOT ×4 · WS2812 LED ring                                   │
│  USB-C · microSD pads (blackbox) · boot/reset                      │
└───────────────┬────────────────────────────────────────────────────┘
                │ SDIO (esp-hosted, same as Fr4n7)
        ┌───────┴────────┐
        │   ESP32-C6     │  Wi-Fi 6 AP/STA · 192.168.10.1 · swarm STA mode
        └────────────────┘

  Stratos Deck connector (2×10, stackable):
  3V3 · 5V · VBAT · I2C · SPI · UART×2 · GPIO×6 · DETECT(EEPROM) · GND
```

## Part selection (v0)

| Block | Part | Why |
|---|---|---|
| Flight/vision MCU | **ESP32-P4** (P4NRW32) | proven on Fr4n7; dual RISC-V 400 MHz, MIPI-CSI + HW H.264 1080p30 — no companion needed for video |
| Radio | **ESP32-C6-MINI-1** | Wi-Fi 6; same esp-hosted SDIO link as Fr4n7 |
| IMU | **ICM-42688-P** (SPI) | same driver as Fr4n7 (`firmware/components/drivers/icm42688.c`) |
| Baro | **SPL06-001** | same driver |
| Flow / ToF | **PMW3901 · VL53L1X** | DEXI-style indoor positioning; same drivers |
| Compass | IST8310 / QMC5883L pads | outdoor heading (GPS missions) |
| GPS | **JST-GH port** (UART + I2C) | M10 modules; optional |
| ESC | **external 4-in-1**, 30.5×30.5, BLHeli_32/AM32, ≥45 A burst | industry standard, classroom-replaceable; keeps 30–50 A off our board (Bolt's integrated PDB ≈ 8 A/motor is the cautionary tale) |
| Motors | **2207**, 1750 KV (4S) / 1300 KV (6S) | DEXI-5 class (22×7 stator, 1980 KV on 6S Li-ion) |
| Power | reverse-pol FET, shunt+amp, buck 5 V/3 A, 3V3, optional 9 V | 2–6S input window; companion rail; VTX rail |
| Camera | **OV5647** CSI (same as Fr4n7) + 20×20 FPV bay | Tello-protocol video stays; analog/HD FPV optional |
| LEDs | WS2812 output (ring in ducts) | DEXI-style orientation ring |
| Expansion | **Stratos Deck** 2×10 + EEPROM detect | Bolt-style auto-detected decks |
| USB | USB-C on P4 | flash/logs |

## Electrical budget (v0 estimates — validate at M2)

- Logic + radio + camera: ≤ 2.5 W (Fr4n7-measured class)
- Companion rail: 5 V × 3 A = 15 W budget (CM4 + accessories)
- Motors (4S 1500 mAh, 2207@1750 KV, 5×4.3×3): ~80–350 W flight envelope —
  entirely through the ESC stack, not our copper
- VBAT sense: 1% divider to P4 ADC; current: 0.5 mΩ shunt + INA180-class amp

## PCB plan (M2)

Follow the Fr4n7 pipeline: single `design.py` source of truth →
generated KiCad netlist/placement, BOM/CPL for assembly, and an honest
`KNOWN_GAPS.md`. Board outline 42×42 mm (30.5×30.5 M3 stack pattern),
4-layer, USB-C edge, camera FFC forward, downward sensor bay, deck header
on top. The Fr4n7 board's lessons that carry over verbatim: P4 core
DC-DC topology, C6 antenna keepout, sensor apertures, strap pins ledger.

## Open questions (tracked, not hidden)

1. DSHOT600 timing on P4 RMT — prototype at M2 (fallback: DSHOT300 /
   OneShot125, both fine for 5" education).
2. ESC telemetry parsing (KISS/BLHeli UART TLM) into `battery?`-style SDK
   extensions.
3. 6S Li-ion pack (DEXI-style endurance) vs 4S LiPo default — power tree
   is sized for both; motor KV differs per pack (see motors row).
4. Companion deck power sequencing (CM4 boot vs battery sag on punch-outs).
