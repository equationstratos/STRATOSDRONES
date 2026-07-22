# Stratos FPV Configurator

A self-contained, **parametric** FPV drone configurator — open
[`configurator.html`](configurator.html) by double-click (no server, no build).

## What it does

- **Class selector** — 2" / 3" / 5" / 7". The whole quad is **procedurally
  rebuilt** at the right size (wheelbase, arm length/section, motor & prop
  diameter, stack mount, battery envelope all scale with the class).
- **Part pickers** — swap **frame, motors, FC/ESC, props, camera, VTX,
  receiver, battery** from a catalogue of the **popular models** sold by
  StudioSPORT / La Caméra Embarquée (KV, size, cells, weight class shown as a
  spec line under each dropdown). Only class-compatible parts are offered.
- **Instant 3-D** — every change re-renders the custom quad immediately.
- **Per-part colour pickers** + show/hide toggles for every group
  (châssis, moteurs, hélices, stack, caméra, VTX, batterie, antennes, visserie).
- **Preset builds** — 🐝 Tiny Whoop 2" · 🎥 Cinewhoop 3" · 🔥 Freestyle 5" ·
  🏁 Racing 5" · 🛰️ Long Range 7".
- **Build sheet** — live recap (class, wheelbase, prop size, selected parts,
  mass order-of-magnitude).
- Views (iso / top / face / side), prop spin, light/dark theme.

```bash
python3 configurator/gen_configurator.py   # regenerate configurator.html
```

## Honesty / roadmap

- The geometry is **procedural** (correct proportions and positioning per
  class), not a photo-real mesh of each exact SKU. It's the fast, light way to
  get *any* size right in one file (~1.7 MB, no embedded meshes).
- **FPV style only** for now, as requested.
- Catalogue figures are the **public spec sheets** of popular models; they are
  a starting point, not a live price/stock feed.
- Next step for maximum realism: drop **real STL/STEP part models** per SKU
  (like the TinyHoop MK1 viewer does for the JeNo frame + DJI O4 + GHF411) and
  key each catalogue entry to its mesh, plus exact mount coordinates from each
  part's assembly notice.
