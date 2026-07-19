# fpv85 CAD — printable frame + canopy (v0)

![assembly](preview/assembly_iso.png)

One parametric file, `frame.scad`, `PART`-selected like every Stratos model.

| PART | Print | Note |
|---|---|---|
| `frame` | 1× | unibody plate: X arms → 0802 pods (3×M1.4 Ø6.6) + whoop 25.5 AIO posts + battery strap slots + feet |
| `canopy` | 1× | v4 EAGLE2-STYLE: tall faceted NOSE PLATES (kidney cutouts) flanking the big lens, slender TOP SPAR to a faceted tail tip, screw rows nose+spar, raked antenna seats |
| `prop` / `motor` | — | viewer/playground meshes (buy real ones) |
| `board/airunit/fpvcam/rxmod/battery/antennas` | — | electronics + pack + antennas — viewer meshes (buy, don't print) |
| `assembly` | — | full preview: frame + canopy + ELECTRONICS + battery + antennas + motors (ghost props) |

Key parameters (top of the file, all `TUNE` until first print): wheelbase 85
(v3.2 — the class is named by wheelbase; 65 could not swing Ø40 props past
the rails), prop 40, motor_bc 6.6, aio 25.5, cam_w 14.4, cam_tilt 15°, foot 7.

## Regenerate

```bash
cd fpv85/cad
for P in frame canopy; do
  xvfb-run -a openscad -o stl/$P.stl --export-format binstl \
    -D "PART=\"$P\"" frame.scad; done
xvfb-run -a openscad -o preview/assembly_iso.png --imgsize=1100,820 \
  --colorscheme=Tomorrow --camera=0,0,4,55,0,35,240 -D 'PART="assembly"' frame.scad
```

Status: dry-fit dimensions from catalogue values. v3.2/v3.3 prop-clearance
audit (measured on the exported STLs at the viewer placements): blade tip
19.57 mm ≤ Ø/2; nearest chassis point in the blade z-band 22.0 mm from a
motor axis (canopy rail), everything else ≥ 25 mm; disc-to-disc gap 21 mm.
Still **print & iterate before trusting any TUNE dim**.
