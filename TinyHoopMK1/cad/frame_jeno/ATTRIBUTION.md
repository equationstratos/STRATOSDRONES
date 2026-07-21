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
- **Changes made:** none to the geometry — the files are copied as-is. The
  viewer only *positions* them and adds our own separate meshes (motors,
  props, FC board, battery, screws, antenna whip, STRATOS logo) around them.
  `step_to_stl.py` is kept for anyone who wants to re-mesh the STEP instead.

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
