# D'où vient chaque cote

Le châssis OasisFly30 est **re-modélisé**, pas issu du CAO d'origine de Sub250.
Ce fichier dit, cote par cote, sur quoi elle s'appuie — pour qu'on sache
exactement ce qui est mesuré et ce qui est estimé.

## 1. Mesuré sur `photos/dimensions.webp`

Le plan coté du constructeur. Échelle établie sur la cote 125 mm :
**730 px = 125 mm → 0,1712 mm/px**.

| Cote | Valeur | Comment |
|---|---|---|
| Entraxe diagonal | **150 mm** | coté sur le plan |
| Écartement latéral des moteurs | **125 mm** | coté sur le plan |
| Longueur hors-tout | **132 mm** | coté sur le plan |
| Écartement longitudinal | **82,92 mm** | déduit : √(150² − 125²) |
| Position des moteurs | **(±62,5 ; ±41,46)** | déduit des deux précédents |

**Recoupement indépendant** : sur l'image, l'écart vertical entre les axes
moteur avant et arrière mesure 485 px et l'écart latéral 730 px. Le rapport
485/730 = 0,664 ; le rapport calculé 82,92/125 = 0,663. Les deux tombent à
0,2 % près — la géométrie est donc bien un **X large**, pas un X carré.

Silhouette des plaques : relevée en balayant l'image ligne par ligne
(demi-largeurs consignées dans `../cad/tune.py`, variable `PROFILE_WIDE`).

| Y (mm) | largeur du corps |
|---|---|
| +60 | 37,2 (cage caméra) |
| +26 | 40,8 |
| 0 | 43,8 |
| −35 | 25,5 (poutre de queue) |
| −70 | 13,7 (pointe) |

## 2. Relevé dans les STL Sub250 d'origine

Mesures exactes, prises directement dans les fichiers de `sub250_stl/`.

| Pièce | Emprise | Ce qu'on en tire |
|---|---|---|
| `side_panel.stl` | 99,0 × 17,7 × **32,5** | **la hauteur hors-tout du châssis** |
| `foot_pad_x4.stl` | 4 patins de 17,3 × 17,7 × **11,2** | garde au sol sous les bras |
| `rx_antenna_plate.stl` | 29,6 × 29,7 × 5,9 | encombrement sur le roof |
| `tail_antenna_mount.stl` | 16,3 × 29,1 × 25,5 | encombrement en queue |

**Le recoupement le plus utile du projet** : l'empilage calculé à partir des
épaisseurs publiées — basse 2,5 + bras 3,0 + médiane 2,5 + pont 2,5 +
entretoise **20** (longueur du commerce) + roof 2,0 — donne **32,5 mm**, soit
exactement la hauteur du flanc Sub250 mesurée ci-dessus. Deux sources
indépendantes qui tombent sur le même chiffre : c'est ce qui valide la
longueur d'entretoise. `../cad/export.py` contrôle les deux à chaque export.

## 3. Publié par Sub250 et ses revendeurs

`sub250.com` renvoie une erreur 403 aux robots ; les valeurs viennent des
fiches produit Banggood, Unmanned Tech et Rotorama, concordantes entre elles.

| Cote | Valeur |
|---|---|
| Bras | **3,0 mm** (version O4 Pro ; 2,5 sur la version O3) |
| Plaque basse / médiane | **2,5 mm** |
| Roof | **2,0 mm** |
| Perçage FC | **20 × 20** |
| Perçage VTX | **20 × 20 / 25,5 × 25,5** |
| Moteurs | 1404 **4500 KV** |
| Batterie | 4S **660-720 mAh**, XT30 |
| Masse | **170 g ± 3** sans batterie |
| FC/ESC | RedFox A3 45A AIO — STM32F722 · ICM42688-P · BLHeli32 |

## 4. Lu sur les photos d'assemblage

`photos/chassis-sub250-oasisfly30-dji-o4-pro*.jpg` et les captures.

- Les **bras sont pris en sandwich** entre la plaque basse et la plaque
  médiane — visible sans ambiguïté sur la vue trois-quarts arrière.
- Le **roof est surélevé sur entretoises**, il ne touche pas la médiane.
- La **cage caméra** est faite de **deux joues carbone verticales** (le
  « splint » de 2,5 mm de la fiche technique), pas d'une pièce moulée.
- Un **patin de pied teal sous chaque patin moteur**.
- Le **support d'antenne de queue dépasse à l'arrière** du châssis.
- `photos/plaque.png` donne la nomenclature complète du kit : 4 plaques
  carbone, 4 bras, 2 joues de cage, 2 flancs, 4 patins, berceau caméra en
  deux parties, visserie, 4 entretoises, 2 sangles.

