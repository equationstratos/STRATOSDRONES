# OASIS 30 — le build Stratos sur châssis Sub250 OasisFly30

Un **3 pouces, 150 mm d'entraxe**, monté sur le châssis
[Sub250 OasisFly30](https://sub250.com/products/sub250-oasisfly30-frame) :
tout le châssis re-modélisé en paramétrique (**STEP** + **STL**), les pièces
imprimées qui manquent au kit, et un **visualisateur 3-D** + **simulateur
d'assemblage** dans le navigateur.

```bash
python3 oasis30/cad/prep_sub250.py   # prépare les STL Sub250 d'origine
python3 oasis30/cad/prep_vendor.py   # convertit les STEP du commerce (--ref pour le maillage fin)
python3 oasis30/cad/export.py        # -> cad/step/*.step + cad/stl/*.stl + contrôles
python3 oasis30/viz/gen_viewer.py    # -> viz/drone_viewer.html + build/build.html
```

| | |
|---|---|
| **[`viz/drone_viewer.html`](viz/)** | le visualisateur — ouvrir par double-clic |
| **[`build/build.html`](build/)** | le simulateur d'assemblage, 28 pièces à emboîter |
| **[`cad/step/`](cad/step/)** | un `.step` par pièce + `oasisfly30_assembly.step` |
| **[`cad/stl/`](cad/stl/)** | les `.stl` d'impression (et `stl/viz/` pour le web) |
| **[`ref/`](ref/)** | les 4 STL Sub250 d'origine + les photos + [`MEASURES.md`](ref/MEASURES.md) |
| **[`ref/vendor_step/`](ref/vendor_step/)** | les STEP du commerce — **DJI O4 Pro** et **moteur XING2 1404** |
| **[`hardware/README.md`](hardware/)** | la nomenclature complète, deux variantes |

## Géométrie

| | |
|---|---|
| Entraxe | **150 mm** en diagonale — **125 × 82,9** (X large, pas carré) |
| Moteurs | **XING2 1404** aux points **(±62,5 ; ±41,46)**, entraxe M2 9×9 |
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
flanc latéral · patin de pied (×4) · platine d'antennes RX ·
support d'antenne de queue.

Le flanc est livré en **un seul fichier, qui est le côté gauche** : `prep_sub250.py`
en écrit les deux versions imprimables, `cad/stl/flanc_gauche.stl` et
`cad/stl/flanc_droit.stl` (miroir, enroulement des triangles inversé pour que les
normales restent sortantes).

### Du commerce — les STEP constructeur, repris tels quels

Le dossier [`ref/vendor_step/`](ref/vendor_step/) contient les fichiers
d'origine : **caméra O4 Pro**, **air unit O4 Pro**, **antenne O4 Pro** et
**moteur XING2 1404**. `cad/prep_vendor.py` en tire les STL du visualisateur.
Ce sont eux qui ont tranché trois points du montage :

- la caméra porte ses **propres tourillons** Ø 2,1 mm en y = ±10, et mesure
  **23,8 mm** hors tourillons : elle bascule directement entre les deux joues
  carbone, dont l'écart intérieur fait 24,7 — **il n'y a pas de berceau** ;
- l'air unit fait **33,5 mm de côté** et se fixe en **25,5 × 25,5**, ce qui
  recoupe le perçage VTX relevé sur le châssis ;
- le moteur fait **Ø 19,9 × 18,6 mm** et son plan de pose est à z = −4,25 dans
  son fichier : plaqué sur la face haute du bras, il met le haut de cloche à
  **z = 19,3**, donc l'hélice à **19,6** — et non aux 21 mm que j'estimais.

### Imprimé — ce qui manque, et qu'on ajoute

`arm_guard` ×4 (clip de bras **avec canal pour les 3 fils de phase**) ·
`batt_pad` (patin antidérapant nervuré) · `xt30_grommet` (passe-fil du roof) ·
`gps_mount` (variante Stratos) · `rear_bumper` (capuchon de pointe arrière).

`cam_cradle_bottom` + `cam_cradle_top` restent exportés dans `cad/`, mais **ne
sont plus au montage** : ils ne servent qu'à une caméra dépourvue de tourillons.

## Le visualisateur

Même recette que les autres visualisateurs du dépôt — page **autonome**,
Three.js embarqué, aucun fichier externe, ouvrable par double-clic.

**Étiquette de version.** En haut à droite du bandeau, un badge vert du type
`r5 · 28/07 12:27 · cb1cdc2` : numéro de révision, date de génération, et le
commit présent au moment où la page a été produite. Le même texte est dans le
titre de l'onglet, dans un commentaire à la première ligne du fichier, et dans
`window.__build`. C'est le seul moyen sûr de savoir si la page ouverte est bien
la dernière ou si le navigateur ressert une version en cache — le fichier fait
7 Mo, il est mis en cache volontiers. En cas de doute : **Ctrl+Maj+R**.

- **28 composants** affichables/masquables, chacun avec son sélecteur de couleur —
  flanc gauche et flanc droit y figurent séparément, la caméra et l'air unit O4
  Pro aussi, et **chaque antenne VTX a son propre groupe** pour pouvoir être
  écartée en V indépendamment de l'autre.
- **Sélecteur d'électronique** : *stock Sub250* (RedFox A3 45A AIO + DJI O4 Pro)
  ou *Stratos programmable* (carte TINYHOOP AIO + LoRa 868 + GPS).
- Clic sur une pièce → surbrillance + description ; vue **éclatée** ;
  fil de fer ; thème clair ; **plein écran** (touche `F`).
- **Déplacement à la souris** : attrape n'importe quelle pièce dans la vue et
  fais-la glisser. Le déplacement se fait dans le plan de l'écran, donc il reste
  intuitif quel que soit l'angle de la caméra ; **Maj** enfoncé, seule la hauteur
  bouge. Un clic dans le vide fait toujours tourner la scène.
- **Panneau « Réglages »** : six curseurs (X/Y/Z en mm, RX/RY/RZ en degrés) sur
  **chacune des 28 pièces**. Chaque groupe pivote **sur lui-même** — son origine
  est ramenée au centre de la pièce, pas au centre du drone, sinon une rotation
  la promènerait autour du châssis. La caméra O4 Pro fait exception voulue : son
  pivot **est** l'axe de bascule, donc le curseur RX règle son inclinaison.
  Les valeurs s'affichent en bas du panneau et se copient d'un bouton : c'est ce
  qu'on recopie dans le générateur pour figer un calage, au lieu de chercher une
  orientation à l'aveugle.
- **Mode assemblage** : les 28 pièces attendent autour du drone, leur logement
  est marqué par un fantôme bleu, un double-clic dans la liste les emboîte.

Les deux pages sortent du **même générateur** : le simulateur ne peut pas
diverger du visualisateur, il n'y a qu'une seule définition de chaque pièce.
Et les STL du visualisateur sont produits par `cad/export.py` en même temps
que ceux d'impression — la 3-D montre donc bien ce qui sortira de l'imprimante.

## Réglages d'impression

- **TPU 95A** pour `arm_guard`, `batt_pad`, `xt30_grommet`, `rear_bumper`
  (et `cam_cradle_*` si tu montes une caméra sans tourillons) — buse 0,4 · couche 0,2 ·
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
3. La cage caméra a un écart intérieur de **24,7 mm** et la caméra O4 Pro fait
   **23,8 mm** hors tourillons : elle rentre nue, sur l'axe M2 percé dans les
   joues à (0 ; 55 ; 18). Basculée à 30°, son coin arrière-bas descend à z = 3 —
   c'est normal, la médiane ne fait plus que 11 mm de large à cette hauteur.
4. **Souder l'XT30 en dernier**, condensateur d'abord — plus de place au fer.
5. Faire passer le fil de batterie par la **découpe du roof** (avec le
   passe-fil) : il descend droit sur les pads de l'ESC au lieu de frotter sur
   un bord carbone.
6. Antennes **avant** de remonter les flancs : ils cachent les soudures. Les
   deux fourreaux vidéo s'enfilent dans les **alésages Ø 3 mm du support de
   queue** (17,3 mm de profondeur, entraxe 21,4 mm — cotes relevées dans le STL
   Sub250, pas estimées). Le support se pose **sur le roof, à l'extrême
   arrière, basculé à 45°** : les antennes partent vers l'arrière *et vers le
   haut*, comme sur le drone monté. Ses deux alésages sont **parallèles** — si
   les tiennes s'écartent en V, c'est le montage qui les cintre.
   La platine RX descend alors dans la **baie arrière**, posée sur le pont :
   les deux ne tiennent pas sur les 36 mm de roof libres à l'arrière.
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

Les 4 pièces Sub250 et les 3 pièces DJI O4 Pro, elles, sont les fichiers
d'origine — donc exactes. En revanche **leur placement dans le drone** reste
mon travail : les cotes des pièces sont justes, leur position est déduite des
photos et des points d'accroche du châssis.

`cad/export.py` contrôle 11 cotes à chaque export et **échoue** si l'une dérive.
Le visualisateur est passé au test d'interférence pièce par pièce : **0 collision**
sur 90 maillages. Mais ce test compare des boîtes englobantes — il attrape les
interpénétrations franches, pas les contacts tangents, et ne remplace pas un
contrôle booléen. Rien n'a été imprimé ni volé.

## Crédits

Châssis **OasisFly30** conçu par **Sub250** — les 4 STL de `ref/sub250_stl/`
sont leurs fichiers, redistribués tels quels. Le reste (modèle paramétrique,
pièces imprimées complémentaires, visualisateur) est le travail Stratos Drones.
