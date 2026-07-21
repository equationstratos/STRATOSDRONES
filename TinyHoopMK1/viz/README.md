# TinyHoop MK1 viewer + simulateur (navigateur)

`drone_viewer.html` — un seul fichier autonome (double-clic, hors-ligne,
Three.js r160 inliné) :

- **Vue 3D** : plaque basse / plaque haute / moteurs / hélices / carte /
  O4 Lite / plaques caméra (les vrais STL de `../cad/stl/`), vues, toggles,
  fil de fer, rotation d'hélices, recolor `{type:'colors'}`.
- **`?playground=1` = le SIMULATEUR** — scripts SDK Tello
  (command/takeoff/go/curve/flip/…, essaim `drones N` + expressions en `i`),
  presets (hover/carré/swarm/freestyle) et **pilotage clavier** (T décoller,
  flèches translater, Z/W monter/descendre, Q/D pivoter, F flip, L atterrir).
  Cinématique SDK, airframe-agnostique : les mêmes verbes tournent contre le
  sim Gazebo et le vrai drone.
- Hooks : `__vizRendering`, `__pgState`, `__lastColors` ; pause hors-écran
  `{type:'viz'}` + handshake `{type:'ready'}`.

Le simulateur du navigateur est **cinématique** (pas un modèle de
dynamique) — c'est l'aperçu de mission ; la dynamique haute-fidélité est le
portage Gazebo (M3, voir `../sim/README.md`).

## Régénérer

```bash
# 1. exporter les STL (voir ../cad/README.md)
# 2. régénérer le HTML :
python3 TinyHoopMK1/viz/gen_viewer.py   # -> TinyHoopMK1/viz/drone_viewer.html
```