## 5. Estimé — à confirmer sur le vrai châssis

Ces valeurs sont marquées `# EST` dans `../cad/tune.py`. Elles n'ont **aucune**
source : ce sont des choix cohérents avec le reste, à reprendre après un
montage à blanc.

| Paramètre | Valeur retenue | Pourquoi il faut le vérifier |
|---|---|---|
| `STACK_Y` (recul du stack) | −6 mm | la position exacte du perçage n'est pas cotée |
| `CAM_H` (hauteur caméra) | 19 mm | dépend du modèle d'O4 Pro |
| `CAM_Z` (axe optique) | 18 mm | déduit de la cage, pas mesuré |
| `STANDOFFS_CAM` | (±13 ; 25) | position des entretoises avant |
| Section exacte du flanc Sub250 | — | ses lèvres recouvrent les plaques ; le
  recouvrement est **voulu**, mais son profil réel n'est pas connu |

## 6. Deux vis qui tombaient dans le vide

Le contrôle de marge au bord ajouté à `../cad/export.py` compare chaque perçage
à la silhouette **réelle** de la plaque, interpolée entre les points du profil.
Il a trouvé deux erreurs qu'un simple coup d'œil ne voit pas :

| Perçage | Position | Marge | Correction |
|---|---|---|---|
| Entretoise arrière | x = 13, y = −46 | **−1,7 mm** | rentrée à x = 9, avancée à y = −34 |
| Vis extérieure de bras | x = 25, y = −16,6 | **−7,3 mm** | rayon ramené de 30 à 25 mm |

La deuxième a révélé une erreur de fond : mon profil de plaque était un fuseau
lisse, alors que les photos montrent des **lobes** aux racines de bras — c'est
justement là que se trouve la matière autour des vis de fixation. Le profil a
été corrigé (demi-largeur 26 mm à y ≈ ±12). Marge la plus juste aujourd'hui :
**2,3 mm**, et `export.py` échoue si elle repasse en négatif.

## 7. Ce que les STEP du commerce ont tranché

Les fichiers de `vendor_step/` sont ceux des constructeurs. Lus dans gmsh, ils
donnent des cotes **exactes** — pas des estimations — et plusieurs d'entre
elles règlent des questions restées ouvertes :

| Cote | Valeur lue | Ce qu'elle décide |
|---|---|---|
| Largeur caméra hors tourillons | **23,8 mm** | l'écart intérieur de cage (24,7) est bon : la caméra rentre **nue**, il n'y a pas de berceau |
| Tourillons caméra | Ø 2,1 en (0 ; ±10 ; 0) | l'axe de bascule est bien un M2 percé dans les joues |
| Profondeur caméra | 25,4 mm | basculée à 30°, son coin arrière-bas descend à z = 3 |
| Air unit | 33,4 carré × 13,0 | tient dans les 43 mm de large du châssis |
| Fixation air unit | **25,5 × 25,5** | recoupe le perçage VTX relevé sur la médiane |
| Fourreau d'antenne | Ø 3,5 | les alésages du support de queue font Ø 3,0 : le TPU serre le fourreau, c'est bien lui qui passe dedans |
| Moteur XING2 1404 | Ø 19,9 × 18,6 | plan de pose à z = −4,25, haut de cloche à z = 9,54 |
| Haut de cloche | **z = 19,3** | plan de pose plaqué sur le bras (5,5) + 9,54 |
| Hauteur d'hélice | **z = 19,6** | posée sur la cloche, rondelle comprise — j'avais estimé 21,0 |

Les 148 mm de nappe droite du STEP caméra, le connecteur MMCX du STEP antenne
et les 25 mm de fils droits du STEP moteur sont **retirés à la conversion** : dans le drone ils sont pliés, et
`viz/gen_viewer.py` les retrace en courbe.

Ce qui reste estimé, malgré ces fichiers : **la position** de l'air unit dans
la baie (z = 13,5, au-dessus du stack de vol) et le tracé exact de la nappe et
des coaxiaux. Les pièces sont justes, leur placement est déduit des photos.

## 8. Limites de méthode

Une limite de méthode, pas une cote : le contrôle d'interférence du
visualisateur compare des **boîtes englobantes alignées sur les axes**. Pour
une pièce en diagonale — les bras — cette boîte couvre un grand rectangle
vide et signale des collisions qui n'existent pas. Les paires concernées sont
donc exclues explicitement du test, et listées comme telles dans le script.
Ce test détecte les interpénétrations franches ; il ne remplace pas un
contrôle booléen.
