# TinyHoop MK1 — CAD (clean-room JeNo Pocket V2, 2.5" wide-X)

`frame.scad` is a single parametric source that exports **two** things:

- **STL** — a printable **prototype** (PLA-CF / PETG) for dry-fitting motors,
  board, camera, RX and battery before you commit to carbon;
- **DXF** — the real **carbon profiles** (3 mm bottom, 2 mm top / camera
  plates) to send to a cutter, exactly as the JeNo is built.

The `frame.scad` design is a clean-room re-creation of the **JeNo Pocket V2**
by **WE are FPV** (CC-BY-4.0, https://www.printables.com/model/1704840) —
wide-X 2.5", whoop 25.5×25.5 M2 main stack + 13×13 rear RX stack, 9 mm motor
mounts (1203-1303), O4-Lite-native camera bay, camera tilt 15-35°, three
bottom-plate personalities. Geometry is our own OpenSCAD, re-branded STRATOS.

> **The genuine WE are FPV STEP is also included** — see
> [`frame_jeno/`](frame_jeno/) (`JeNoPocket_V2.step`, CC-BY-4.0). The 3-D
> **viewer** renders that real frame for maximum fidelity
> ([`frame_jeno/step_to_stl.py`](frame_jeno/step_to_stl.py) meshes it to
> `stl/frame_real.stl`); `frame.scad` here is the independent STRATOS variant
> for those who want to print/cut the Stratos version. Attribution +
> licence: [`frame_jeno/ATTRIBUTION.md`](frame_jeno/ATTRIBUTION.md). Go buy
> the original plates from WE are FPV.

## Render

```bash
# printable prototype plates + viewer meshes -> stl/
for P in bottom_classic bottom_xcore bottom_tank top cam_plate \
         tpu_cam tpu_antenna tpu_guard tpu_bumper \
         motor prop board o4lite battery; do
  xvfb-run -a openscad -o stl/$P.stl --export-format binstl \
    -D "PART=\"$P\"" frame.scad; done

# carbon cut profiles -> dxf/  (cut these on 3 mm / 2 mm carbon)
for P in bottom_classic bottom_xcore bottom_tank top cam; do
  xvfb-run -a openscad -o dxf/$P.dxf -D "PART=\"dxf_$P\"" frame.scad; done
```

## Bottom-plate personalities (JeNo convention)

| Style | Centre | Use |
|---|---|---|
| **Classic** | carbon cross | balanced rigidity (recommended default) |
| **X-Core** | carbon X | lighter, works with vertical-USB FCs |
| **Tank** | reinforced, minimal lightening | durability / freeride |

## Carbon vs print

The **DXF** files are the deliverable for carbon (3 mm bottom, 2 mm top and
camera plates). The **STL** bottom prints at the same outline — bump the
thickness in `frame.scad` (`bottom_t`) for a stiff PLA-CF proto. TPU parts
(`tpu_cam`, `tpu_antenna`, `tpu_guard`, `tpu_bumper`) always print in TPU.

## Honesty (M0)

The plate **outlines are TUNE** — WE are FPV do not publish exact plate
dimensions, so these are re-drawn from the known facts (2.5", 25.5 + 13
stacks, 9 mm mounts, wide-X). The render self-checks the prop clearance
(`ASSERT wheelbase=114.6 … disc_gap_y=14.5 mm`), but **dry-fit a printed
plate before cutting carbon** and adjust `motor_mx/motor_my/body_*`. Nothing
here has been printed, cut or flown.
