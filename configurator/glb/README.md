# Pipeline GLB (glTF 2.0 binaire) — fondation du configurateur en ligne

Objectif : servir le configurateur avec **une pièce = un fichier `.glb`** chargé
à la demande, au lieu du visualisateur monolithique actuel
(`TinyHoopMK1/viz/drone_viewer.html`, ~18 Mo avec tous les maillages en base64).

## Ce qui est ici

| Fichier | Rôle |
|---|---|
| `stl_to_glb.py` | convertisseur **STL → GLB** : met à l'échelle en mètres et attache un vrai **matériau PBR glTF** (baseColor + metallic + roughness) par pièce |
| `parts/*.glb` | les 26 pièces converties (châssis, moteurs, hélices, FC, caméra O4, TPU, antennes, batterie…) |
| `manifest.json` | index machine : pièce → fichier, matériau, nb de triangles, taille |
| `gen_glb_viewer.py` | génère `glb_viewer.html`, la **preuve de bout en bout** : une coquille légère qui `fetch` les GLB et assemble le drone |

## Utilisation

```bash
python3 configurator/glb/stl_to_glb.py          # (re)convertir le catalogue
python3 configurator/glb/stl_to_glb.py --list   # voir le plan sans écrire
python3 configurator/glb/gen_glb_viewer.py      # régénérer la page de démo

# les GLB se chargent en HTTP (pas en file://) :
python3 -m http.server -d configurator/glb 8000
# puis ouvrir http://localhost:8000/glb_viewer.html
```

## Résultats mesurés

- **26 pièces** converties : **10 058 Ko de STL → 3 646 Ko de GLB** (−64 %).
- Page de démo vérifiée en navigateur : **23 GLB chargés en HTTP 200, 0 erreur JS**,
  ~3,5 Mo transférés, drone complet assemblé aux mêmes coordonnées que le
  visualisateur TinyHoop.
- Le sélecteur d'antenne montre le gain : changer de modèle **n'échange qu'un
  petit GLB** (matchstick = 6 Ko) au lieu de régénérer un HTML entier.

## Détails techniques qui comptent

- **Unités** : les STL sont en mm, les GLB sont écrits en **mètres** (convention glTF).
- **Couleurs** : `baseColorFactor` glTF est **linéaire**. Les presets sont
  exprimés en sRGB (comme dans le visualisateur) puis convertis
  (`srgb_to_linear`) — sans ça les pièces sombres rendaient ~3× trop clair.
- **Loaders vendorisés** : `sim/viz/vendor/addons/loaders/GLTFLoader.js` +
  `addons/utils/BufferGeometryUtils.js` (three r160). L'import relatif de
  GLTFLoader a été réécrit en spécificateur nu (`three/addons/utils/…`) pour
  fonctionner avec l'importmap en `data:` URL.
- **Éclairage** : IBL studio (`RoomEnvironment` + PMREM) et tone-mapping ACES,
  comme le visualisateur — c'est ce qui fait le rendu « matière », pas le format.

## Honnêteté / limites

- Ce pipeline livre la moitié **géométrie + matériau** d'un rendu « photo-réel
  par SKU ». Les **textures bakées** (tissage carbone, alu brossé en maps)
  demandent une étape DCC (UV unwrap sous Blender) : **Blender n'est pas
  disponible dans cet environnement**, donc cette étape n'est ni exécutée ni
  simulée ici.
- En attendant, les textures restent **procédurales dans la page** (canvas), ce
  qui garde les GLB petits et sans UV — voir `TinyHoopMK1/viz/gen_viewer.py`
  (tissage carbone, étiquette DOGCOM).
- **Compression Draco non activée** : elle exige l'encodeur natif
  (`draco_encoder`) plus un décodeur wasm côté client, tous deux absents de cet
  environnement. Les gains actuels (−64 %) viennent du binaire glTF lui-même ;
  Draco ajouterait typiquement −50 à −80 % sur la géométrie.
- Le `configurator.html` existant reste **procédural** (2/3/5/7"). Le brancher
  sur ces GLB est l'étape suivante, une fois les modèles GLB validés.
