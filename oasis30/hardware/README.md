# OASIS 30 — nomenclature complète

Tout ce qu'il faut pour assembler le drone, en deux colonnes : la version
**stock Sub250** (celle qui se vend, sous Betaflight) et la version
**Stratos programmable** (le châssis avec le cerveau du dépôt). Les deux
partagent exactement le même châssis et la même motorisation.

Les deux variantes sont sélectionnables dans le visualisateur
([`../viz/drone_viewer.html`](../viz/)) — c'est la même liste que ci-dessous.

## Châssis — identique aux deux variantes

| Pièce | Qté | Matière | Source |
|---|---|---|---|
| Plaque basse | 1 | carbone 2,5 mm | `../cad/step/bottom_plate.step` |
| Plaque médiane | 1 | carbone 2,5 mm | `../cad/step/mid_plate.step` |
| Pont étroit (« splint ») | 1 | carbone 2,5 mm | `../cad/step/deck_plate.step` |
| Roof (plaque haute) | 1 | carbone 2,0 mm | `../cad/step/top_plate.step` |
| Bras | **4** | carbone 3,0 mm | `../cad/step/arm.step` |
| Joue de cage caméra | **2** | carbone 2,5 mm | `../cad/step/cam_side_plate.step` |
| Entretoise lisse M3 × 20 mm | **6** | aluminium | `../cad/step/standoff.step` |
| Vis M2 (moteurs) | 16 | inox | + frein-filet |
| Vis M3 (entretoises, bras) | ~14 | inox | |
| Écrous nylstop M3 | 8 | | |
| Sangle de batterie | 2 | | |

## Pièces imprimées

### Livrées par Sub250 — fichiers d'origine, repris tels quels

| Pièce | Qté | Matière | Fichier |
|---|---|---|---|
| Flanc latéral gauche | 1 | TPU 95A | `../cad/stl/flanc_gauche.stl` |
| Flanc latéral droit | 1 | TPU 95A | `../cad/stl/flanc_droit.stl` (miroir du gauche) |
| Patin de pied | **4** | TPU 95A | `../ref/sub250_stl/foot_pad_x4.stl` (les 4 sur une planche) |
| Platine d'antennes RX | 1 | TPU 95A | `../ref/sub250_stl/rx_antenna_plate.stl` |
| Support d'antenne de queue | 1 | TPU 95A | `../ref/sub250_stl/tail_antenna_mount.stl` |

### Ajoutées par ce dépôt — absentes du kit

| Pièce | Qté | Matière | À quoi ça sert |
|---|---|---|---|
| `arm_guard` | **4** | TPU 95A | clip de bras + **canal pour les 3 fils de phase** |
| `batt_pad` | 1 | TPU 95A | patin antidérapant nervuré sous la sangle |
| `xt30_grommet` | 1 | TPU 95A | passe-fil de la découpe du roof |
| `rear_bumper` | 1 | TPU 95A | capuchon de la pointe arrière |
| `gps_mount` | 1 | PLA/PETG | platine GPS surélevée — **variante Stratos seulement** |
| `cam_cradle_bottom` + `_top` | (0) | TPU 95A | **non montés** — le STEP DJI montre que la caméra O4 Pro a ses propres tourillons et bascule nue entre les joues. À n'imprimer que pour une caméra qui n'en a pas. |

## Électronique

| | **Stock Sub250 (O4 Pro)** | **Stratos programmable** |
|---|---|---|
| FC / ESC | **RedFox A3 45A AIO** — STM32F722 · ICM42688-P · BLHeli32, montage 20×20 | **STRATOS TINYHOOP AIO** ([`../../hardware/pcb_tinyhoop/`](../../hardware/pcb_tinyhoop/)) |
| Firmware | Betaflight | `fc_core` ([`../../fc_core/`](../../fc_core/)) — manuel · stabilisé · programmé · essaim |
| Vidéo | **DJI O4 Pro** (air unit + caméra), fixation **25,5 × 25,5** | idem O4 Pro |
| Radio | récepteur **ExpressLRS** 2,4 GHz (CRSF) | idem + **SX1262 LoRa 868** pour le lien PC/essaim |
| Position | — | flow + ToF, **GPS/compas** sur `gps_mount` |
| Antennes | **2 antennes O4 Pro** dans les alésages Ø 3 mm du support de queue + antennes RX à plat sur leur platine | idem |
| Condensateur | 35 V faible ESR, couché sur le pont | idem |
| Buzzer | optionnel | optionnel |

### Fichiers 3-D du constructeur

Les trois STEP DJI de [`../ref/vendor_step/`](../ref/vendor_step/) sont repris
tels quels et convertis par [`../cad/prep_dji_o4.py`](../cad/prep_dji_o4.py) :

| Pièce | Fichier | Cotes lues dans le STEP |
|---|---|---|
| Caméra O4 Pro | `DJI_O4_PRO_CAM.step` | 25,4 × 23,8 × 20,0 · tourillons Ø 2,1 en y = ±10 |
| Air unit O4 Pro | `DJI_O4_AIR_UNIT_PRO.step` | 33,4 carré × 13,0 · fixation 25,5 × 25,5 |
| Antenne O4 Pro | `DJI_O4_Pro_Antenna_v1.step` | fourreau Ø 3,5 · 85 mm utiles |

## Motorisation — identique aux deux variantes

| Pièce | Qté | Référence |
|---|---|---|
| Moteurs | **4** | **1404 · 4500 KV**, entraxe M2 9 × 9 mm |
| Hélices | **4** (2 CW + 2 CCW) | **3″ · 76 mm** tri-pale (HQProp / Gemfan) |
| Batterie | 1-2 | **LiPo 4S 660-720 mAh**, connecteur **XT30** |

## Au sol

| Pièce | Pour quoi |
|---|---|
| Radiocommande ExpressLRS | pilotage — les deux variantes |
| Lunettes DJI | vidéo O4 Pro |
| Dongle LoRa (Heltec LoRa32 V3) | **variante Stratos** — lien PC et essaim, [`../../sdk/lora_dongle/`](../../sdk/lora_dongle/) |
| Chargeur LiPo 4S + sac de charge | |

## Masse

Sub250 annonce **170 g ± 3** pour le drone complet sans batterie (version
stock O4 Pro). Une 4S 660 mAh pèse ~75 g, soit **~245 g en ordre de vol** —
au-dessus des 250 g, il faut donc l'enregistrer et respecter la
réglementation applicable pour cette classe.

Ce chiffre est **celui du constructeur**, pas une pesée : les pièces de ce
dépôt n'ont pas été imprimées, et la variante Stratos n'a jamais volé.

## Ce que la variante Stratos ne fait pas encore

La carte STRATOS TINYHOOP AIO et son firmware sont **développés et testés sur
hôte**, pas volés. Tant que ce n'est pas fait, la version qui vole est la
version stock, sous Betaflight — elle est complète et cohérente ci-dessus.
Voir [`../../TinyHoopMK1/ROADMAP.md`](../../TinyHoopMK1/ROADMAP.md) pour l'état réel.
