# STRATOSDRONE — presentation site

A single-page, dependency-free presentation of the project: hero, specs vs the
DJI Tello EDU, the Tello-look double-strut design, the real clip-on prop
guards, how the project is built, and a gallery of the concept brief + CAD/PCB
renders.

Plain HTML/CSS/JS — **no build step**, no frameworks, no tracking.

## Files

| File | Purpose |
|---|---|
| `index.html` | the page |
| `style.css` | dark, minimal theme |
| `assets/concept/*.jpg` | the original concept brief (resized from `/g`) |
| `assets/cad/*.jpg` | OpenSCAD renders of the `tello_style` v2 airframe (hero, arms, battery, guards, iso/front/side/underside/section) |
| `assets/pcb/*.jpg` | the PCB component map and a routed board render |

## View locally

Open `index.html` directly, or serve the folder:

```bash
cd site && python3 -m http.server 8000
# → http://localhost:8000
```

## Deploy

Pushed to `claude/cool-ride-w1bpia` or `main`, `.github/workflows/pages.yml`
publishes this folder to GitHub Pages as-is (after checking every referenced
asset exists). Enable Pages once in **Settings → Pages → Source: GitHub Actions**.

## Refreshing the images

The frame-only renders (`arms.jpg`, `battery.jpg`, `iso.jpg`, `front.jpg`,
`side.jpg`, `underside.jpg`, `section.jpg`) come straight from
`hardware/frame/tello_style/preview/v2_*.png` — see that directory's own
render commands. Studio previews use the `Cornfield` colorscheme (light
background) for consistency with the dark page's white `.ph` card boxes.

`hero.jpg` and `guards.jpg` need the real Tello prop guards attached, which
aren't part of the printable frame (they're a separate STL placed only in the
3-D viewer), so they're rendered from a dedicated scene,
`hardware/frame/tello_style/assembly_site.scad` — imports the guard STL at
each motor with the same transform `sim/viz/gen_viewer.py` uses, wrapped in
explicit `color()` (OpenSCAD's `--render` mode drops per-object colours for
this multi-part scene; use plain preview instead — no `--render` flag):

```bash
cd hardware/frame/tello_style
# three-quarter hero — full drone with guards
xvfb-run -a openscad -o /tmp/hero.png --imgsize=1600,1040 --colorscheme=Cornfield \
  --camera=0,0,5,58,0,35,420 --projection=ortho assembly_site.scad
# top-down — all four guards, symmetric
xvfb-run -a openscad -o /tmp/top.png --imgsize=1400,1400 --colorscheme=Cornfield \
  --camera=0,0,0,0,0,0,480 --projection=ortho assembly_site.scad
```

The PCB renders are regenerated straight from the current board:

```bash
cd hardware/pcb
python3 scripts/gen_component_map.py          # -> preview/component_map.png
kicad-cli pcb export svg --layers "F.Cu,F.Silkscreen,Edge.Cuts,F.Mask" \
  --page-size-mode 2 -o /tmp/pcb_top.svg stratosdrone.kicad_pcb
python3 -c "import cairosvg; cairosvg.svg2png(url='/tmp/pcb_top.svg', \
  write_to='/tmp/pcb_top.png', output_width=1000, background_color='white')"
```

After re-rendering, resize into `site/assets/`:

```bash
python3 - <<'PY'
from PIL import Image; import pathlib
jobs = {
  "/tmp/hero.png":                                              "site/assets/cad/hero.jpg",
  "/tmp/top.png":                                                "site/assets/cad/guards.jpg",
  "hardware/frame/tello_style/preview/v2_top.png":              "site/assets/cad/arms.jpg",
  "hardware/frame/tello_style/preview/v2_exploded.png":         "site/assets/cad/battery.jpg",
  "hardware/frame/tello_style/preview/v2_iso.png":              "site/assets/cad/iso.jpg",
  "hardware/frame/tello_style/preview/v2_front.png":            "site/assets/cad/front.jpg",
  "hardware/frame/tello_style/preview/v2_side.png":             "site/assets/cad/side.jpg",
  "hardware/frame/tello_style/preview/v2_underside.png":        "site/assets/cad/underside.jpg",
  "hardware/frame/tello_style/preview/v2_battery_section.png":  "site/assets/cad/section.jpg",
  "hardware/pcb/preview/component_map.png":                     "site/assets/pcb/component_map.jpg",
  "/tmp/pcb_top.png":                                            "site/assets/pcb/top.jpg",
}
for src, dst in jobs.items():
    p = pathlib.Path(src)
    if not p.exists(): continue
    im = Image.open(p).convert("RGB")
    im.thumbnail((1600, 1600))
    pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=86, optimize=True)
    print("wrote", dst)
PY
```

The concept images in `assets/concept/` are resized copies of `/g/1.png … 10.png`.
