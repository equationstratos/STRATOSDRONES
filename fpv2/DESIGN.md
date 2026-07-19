# Fr4n9-001 (fpv2) — design notes (deltas vs fpv85)

Common decisions (outdoor stack, analog video path, CRSF radio, shared AIO,
DShot/CRSF firmware specs): **see [`../fpv85/DESIGN.md`](../fpv85/DESIGN.md)** —
single source, not duplicated.

## Geometry

| Quantity | Value |
|---|---|
| wheelbase | **98 mm** (motors at ±34.65/±34.65) |
| props | **51 mm (2") tri-blade** |
| overall | 0.707·98 + 51 ≈ **120 mm** |
| motor mount | 3× M2 on Ø9 (1102 class) `TUNE` |
| prop plane | z ≈ 16 above plate (taller 1102 bells) |
| plate | 3.4 mm (bigger spans), feet 8 mm |

## Weight budget (targets, `TUNE`)

| Item | g |
|---|---|
| frame + canopy | 20-25 |
| 4× 1102 ~10000KV + 2" props | 26-30 |
| AIO + RX + cam + VTX | 13-19 |
| 2S 650 mAh + XT30 | 33-38 |
| **AUW** | **92-112** |

1102@2S on 2" tri-blades ≈ 65-80 g/motor → **T/W ≈ 2.4-3.0** — the
freestyle margin fpv85 doesn't have.

## What stays honest

Same M0 statement as fpv85: nothing printed/fabbed/flown; thrust numbers
are catalogue-class `TUNE`; the shared-board `VERIFY` gaps are fab-blocking.
