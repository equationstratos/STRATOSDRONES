# fpv85 hardware — the shared STRATOS FPV AIO + off-board modules

The flight controller is the **shared AIO board**:
[`../../hardware/pcb_fpv/`](../../hardware/pcb_fpv/) (32×32, whoop 25.5
mount, 2S, 4× integrated BLHeli_S ESC, CRSF socket, VTX/cam pads). One
board serves fpv85 AND fpv2 — order once, build either.

## Module BOM (per drone, indicative €)

| Item | Spec | ~€ |
|---|---|---|
| 4× motors | 0802-class ~14000KV, 3×M1.4 Ø6.6 mount | 32-45 |
| 4× props | 40 mm tri-blade (1.5 mm shaft) | 3 |
| ELRS RX | any CRSF ExpressLRS 2.4G (EP1/RP1-class) | 5-12 |
| Analog cam | nano 14 mm, 5V | 8-15 |
| VTX | 25-400 mW 5.8G, SmartAudio, 5V | 10-20 |
| Battery | 2S 450 mAh, XT30 | 8-12 |
| Charger | USB-C 2S balance (off-board — no charger on the AIO) | 10 |
| Hardware | M2 screws, strap, grommets | 3 |

Radio side: any ELRS TX module/handset (Boxer, Pocket, Zorro…).
Goggles: any analog 5.8 GHz.
