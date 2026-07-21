# STRATOS TINYHOOP AIO — known gaps (read BEFORE ordering)

Honest ledger for the TinyHoop MK1 board (Fr4n10-001). Same discipline as
[`../pcb_fpv/KNOWN_GAPS.md`](../pcb_fpv/KNOWN_GAPS.md), which this board
**inherits in full** — it is defined by importing that design database and
adding deltas. Everything in the FPV AIO ledger (§1-6 there) still applies:
the AP63203/05 bucks, the EFM8/FD6288T/AO3400 ESC stage, the WS2812-on-5V
data VIH, the P4 strapping pins, the camera FFC, the crystal caps.

The board is **M0**: netlist complete + self-checked (`python3
scripts/design.py`), geometry/routing/fab from the KiCad stage only (CI
container or desktop KiCad).

## New to this board (on top of the inherited FPV AIO gaps)

### A. FAB-BLOCKING — SX1262 LoRa module pad map (VERIFY)

`U12` is an **Ebyte E22-900M22S** castellated module. Its 17-pad map
(GND/BUSY/DIO1/DIO2/DIO3/3V3/MISO/MOSI/SCK/NSS/RST/TXEN/RXEN/ANT) was written
from the module's **published pinout, not a datasheet-in-hand reflow trial**.
Verify against the E22-900M22S datasheet before `make fab`, including:
- which castellations are the SPI four vs the two RF-switch enables (TXEN/RXEN
  are driven by the module's own logic on some variants — confirm whether the
  P4 must toggle them or `DIO2_as_RF_switch` handles it; the firmware assumes
  DIO2 RF switching);
- the ANT pad + a matched u.FL launch and an **antenna keepout opposite the
  C6 Wi-Fi antenna edge** (two 2.4 GHz-ish emitters — actually 868 vs 2400,
  but keep them apart);
- the module is **optional/DNP**: a solo (non-swarm) build leaves it off.

### B. FAB-BLOCKING — ESC FET current at 1203-1303 / up to 3S

The inherited ESC stage was sized for 0802/1102 on 2S. TinyHoop runs
**1203-1303 on 2S-3S**, higher stall/burst currents. Re-check AO3400A SOA and
phase copper for ~15-20 A per motor, or swap to a higher-current FET (keep the
SOT-23 land or move to a 3×3 mm power package). Fab-blocking.

### C. 5 V budget vs DJI O4 Lite

The AP63205 5 V rail is **2 A**. Analog VTX (25-400 mW) + nano cam + ELRS RX
fit comfortably. A **DJI O4 Lite** peaks well beyond that on 5 V — power it
from the LiPo directly (DJI allows 2S-3S on the O4 Lite input) rather than the
5 V rail, or add a second AP63205 phase. Documented, not auto-enforced.

### D. VBAT divider is now /5

`R7/R33/R34/R35` (4×100k) + `R8` (100k) → /5, so 12.6 V (3S full) → 2.52 V at
the ADC. The firmware `VBAT_DIVIDER` (board_pinmap_tinyhoop.h) is 5.0f — keep
the two in sync (the generator does). 3S cutoff / cell-count detection is a
firmware task (M2).

### E. Placement density 34×34

The board is grown to **34×34** (mount pattern 25.5 unchanged) to fit the FPV
AIO's 4 ESC stages + P4 + C6 **plus** the re-added PMW3901/VL53L1X (bottom),
the SX1262 module + u.FL, and the GPS connector. `assert_placement()` in the
CI `board-tinyhoop` job is the gate — if it still fails, grow to 36×36 (both
the printed proto and the carbon plate absorb it; the mount stays 25.5).

### F. EU868 duty-cycle compliance

The default channel 869.525 MHz sits in the 10 % duty sub-band. The ground
dongle is TX-heavy (beacons + commands); the drones are TX-light (telemetry).
At the documented ~6-drone ceiling and 2 Hz telemetry this is within limits,
but **any change to beacon rate or telemetry rate must be re-checked against
ETSI EN 300 220-2** before field use outside a test licence.

## Firmware status (this board)

Unlike the FPV AIO (firmware specified-not-implemented), the TinyHoop
firmware **is implemented and CI-compiled**: `outputs_dshot.c`, `crsf_task.c`,
`sx1262.c`, `lora_task.c`, selected by `-DSTRATOS_BOARD_TINYHOOP`. It has
**not run on hardware** — the RMT timings, SX1262 command sequence and PA
config, and CRSF UART pins are all VERIFY at M2 bring-up. The portable logic
(`fc_crsf`, `fc_lorap`, mode manager, show executor) is host-tested.
