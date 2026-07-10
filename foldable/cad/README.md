# Fr4n7-F CAD — parametric foldable frame

One OpenSCAD file, `frame_foldable.scad`, `PART`-selected like the Fr4n6
CAD. Fold math and mechanism rationale: [`../DESIGN.md`](../DESIGN.md).

| PART | Print | Note |
|---|---|---|
| `body` | 1× | pod + INSET corner hinges + flush tab windows + feet |
| `capot` | 1× | foldable-specific lid (battery channel, centred button bore) |
| `arm_front` | 2× (1 mirrored) | paddle + snap tab, inverted pod — prop under the belly |
| `arm_rear` | 2× (1 mirrored) | paddle + snap tab, v2-style pod — prop on top |
| `latch` | 1× | rails above the PCB + 4 release fingers + centre bridge/sleeve |
| `button` | 1× (V1) | vertical CENTRED pin, cone cams the bridge |
| `mechanisms.scad` | demos | `worm_crank` / `scissor` / `iris_cam` (+ `_kit` flat plates) — printable alternative mechanisms |
| `servo_cam` | 1× (V2) | cam disc for a 3.7 g nano-servo horn |
| `arm_fr/fl/rr/rl` | — | pivot-local exports for the viewer (pre-mirrored) |
| `assembly` / `assembly_folded` | — | previews (ghost prop discs) |
| `collision_deployed/_folded/_arms` | — | **gates: binstl must be exactly 684 B** |

Hardware per drone: 4× M3×14 + nyloc (as the original thing:1604440),
2 LH + 2 RH torsion springs (0.5 mm wire, Øi 4), 1 rubber band (latch
return), V2 only: 3.7 g nano servo.

## Regenerate

```bash
cd foldable/cad
for P in body capot arm_front arm_rear arm_fr arm_fl arm_rr arm_rl latch button servo_cam; do
  xvfb-run -a openscad -o stl/$P.stl --export-format binstl \
    -D "PART=\"$P\"" frame_foldable.scad; done
# collision gates — every file must be exactly 684 bytes:
for G in collision_deployed collision_folded collision_arms; do
  xvfb-run -a openscad -o /tmp/$G.stl --export-format binstl \
    -D "PART=\"$G\"" frame_foldable.scad && stat -c "%s  $G" /tmp/$G.stl; done
```

Previews (`preview/*.png`) are rendered with the camera flags in the file
history; anything tagged `TUNE` is a first-print estimate.
