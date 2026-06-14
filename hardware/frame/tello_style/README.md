# Tello-style closed body (alternative frame)

A second airframe for the same electronics — a **closed clamshell body** in
the DJI Tello size class, as an alternative to the open `../frame.scad` X-frame.

![assembly](preview/assembly.png)

Same flight envelope as a Tello (≈ 98 × 92.5 mm footprint, **118 mm
wheelbase**, 3" / 76 mm props, 8520 motors), but visually distinct: hexagonal
motor nacelles, a faceted vented canopy, a chamfered camera nose, and a
slide-in rear battery.

| File | Part |
|---|---|
| `body_bottom.scad` | lower shell — PCB bay, 4 arms + motor pockets, bottom sensor window, camera nose |
| `body_top.scad` | upper canopy — camera window, hex vents, LED light pipes, snap clips |
| `assembly.scad` | preview only (both shells + motors + prop disks) — do not print |

```bash
openscad -o stl/body_bottom.stl --export-format binstl body_bottom.scad
openscad -o stl/body_top.scad   --export-format binstl body_top.scad
```

Print in PETG or tough PLA, 3 perimeters, no supports (each shell prints flat
on its open face). The pod fits the **36 × 70 mm Tello-style PCB** (see
`../../pcb/`, board outline `BOARD` in `design.py`); the four M2 bosses are at
a 26 × 60 mm pitch. Press the 8520 motors into the hex nacelles, route the
wires through the arm channels to the board's corner motor pads, slide the 1S
pack into the rear bay, and snap the canopy on.

Target all-up weight ≈ 90 g (95 g cap). For the open racing-style frame use
the parts in the parent directory instead.
