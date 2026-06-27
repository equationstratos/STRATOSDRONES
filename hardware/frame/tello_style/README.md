# Tello-style closed body (alternative frame)

A second airframe for the same electronics — a **closed clamshell body** in
the DJI Tello size class, as an alternative to the open `../frame.scad` X-frame.

![assembly](preview/assembly.png)

Same flight envelope as a Tello (≈ 98 × 92.5 mm footprint, **118 mm
wheelbase**, 3" / 76 mm props, 8520 motors): smooth rounded clamshell, round
thin-wall motor mounts, a faceted hex-vented canopy and a chamfered camera nose.
The pod is sized to the **real mainboard** (38 × 74 mm, M2 mounts at 28 × 64 —
straight from `design.py` `BOARD`); the 1S pack sits on top of the board under
the canopy (bottom-side flow + ToF sensors look down through the floor window,
so nothing mounts beneath the board).

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
a **28 × 64 mm** pitch (matching the board). Press the 8520 motors into the
round motor mounts, route the wires through the arm channels to the board's
corner motor pads, drop the board onto the four bosses, set the 1S pack on top
of it, and snap the canopy on.

## Printed mass

Lightweight revision — round thin-wall motor mounts (was solid hex blocks),
slimmer tapered arms, rounder pod, thinner walls/floor, and the canopy is a
clean cover (the cosmetic arm caps were removed). Solid-volume estimate in PLA
(1.24 g/cm³); the real print, mostly thin walls, lands close to this:

| Shell | Volume | ~Mass (PLA) |
|---|---|---|
| `body_bottom` | 14.0 cm³ | **17.4 g** |
| `body_top` | 5.3 cm³ | **6.6 g** |
| **Frame total** | 19.3 cm³ | **≈ 24 g** |

Down from ≈ 39 g (the original hex-block shells) — ~38 % lighter, and the pod
now actually fits the 38 × 74 board (the previous 37 mm inner pod was too narrow
for it). With the ~92 g electronics + battery + motors the all-up weight stays
Tello-class (≈ 90 g, 95 g cap). A top-side battery cradle can be added to the
canopy if the pack needs more than friction retention. For the open racing-style
frame use the parts in the parent directory instead.
