# JeNo Pocket V2 — attribution (CC-BY-4.0)

`JeNoPocket_V2.step` in this folder is the **JeNo Pocket V2** drone frame by
**WE are FPV**, used here under its original licence.

- **Author / source:** WE are FPV — https://www.printables.com/model/1704840-jeno-pocket-v2
  (project repository: https://github.com/WE-are-FPV/JeNo-Pocket-V2)
- **Licence:** Creative Commons Attribution 4.0 International (**CC-BY-4.0**)
  (the repo `LICENSE` is kept here alongside).
- **Files used (redistributed unmodified):**
  - `JeNoPocket_V2.step` — the frame CAD (01-FRAME).
  - `../stl/frame_real.stl` — WE are FPV's own `01-FRAME/JeNoPocket_V2.stl`,
    what the viewer renders as the frame.
  - `tpu/` — the real TPU parts from `02-TPU`: `arm_bumper.stl`,
    `back_bumper.stl`, `vtx_antenna_mount.stl`, `o4lite_mount.stl`.
- **Changes made:** none to the geometry — the files are copied as-is.
  - `parts/` holds the STEP **split into its individual solids** (bottom
    plate, camera cage, standoffs, camera) by `step_to_stl.py`, so each part
    can be shown / exploded on its own in the viewer. Same geometry, just
    separated per solid.
  - The viewer *positions* these and adds our own meshes (props, FC board,
    DOGCOM 3S 560 mAh battery, screws + grommets, LiPo capacitor, buzzer,
    GPS/compass, ELRS RX antenna and the motor phase cables) plus a
    **clean parametric top plate** (`../frame.scad` `jeno_top`) that keeps the
    JeNo top-plate envelope and lightening pattern **without the "JeNo"
    wordmark** — our own geometry, so nothing of theirs is altered.

## Other third-party files

- `parts/motor_1104.stl` — **Readytosky 1104-7500KV** motor model, provided by
  the project owner for a faithful motor render. Product geometry by
  Readytosky; used here for visualisation only.
- `dji_o4/o4_cam_head.stl`, `dji_o4/o4_airunit.stl`, `dji_o4/o4_antenna.stl` —
  the **DJI O4 Lite** camera head, air-unit board and antenna, split out of the
  single O4-Lite STEP supplied by the project owner: the camera head (ribbon
  trimmed), the small bare air-unit PCB (its ~450 micro-pads dropped for a
  light mesh), and the **single** antenna, routed into the rear TPU antenna
  mount. Product geometry © DJI; used here for visualisation only.
- `dji_o4/ghf411_aio.stl` — the **JHEMCU GHF411 AIO** flight controller, meshed
  from the STEP supplied by the project owner. It is the *ready-to-buy*
  Betaflight option; the viewer's "Électronique" button swaps it for the
  custom **STRATOS TINYHOOP AIO** and back. Product geometry © JHEMCU; used
  here for visualisation only.

## Why the real file is here

The TinyHoop MK1 keeps the JeNo Pocket V2 frame design (the owner's brief).
Earlier the frame was a *clean-room* parametric re-creation in
[`../frame.scad`](../frame.scad); the owner then supplied the genuine STEP, so
the **viewer now shows the real frame** for maximum fidelity. Both coexist:

- **`frame_jeno/JeNoPocket_V2.step`** — the real WE are FPV frame (CC-BY-4.0),
  what the viewer renders.
- **`../frame.scad`** — our own STRATOS-branded parametric variant
  (printable STL + carbon DXF), independent geometry, for those who want to
  cut/print the Stratos version.

Per CC-BY-4.0: this credit, the licence, and the "unmodified STEP / meshed
for the viewer" note satisfy the attribution and change-indication terms.
Thank you WE are FPV — please support them and buy their carbon.
