# Fr4n9-001 (fpv2) — the outdoor 2" FPV (98 mm, 2S brushless)

The **2" big sibling** of [`../fpv85/`](../fpv85/) (Fr4n8-001): same design
language, same shared AIO board, more muscle — the freestyle one. Radio
ExpressLRS, analog 5.8 GHz video, brushless 2S, fully programmable
(ESP32-P4 + C6 + `fc_core`, Tello-SDK compatible).

## Positioning

| | Fr4n8-001 (fpv85) | **Fr4n9-001 (this)** |
|---|---|---|
| Wheelbase / props | 65 mm / 40 mm | **98 mm / 51 mm (2") tri-blade** |
| Overall | ≈ 86 mm | **≈ 120 mm** |
| Motors | 0802 ~14000KV | **1102-class ~10000KV 2S** (3×M2 Ø9) |
| Battery | 2S 450 mAh | **2S 650 mAh XT30** |
| AUW target | 65-78 g | **90-110 g** |
| Board / radio / video | STRATOS FPV AIO · ELRS CRSF · analog 5.8G | **identical (shared)** |

Everything else — charter rationale, inspirations, the analog FPV chain,
the `outputs_dshot.c` + `crsf_task.c` firmware specs — is **common with
fpv85**: see [`../fpv85/README.md`](../fpv85/README.md) and
[`../fpv85/DESIGN.md`](../fpv85/DESIGN.md). This folder documents only what
differs.

## Layout

```
fpv2/
  README.md DESIGN.md ROADMAP.md
  cad/       frame.scad (98 mm scale of the fpv85 one — keep in sync), stl/, preview/
  viz/       viewer + playground simulator (same generator, fpv2 meshes)
  hardware/  shared AIO pointer + module BOM deltas
  firmware/  = fpv85 (shared specs)
  sim/       SDF targets (mass 0.100, arm 0.0346, kT ~0.75)
```

**See it in 3-D** — [`viz/drone_viewer.html`](viz/) (`?playground=1` = simulator).

## Status

**M0 — concept & scaffold.** Not printed, not flown; TUNE tags + shared
board gaps apply (`hardware/pcb_fpv/KNOWN_GAPS.md`).
