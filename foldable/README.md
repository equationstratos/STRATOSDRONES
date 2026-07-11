# Fr4n7-F — la Fr4n7 qui se plie

A **folding-arm variant** of the Fr4n7-001: same electronics (the Fr4n7
mainboard), same 8520 motors and 3" props, same firmware — but four
**sculpted paddle arms** pivot on **inset corner hinges dimensioned from
the real thing:1604440** (M3 axes, 6 mm inside the corner) and fold flat
along the flanks, each one snapping in by its own **arm-mounted tab**
(nothing protrudes from the body). Spring-loaded pivots pop them open in
half a second:

- **V1 « manuelle »** — a **centred TOP push-button** (umbrella style)
  releases the latch. Zero electronics added.
- **V2 « commande »** — a 3.7 g nano-servo turns a **self-locking worm +
  toothed sector** (the retained mechanism) that releases the *same* latch,
  triggered by a new **`deploy`** SDK verb (and the BOOT button as a physical
  fallback). The verb is **specified, not yet implemented** — see
  [`DESIGN.md`](DESIGN.md) §4 for the wire spec and the exact future
  implementation map (no PCB change needed).

## Inspirations (credit where due)

- **[Thingiverse thing:1604440](https://www.thingiverse.com/thing:1604440)**
  — the folding mini-quad concept this follows closely: **flat sculpted
  paddle arms** pivoting inside the body's rounded corner lobes, folding
  alongside it into one compact silhouette. **Clean-room**: our geometry is
  original parametric OpenSCAD; nothing was copied from that mesh — same
  discipline as the Fr4n6's Avata homage.
- **The project owner's printed prototype** (photos in the project log):
  the key optimisation is his — the **front arms mount INVERTED** (pod
  flipped, prop *under* the belly). Folded, the front arm sweeps rearward in
  a LOW prop plane while the rear arm folds forward in a HIGH plane along
  the same flank: **the arms can never cross**, and the package gets
  tighter. Deployed, the two prop planes are ~23 mm apart — his prototype
  flies that way.

## Positioning vs Fr4n7-001

| | Fr4n7-001 | **Fr4n7-F** |
|---|---|---|
| Wheelbase (deployed) | 118 mm | **same** |
| Footprint | 96 × 92.5 mm fixed | **≈ 68 × 83 mm folded** (−35 % width, blades aligned) |
| Arms | printed into the shell | **4 sculpted paddle arms on INSET corner hinges (M3 + torsion springs), snap tabs ON THE ARMS into flush wall windows** |
| Deploy | — | **spring-loaded; centred TOP button (V1) or servo + `deploy` (V2, retained drive = self-locking worm+sector); 7 printable mechanisms compared in the viewer** |
| Props | one plane | **two planes** (front low / rear high — inverted front pods) |
| Landing | belly | **4 feet** in the blade-free "dead diamond" |
| Electronics / firmware | Fr4n7 board + fc_core | **identical** (servo on J9's EXP_IO for V2) |

## Repository layout (this folder)

```
foldable/
  README.md          this charter
  DESIGN.md          fold math, mechanism, and the `deploy` verb spec
  cad/               parametric OpenSCAD (frame_foldable.scad) → STL + previews
  viz/               self-contained browser 3-D viewer with the fold ANIMATION
```

**See it in 3-D:** open [`viz/drone_viewer.html`](viz/) — orbit it, then hit
**« Replier / Déployer »** (or send `postMessage({type:'deploy'})`) to watch
the arms fold. Built exactly like the Fr4n7/Fr4n6 viewers (offline, no CDN).

## Status

**M0 — geometry validated, not flight-validated.** The kinematics are
proven in CAD (three machine-checked collision gates: deployed, folded,
arm-vs-arm — all empty-intersection) and animated in the viewer. Spring
rates, detent depths, latch travel and all fits marked `TUNE` in the SCAD
are **first-print estimates**. The `deploy` verb is documentation only.
Print it, iterate the TUNE list, then fly.
