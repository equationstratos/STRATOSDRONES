# STRATOSDRONE — presentation site

A single-page, dependency-free presentation of the project: hero, specs vs the
DJI Tello EDU, the swept "whoop" design, the three protection variants, how the
project is built, and a gallery of the concept brief + CAD/PCB renders.

Plain HTML/CSS/JS — **no build step**, no frameworks, no tracking.

## Files

| File | Purpose |
|---|---|
| `index.html` | the page |
| `style.css` | dark, minimal theme |
| `assets/concept/*.jpg` | the original concept brief (resized from `/g`) |
| `assets/cad/*.jpg` | OpenSCAD renders of the whoop airframe (the three variants, hero, top, frame) |
| `assets/pcb/*.jpg` | the PCB component map and a board render |

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

The CAD renders come from `hardware/frame/whoop/preview/*.png` and the PCB map
from `hardware/pcb/preview/`. The studio previews use the `Tomorrow` colorscheme
(light #f8f8f8 background) on `assembly.scad`:

```bash
cd hardware/frame/whoop
CAM=0,0,4,62,0,22,0
# airframe (no canopy) and canopy alone
xvfb-run -a openscad -D guard='"duct"' -D show='"frame"'  --camera=$CAM --viewall \
  --autocenter --projection=p --colorscheme=Tomorrow --imgsize=1200,820 -o preview/frame.png  assembly.scad
xvfb-run -a openscad -D show='"canopy"' --camera=$CAM --viewall \
  --autocenter --projection=p --colorscheme=Tomorrow --imgsize=1200,820 -o preview/canopy.png assembly.scad
```

After re-rendering, regenerate the resized JPEGs:

```bash
python3 - <<'PY'
from PIL import Image; import pathlib
jobs = {
  "hardware/frame/whoop/preview/hero.png":          "site/assets/cad/hero.jpg",
  "hardware/frame/whoop/preview/assembly_duct.png": "site/assets/cad/duct.jpg",
  "hardware/frame/whoop/preview/assembly_ring.png": "site/assets/cad/ring.jpg",
  "hardware/frame/whoop/preview/assembly_none.png": "site/assets/cad/none.jpg",
  "hardware/frame/whoop/preview/top.png":           "site/assets/cad/top.jpg",
  "hardware/frame/whoop/preview/frame.png":         "site/assets/cad/frame.jpg",
  "hardware/frame/whoop/preview/canopy.png":        "site/assets/cad/canopy.jpg",
  "hardware/pcb/preview/component_map.png":         "site/assets/pcb/component_map.jpg",
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
