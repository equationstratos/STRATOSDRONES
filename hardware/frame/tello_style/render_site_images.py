#!/usr/bin/env python3
"""Render the site/README product shots from assembly_site*.scad.

Renders each view as two clean layers (`-D SHOW_CAPOT=false` / `-D
SHOW_BODY=false`) and composites them in Python, instead of a single
`SHOW_BODY=SHOW_CAPOT=true` pass. OpenSCAD's preview ("thrown together")
mode dithers between the body's and capot's colours where their surfaces
are close/touching, and this OpenSCAD build (2021.01) drops per-object
colour entirely under `--render`/`render()` for multi-coloured scenes — two
single-colour renders + a compositing step sidesteps both.

Outputs PNGs next to this script; resize/copy into site/assets/ and
hardware/frame/tello_style/preview/ afterwards (see site/README.md).

Run:  python3 render_site_images.py            # main site renders
      python3 render_site_images.py --configurator   # colour-swatch renders
"""
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

JOBS = [
    # (scad file, output name, imgsize, camera, capot_on_top)
    # capot_on_top=True everywhere the capot faces the camera (it's the topmost
    # shell, so it should occlude the body); False for the underside, where
    # the camera looks up from below and the body's floor should occlude the
    # capot instead (only peeking through the vent holes).
    ("assembly_site.scad",       "hero.png",         "1600,1040", "0,0,5,58,0,35,420", True),
    ("assembly_site.scad",       "guards.png",       "1400,1400", "0,0,0,0,0,0,480",   True),
    ("assembly_site_plain.scad", "v2_iso.png",        "1000,850", "0,0,5,58,0,35,300", True),
    ("assembly_site_plain.scad", "v2_top.png",         "820,980", "0,0,0,0,0,0,230",   True),
    ("assembly_site_plain.scad", "v2_front.png",      "1000,560", "0,0,8,90,0,0,220",  True),
    ("assembly_site_plain.scad", "v2_side.png",       "1000,560", "0,0,8,90,0,90,220", True),
    ("assembly_site_plain.scad", "v2_underside.png",  "1000,850", "0,0,-5,235,0,35,300", False),
]

# Configurator colour swatches — id must match site/index.html's data-color
# attributes. Hex is the capot/front-prop colour passed to CAPOT_COLOR.
COLORS = [
    ("blue",    "#2f6fed"),
    ("white",   "#e9edf3"),
    ("black",   "#1b1e24"),
    ("red",     "#d6293b"),
    ("orange",  "#e6730d"),
]


def render(scad, out_png, imgsize, camera, defines):
    cmd = ["xvfb-run", "-a", "openscad", "-o", out_png,
           f"--imgsize={imgsize}", "--colorscheme=Cornfield",
           f"--camera={camera}", "--projection=ortho"]
    for d in defines:
        cmd += ["-D", d]
    cmd.append(os.path.join(HERE, scad))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit(f"render failed: {out_png}")


def composite(base_png, overlay_png, out_png, tol=10):
    """Paste overlay_png on top of base_png, skipping overlay pixels that
    match its own (sampled) background colour."""
    base = Image.open(base_png).convert("RGB")
    overlay = Image.open(overlay_png).convert("RGB")
    assert base.size == overlay.size
    bg = overlay.getpixel((2, 2))          # sample the shared background colour
    w, h = overlay.size
    out = base.copy()
    ov, op = overlay.load(), out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = ov[x, y]
            if abs(r - bg[0]) <= tol and abs(g - bg[1]) <= tol and abs(b - bg[2]) <= tol:
                continue              # background pixel -> keep the base layer
            op[x, y] = (r, g, b)
    out.save(out_png)


def render_composited(scad, out_path, imgsize, camera, capot_on_top, extra_defines=()):
    body_png = out_path + ".body.png"
    capot_png = out_path + ".capot.png"
    render(scad, body_png, imgsize, camera, ["SHOW_CAPOT=false", *extra_defines])
    render(scad, capot_png, imgsize, camera, ["SHOW_BODY=false", *extra_defines])
    if capot_on_top:
        composite(body_png, capot_png, out_path)
    else:
        composite(capot_png, body_png, out_path)
    os.remove(body_png)
    os.remove(capot_png)
    print("wrote", out_path)


def main_site():
    for scad, out, imgsize, camera, capot_on_top in JOBS:
        render_composited(scad, os.path.join(HERE, out), imgsize, camera, capot_on_top)


def main_configurator():
    imgsize, camera = "1200,900", "0,0,5,58,0,35,380"
    for name, hexcol in COLORS:
        out_path = os.path.join(HERE, f"config-{name}.png")
        render_composited("assembly_site.scad", out_path, imgsize, camera, True,
                           extra_defines=[f'CAPOT_COLOR="{hexcol}"'])


if __name__ == "__main__":
    if "--configurator" in sys.argv:
        main_configurator()
    else:
        main_site()
