# Fr4n7-F — browser 3-D viewer (with the fold animation)

![preview](preview.png)

Self-contained WebGL viewer, same recipe as the Fr4n7/Fr4n6 ones: open
`drone_viewer.html` by double-click — Three.js r160 and every STL are
inlined as base64 `data:` URLs. **No CDN, no server.**

## What's special here

Each arm is its own Three.js group pivoted at its hinge, so the viewer
plays the real kinematics (FOLD_A = 79.45°, signs FR+/FL−/RR−/RL+ from
`../cad/frame_foldable.scad`):

- **« Déployer / Replier »** buttons tween the fold (~1.2 s) and a slider
  scrubs it; folding also eases the blades into the along-arm transport
  pose.
- `postMessage({type:'deploy'})` / `({type:'fold'})` drive it from a host
  page — the browser twin of the `deploy` SDK verb (spec in
  [`../DESIGN.md`](../DESIGN.md)). `?fold=1` opens folded.
- Front props render UNDER the belly (inverted pods) with reversed spin
  sense — the owner's no-crossing trick, visible live.

Everything else matches the other viewers: orbit + bounded zoom, per-part
toggles (châssis / capot / bras / verrou / hélices), wireframe, grid, spin
slider, `postMessage {type:'colors', body/capot/arms/mech/props}` recolour
+ `?body=…` URL params, `{type:'ready'}` handshake, `{type:'viz', visible}`
offscreen pause, and the `window.__vizRendering/__lastColors/__foldT`
test hooks.

## Regenerate

```bash
# 1. export the part STLs (see ../cad/README.md, incl. the 684-byte gates)
# 2. inline them + vendored Three.js into the single HTML:
python3 foldable/viz/gen_viewer.py    # -> foldable/viz/drone_viewer.html
```
