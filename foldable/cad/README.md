# Fr4n7-F CAD — parametric foldable frame

One OpenSCAD file, `frame_foldable.scad`, `PART`-selected like the Fr4n6
CAD. Fold math and mechanism rationale: [`../DESIGN.md`](../DESIGN.md).

| PART | Print | Note |
|---|---|---|
| `body` | 1× | pod + INSET corner hinges + flush tab windows + feet |
| `capot` | 1× | foldable-specific lid (battery channel, centred button bore) |
| `arm_front` | 2× (1 mirrored) | paddle + snap tab, inverted pod — prop under the belly |
| `arm_rear` | 2× (1 mirrored) | paddle + snap tab, v2-style pod — prop on top |
| `latch` | 1× | rails above the PCB + 4 release fingers + centre bridge/sleeve + V2 sector-drive tab |
| `button` | 1× (V1) | vertical CENTRED pin, cone cams the bridge |
| `servo_worm` + `servo_sector` | 1× each (V2) | **the RETAINED drive** — worm on the nano-servo spline + toothed sector whose pin shoves the slider (self-locking) |
| `mechanisms.scad` | demos | 7 printable mechanisms: `worm_crank` ★ / `scissor` / `iris_cam` / `rack_pinion` / `cam_lever` / `toggle_clamp` / `wiper` (+ `_kit` plates, + `stl/mech/p_*` per-part exports) — **compare them animated in [`../viz/mechanisms_viewer.html`](../viz/)** (★ = retained for the V2 drive) |
| `servo_drive` / `servo_cam` | — | assembled V2 drive preview (worm + sector + servo proxy) |
| `arm_fr/fl/rr/rl` | — | pivot-local exports for the viewer (pre-mirrored) |
| `assembly` / `assembly_folded` / `assembly_v2` | — | previews (`_v2` shows the worm+sector drive; ghost prop discs) |
| `collision_deployed/_folded/_arms/_drive` | — | **gates: binstl must be exactly 684 B** (`_drive` = worm+sector clears walls/rails/button) |

Hardware per drone: 4× M3×14 + nyloc (as the original thing:1604440),
2 LH + 2 RH torsion springs (0.5 mm wire, Øi 4), 1 rubber band (latch
return), V2 only: 3.7 g nano servo.

## Regenerate

```bash
cd foldable/cad
for P in body capot arm_front arm_rear arm_fr arm_fl arm_rr arm_rl latch button servo_worm servo_sector; do
  xvfb-run -a openscad -o stl/$P.stl --export-format binstl \
    -D "PART=\"$P\"" frame_foldable.scad; done
# collision gates — every file must be exactly 684 bytes:
for G in collision_deployed collision_folded collision_arms collision_drive; do
  xvfb-run -a openscad -o /tmp/$G.stl --export-format binstl \
    -D "PART=\"$G\"" frame_foldable.scad && stat -c "%s  $G" /tmp/$G.stl; done
```

Previews (`preview/*.png`) are rendered with the camera flags in the file
history; anything tagged `TUNE` is a first-print estimate.
