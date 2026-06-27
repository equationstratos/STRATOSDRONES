# Tello-style closed body (alternative frame)

A second airframe for the same electronics — a **closed clamshell body** in
the DJI Tello size class, as an alternative to the open `../frame.scad` X-frame.

![assembly](preview/assembly.png)

Same flight envelope as a Tello (≈ 98 × 92.5 mm footprint, **118 mm
wheelbase**, 3" / 76 mm props, 8520 motors): smooth rounded clamshell, round
thin-wall motor mounts, **open 3-D Eiffel-truss arms** (triangulated on the top
*and* the side faces, so the lattice reads from every angle), a faceted hex-vented
canopy (solid over the lens) and a chamfered camera nose. The pod is sized to the
**real mainboard** (38 × 74 mm; M2 mounts at **30 × 66**, i.e. one in each
corner_r=4 fillet — straight from `design.py` `BOARD`); the 1S pack sits on top of
the board, held by a **cradle moulded into the canopy** (bottom-side flow + ToF
sensors look down through the floor window, so nothing mounts beneath the board).

| File | Part |
|---|---|
| `body_bottom.scad` | lower shell — PCB bay + bosses, 4 Eiffel-truss arms + motor mounts, bottom sensor window, camera nose |
| `body_top.scad` | upper canopy — hex vents, LED light pipes, snap clips, integrated battery cradle |
| `assembly.scad` | preview only (both shells + motors + prop disks) — do not print |

```bash
openscad -o stl/body_bottom.stl --export-format binstl body_bottom.scad
openscad -o stl/body_top.scad   --export-format binstl body_top.scad
```

Print in PETG or tough PLA, 3 perimeters, no supports (each shell prints flat
on its open face). The pod fits the **38 × 74 mm Tello-style PCB** (see
`../../pcb/`, board outline `BOARD` in `design.py`); the four M2 bosses are at
a **30 × 66 mm** pitch — one in each corner (matching the board's real holes),
filleted with a screw lead-in. Press the 8520 motors into the round mounts, route the wires through
the arm channels to the board's corner motor pads, drop the board onto the four
bosses, slide the 1S pack into the canopy cradle, and snap the canopy on.

## Printed mass

Lightweight revision — round thin-wall motor mounts (was solid hex blocks),
**open 3-D Eiffel-truss arms** (triangulated on top + sides), rounder pod, thinner
walls/floor, and a clean canopy (no cosmetic arm caps, solid over the lens) with
an integrated battery cradle. Solid-volume estimate in PLA (1.24 g/cm³); the real
print, mostly thin walls, lands close to this:

| Shell | Volume | ~Mass (PLA) |
|---|---|---|
| `body_bottom` | 13.8 cm³ | **17.2 g** |
| `body_top` | 6.9 cm³ | **8.5 g** (incl. battery cradle) |
| **Frame total** | 20.7 cm³ | **≈ 25.7 g** |

Down from ≈ 39 g (the original hex-block shells) — ~35 % lighter, *and* it now
fits the real 38 × 74 board (the old 37 mm inner pod could not) and retains the
battery. With the ~92 g electronics + battery + motors the all-up weight stays
Tello-class (≈ 90 g, 95 g cap). For the open racing-style frame use the parts in
the parent directory instead.
