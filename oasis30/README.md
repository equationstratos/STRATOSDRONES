# OASIS 30 — le build Stratos sur châssis Sub250 OasisFly30

Un **3 pouces, 150 mm d'entraxe**, monté sur le châssis
[Sub250 OasisFly30](https://sub250.com/products/sub250-oasisfly30-frame) :
tout le châssis re-modélisé en paramétrique (**STEP** + **STL**), les pièces
imprimées qui manquent au kit, et un **visualisateur 3-D** + **simulateur
d'assemblage** dans le navigateur.

```bash
python3 oasis30/cad/prep_sub250.py   # prépare les STL Sub250 d'origine
python3 oasis30/cad/export.py        # -> cad/step/*.step + cad/stl/*.stl + contrôles
python3 oasis30/viz/gen_viewer.py    # -> viz/drone_viewer.html + build/build.html
```

| | |
|---|---|
| **[`viz/drone_viewer.html`](viz/)** | le visualisateur — ouvrir par double-clic |
| **[`build/build.html`](build/)** | le simulateur d'assemblage, 23 pièces à emboîter |
| **[`cad/step/`](cad/step/)** | un `.step` par pièce + `oasisfly30_assembly.step` |
| **[`cad/stl/`](cad/stl/)** | les `.stl` d'impression (et `stl/viz/` pour le web) |
| **[`ref/`](ref/)** | les 4 STL Sub250 d'origine + les photos + [`MEASURES.md`](ref/MEASURES.md) |
| **[`hardware/README.md`](hardware/)** | la nomenclature complète, deux variantes |

## Géométrie

| | |
|---|---|
| Entraxe | **150 mm** en diagonale — **125 × 82,9** (X large, pas carré) |
| Moteurs | aux points **(±62,5 ; ±41,46)**, entraxe M2 9×9 |
| Hélices | **3″ · 76,2 mm** |
| Longueur hors-tout | **132 mm** · hauteur **32,5 mm** |
| Plaques | basse **2,5** · médiane **2,5** · pont **2,5** · roof **2,0** |
| Bras | **3,0 mm**, pris en sandwich entre la basse et la médiane |
| Entretoises | **20 mm** M3, posées sur le pont |
| Stack | **20 × 20** (perçage VTX **25,5**) |
| Dégagement hélices | **6,7 mm** avant/arrière · 48,8 mm latéral |

Tout est piloté par [`cad/tune.py`](cad/tune.py) : un seul fichier à toucher.

## Les pièces

### Carbone et métal — 12 pièces, toutes imprimables pour un montage d'essai

`bottom_plate` · `mid_plate` · `deck_plate` · `top_plate` (roof) ·
`arm` ×4 · `cam_side_plate` ×2 · `standoff` ×6.

Sur le vrai châssis ce sont des plaques **découpées** dans du carbone : les
`.stl` servent alors de gabarit, et les `.step` vont directement chez l'atelier
de découpe. Mais on peut aussi **tout imprimer** pour valider l'assemblage et
la place des composants avant de commander le carbone — c'est le principal
usage des STL de plaques.

### Imprimé — ce que Sub250 livre déjà

Repris **tels quels**, jamais redessinés, dans [`ref/sub250_stl/`](ref/sub250_stl/) :
flanc latéral (×2) · patin de pied (×4) · platine d'antennes RX ·
support d'antenne de queue.

### Imprimé — ce qui manque, et qu'on ajoute

`cam_cradle_bottom` + `cam_cradle_top` (berceau caméra O4 Pro incliné à 30°) ·
`arm_guard` ×4 (clip de bras **avec canal pour les 3 fils de phase**) ·
`batt_pad` (patin antidérapant nervuré) · `xt30_grommet` (passe-fil du roof) ·
`gps_mount` (variante Stratos) · `rear_bumper` (capuchon de pointe arrière).

## Le visualisateur

Même recette que les autres visualisateurs du dépôt — page **autonome**,
Three.js embarqué, aucun fichier externe, ouvrable par double-clic.

- **23 composants** affichables/masquables, chacun avec son sélecteur de couleur.
- **Sélecteur d'électronique** : *stock Sub250* (RedFox A3 45A AIO + DJI O4 Pro)
  ou *Stratos programmable* (carte TINYHOOP AIO + LoRa 868 + GPS).
- Clic sur une pièce → surbrillance + description ; vue **éclatée** ;
  fil de fer ; thème clair ; **plein écran** (touche `F`).
- **Mode assemblage** : les 23 pièces attendent autour du drone, leur logement
  est marqué par un fantôme bleu, un double-clic dans la liste les emboîte.

Les deux pages sortent du **même générateur** : le simulateur ne peut pas
diverger du visualisateur, il n'y a qu'une seule définition de chaque pièce.
Et les STL du visualisateur sont produits par `cad/export.py` en même temps
que ceux d'impression — la 3-D montre donc bien ce qui sortira de l'imprimante.

## Réglages d'impression

- **TPU 95A** pour tout ce qui commence par `cam_cradle`, `arm_guard`,
  `batt_pad`, `xt30_grommet`, `rear_bumper` — buse 0,4 · couche 0,2 ·
  3 périmètres · 20 % gyroïde · **sans support** · 25-30 mm/s.
- **PLA-CF ou PETG** pour `gps_mount`.
- **Plaques et bras d'essai** : PLA-CF, couche 0,15, **4 périmètres**, 40 %
  — assez rigide pour un montage à blanc, **pas pour voler**.
- `arm_guard` : imprimer **×4**, canal côté intérieur.
- Les pièces Sub250 d'origine : suivre leurs propres recommandations.

## Astuces de montage (les pièges déjà réglés)

1. **Moteurs d'abord**, vis M2 par le dessous, frein-filet, et vérifier
   qu'aucune vis ne touche le bobinage.
2. Passer les **3 fils de phase** par bras **avant** de clipser les `arm_guard`.
3. La cage caméra a un écart intérieur de **24,7 mm** : c'est le **berceau TPU**
   qui rentre dedans, pas la caméra nue. Se tromper là oblige à tout démonter.
4. **Souder l'XT30 en dernier**, condensateur d'abord — plus de place au fer.
5. Faire passer le fil de batterie par la **découpe du roof** (avec le
   passe-fil) : il descend droit sur les pads de l'ESC au lieu de frotter sur
   un bord carbone.
6. Antennes **avant** de remonter les flancs : ils cachent les soudures.
7. `CLR = 0,25 mm` dans `tune.py` est le premier paramètre à toucher si ton
   imprimante sort serré ou lâche.

## Honnêteté

Le châssis est **re-modélisé d'après les cotes publiées et les photos** du kit,
pas exporté du CAO d'origine. Les cotes principales — entraxe, longueur,
hauteur, épaisseurs — sont justes et recoupées (voir
[`ref/MEASURES.md`](ref/MEASURES.md), qui donne la source de chaque chiffre et
liste ce qui reste estimé). Les **détails de contour, d'allègements et de
perçages secondaires sont plausibles, pas relevés** : avant de lancer une
découpe carbone, faire un montage à blanc sur le vrai châssis.

Les 4 pièces Sub250, elles, sont les fichiers d'origine — donc exactes.

`cad/export.py` contrôle 11 cotes à chaque export et **échoue** si l'une dérive.
Le visualisateur est passé au test d'interférence pièce par pièce : **0 collision**
sur 82 maillages. Mais ce test compare des boîtes englobantes — il attrape les
interpénétrations franches, pas les contacts tangents, et ne remplace pas un
contrôle booléen. Rien n'a été imprimé ni volé.

## Crédits

Châssis **OasisFly30** conçu par **Sub250** — les 4 STL de `ref/sub250_stl/`
sont leurs fichiers, redistribués tels quels. Le reste (modèle paramétrique,
pièces imprimées complémentaires, visualisateur) est le travail Stratos Drones.
