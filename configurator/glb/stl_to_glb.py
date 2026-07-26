#!/usr/bin/env python3
"""STL -> GLB converter for the Stratos configurator.

Why GLB: one binary per part carrying geometry **and** its PBR material, ~5-10x
smaller than the base64-STL the viewers inline today, and loadable on demand by
the configurator (one fetch per selected SKU instead of one giant HTML).

    python3 configurator/glb/stl_to_glb.py            # convert the catalogue
    python3 configurator/glb/stl_to_glb.py --list     # show what would be done

Each entry names a material preset (carbon / alu / tpu / pcb / plastic / gold /
copper / lipo), which becomes a real glTF PBR material (baseColor + metallic +
roughness). Textures stay procedural in the page (see viz/gen_viewer.py) so the
GLBs remain tiny and UV-free.

Honesty: this is the geometry+material half of a "photo-real per SKU" pipeline.
Baked texture maps would need a DCC step (Blender UV unwrap) that is out of
scope here and NOT run by this script.
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STL = os.path.join(REPO, "TinyHoopMK1", "cad", "stl")
PARTS = os.path.join(REPO, "TinyHoopMK1", "cad", "frame_jeno", "parts")
TPU_DIR = os.path.join(REPO, "TinyHoopMK1", "cad", "frame_jeno", "tpu")
DJI = os.path.join(REPO, "TinyHoopMK1", "cad", "dji_o4")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parts")

# name -> (metallic, roughness, baseColor RGBA) — mirrors the viewer's look
MATERIALS = {
    "carbon":  (0.22, 0.46, (0.102, 0.114, 0.129, 1.0)),
    "alu":     (0.92, 0.26, (0.760, 0.773, 0.796, 1.0)),
    "gold":    (0.88, 0.26, (0.847, 0.647, 0.125, 1.0)),
    "tpu":     (0.04, 0.86, (0.169, 0.184, 0.212, 1.0)),
    "pcb":     (0.20, 0.50, (0.043, 0.325, 0.180, 1.0)),
    "plastic": (0.10, 0.55, (0.078, 0.082, 0.094, 1.0)),
    "lipo":    (0.12, 0.62, (0.051, 0.051, 0.063, 1.0)),
    "copper":  (0.90, 0.25, (0.793, 0.651, 0.229, 1.0)),
}

# the catalogue: out_name -> (source stl, material)
CATALOG = {
    "frame_bottom":   (os.path.join(PARTS, "frame_bottom.stl"), "carbon"),
    "frame_top":      (os.path.join(STL, "jeno_top.stl"), "carbon"),
    "cam_cage":       (os.path.join(PARTS, "cam_cage.stl"), "carbon"),
    "motor":          (os.path.join(STL, "motor.stl"), "alu"),
    "prop":           (os.path.join(STL, "prop.stl"), "plastic"),
    "ghf411":         (os.path.join(DJI, "ghf411_aio.stl"), "pcb"),
    "board_stratos":  (os.path.join(STL, "board.stl"), "pcb"),
    "battery":        (os.path.join(STL, "battery.stl"), "lipo"),
    "o4_cam":         (os.path.join(DJI, "o4_cam_head.stl"), "plastic"),
    "o4_airunit":     (os.path.join(DJI, "o4_airunit.stl"), "pcb"),
    "cam_mount_top":  (os.path.join(TPU_DIR, "o4_mount_top.stl"), "tpu"),
    "cam_mount_bot":  (os.path.join(TPU_DIR, "o4_mount_bottom.stl"), "tpu"),
    "arm_bumper":     (os.path.join(TPU_DIR, "arm_bumper.stl"), "tpu"),
    "rear_bay":       (os.path.join(STL, "rear_bay.stl"), "tpu"),
    "cap_holder":     (os.path.join(STL, "cap_holder.stl"), "tpu"),
    "capacitor":      (os.path.join(STL, "capacitor.stl"), "plastic"),
    "rx_pcb":         (os.path.join(STL, "rx_pcb.stl"), "pcb"),
    "rx_holder":      (os.path.join(STL, "rx_holder.stl"), "tpu"),
    "gps_module":     (os.path.join(STL, "gps_module.stl"), "plastic"),
    "buzzer":         (os.path.join(STL, "buzzer.stl"), "plastic"),
    "screw":          (os.path.join(STL, "screw.stl"), "alu"),
    "ant_dji":        (os.path.join(STL, "dji_pro_ant.stl"), "plastic"),
    "ant_rhcp":       (os.path.join(STL, "rhcp_lp.stl"), "plastic"),
    "ant_foxeer":     (os.path.join(STL, "foxeer_lp.stl"), "plastic"),
    "ant_matchstick": (os.path.join(STL, "ant_singularity.stl"), "plastic"),
    "rx_antenna":     (os.path.join(STL, "rx_antenna.stl"), "plastic"),
}

MM_TO_M = 0.001


def srgb_to_linear(c):
    """glTF baseColorFactor is LINEAR; the presets above are sRGB (as picked in
    the viewer). Without this, dark parts render ~3x too light."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def convert(name, src, mat_name, draco=True):
    """STL (mm) -> GLB (metres) with a real glTF PBR material."""
    import numpy as np
    import trimesh

    mesh = trimesh.load(src, force="mesh")
    if mesh.is_empty:
        raise ValueError("empty mesh")
    mesh.apply_scale(MM_TO_M)                 # glTF convention is metres
    metal, rough, color = MATERIALS[mat_name]
    mesh.visual = trimesh.visual.TextureVisuals(
        material=trimesh.visual.material.PBRMaterial(
            name=mat_name,
            baseColorFactor=[srgb_to_linear(c) for c in color[:3]] + [color[3]],
            metallicFactor=metal,
            roughnessFactor=rough,
        )
    )
    scene = trimesh.Scene(geometry={name: mesh})
    dst = os.path.join(OUT, name + ".glb")
    with open(dst, "wb") as fh:
        fh.write(scene.export(file_type="glb"))
    return dst, len(mesh.faces), os.path.getsize(dst), os.path.getsize(src)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="only show the plan")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    manifest, tot_glb, tot_stl, missing = {}, 0, 0, []

    print("== STL -> GLB (configurator) ==")
    for name, (src, mat) in sorted(CATALOG.items()):
        if not os.path.exists(src):
            missing.append((name, src))
            continue
        if args.list:
            print(f"  {name:16s} {mat:8s} <- {os.path.relpath(src, REPO)}")
            continue
        try:
            dst, faces, nglb, nstl = convert(name, src, mat)
        except Exception as exc:                       # keep going, report at end
            missing.append((name, f"{src} ({exc})"))
            continue
        tot_glb += nglb
        tot_stl += nstl
        manifest[name] = {
            "file": "parts/" + os.path.basename(dst),
            "material": mat,
            "faces": faces,
            "bytes": nglb,
        }
        print(f"  {name:16s} {mat:8s} {faces:7d} tris  "
              f"{nstl/1024:8.1f} KB STL -> {nglb/1024:7.1f} KB GLB")

    if args.list:
        return 0

    with open(os.path.join(os.path.dirname(OUT), "manifest.json"), "w") as fh:
        json.dump({"units": "m", "materials": MATERIALS, "parts": manifest},
                  fh, indent=1, sort_keys=True)

    print(f"\n  {len(manifest)} parts · STL {tot_stl/1024:.0f} KB -> "
          f"GLB {tot_glb/1024:.0f} KB "
          f"({100 - 100*tot_glb/max(tot_stl,1):.0f}% smaller)")
    print(f"  wrote {os.path.relpath(OUT, REPO)}/ + manifest.json")
    if missing:
        print("\n  SKIPPED (source missing/unreadable):")
        for name, src in missing:
            print(f"    {name}: {os.path.relpath(src, REPO) if os.path.isabs(src.split(' ')[0]) else src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
