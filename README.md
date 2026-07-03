# STRATOSDRONE — presentation site

A single-page, dependency-free presentation of the project: hero, specs vs the
DJI Tello EDU, the Tello-look double-strut design, the real clip-on prop
guards, a live embedded 3-D viewer, the PCB, how the project is built, and a
gallery of the concept brief + CAD/PCB renders.

Plain HTML/CSS/JS — **no build step**, no frameworks, no tracking.

## Files

| File | Purpose |
|---|---|
| `index.html` | the page |
| `style.css` | dark, minimal theme |
| `viewer.html` | the interactive 3-D viewer, embedded live via `<iframe>` in the "Spin it around yourself" section — a straight copy of `sim/viz/drone_viewer.html` (self-contained, ~5 MB, no external requests) |
| `assets/concept/*.jpg` | the original concept brief (resized from `/g`) |
| `assets/cad/*.jpg` | OpenSCAD renders of the `tello_style` v2 airframe (hero, arms, battery, guards, iso/front/side/underside/section) |
| `assets/pcb/*.jpg` | the PCB component map and routed top/bottom renders |

## Refreshing the embedded viewer

`viewer.html` is a plain copy — after regenerating the real one, just copy it over:

```bash
python3 sim/viz/gen_viewer.py
cp sim/viz/drone_viewer.html site/viewer.html
```

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

`hero.jpg`, `guards.jpg` and the frame-only shots (`arms.jpg`, `iso.jpg`,
`front.jpg`, `side.jpg`, `underside.jpg`) all come from
`hardware/frame/tello_style/assembly_site.scad` (with guards/motors/props)
and `assembly_site_plain.scad` (frame + capot only), rendered by:

```bash
cd hardware/frame/tello_style && python3 render_site_images.py
```

That script renders each view as **two** clean single-colour layers
(`-D SHOW_CAPOT=false` for the body+accessories, `-D SHOW_BODY=false` for the
capot alone) and composites them in Python, instead of one
`SHOW_BODY=SHOW_CAPOT=true` pass. OpenSCAD's preview ("thrown together") mode
dithers a checkerboard between the body's and capot's colours wherever their
surfaces are close/touching, and this OpenSCAD build (2021.01) drops
per-object colour entirely under `--render`/`render()` for multi-coloured
scenes — two single-colour renders + compositing sidesteps both. It outputs
PNGs next to itself; move `v2_*.png` into `preview/` and resize everything
into `site/assets/cad/` (see the bottom of this section for the resize
snippet).

`assembly_site_exploded.scad` (exploded/assembly) and `_section.scad`
(battery section — translucent shells, no boolean cut) aren't part of the
two-layer pipeline and still render in one pass; they don't touch the
capot/body boundary in a way that dithers.

The body/capot/UI accent colour (currently blue, `#2f6fed`) is set in three
places that need to move together: the `color()` calls in the four
`assembly_site*.scad` scenes, the capot/LED/front-prop/`--acc` colours in
`sim/viz/gen_viewer.py`, and `--acc`/`--acc2` in `site/style.css`.

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
  "hardware/frame/tello_style/hero.png":                        "site/assets/cad/hero.jpg",
  "hardware/frame/tello_style/guards.png":                      "site/assets/cad/guards.jpg",
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
