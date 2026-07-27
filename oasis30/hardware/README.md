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
| Flanc latéral | **2** | TPU 95A | `../ref/sub250_stl/side_panel.stl` |
| Patin de pied | **4** | TPU 95A | `../ref/sub250_stl/foot_pad_x4.stl` (les 4 sur une planche) |
| Platine d'antennes RX | 1 | TPU 95A | `../ref/sub250_stl/rx_antenna_plate.stl` |
| Support d'antenne de queue | 1 | TPU 95A | `../ref/sub250_stl/tail_antenna_mount.stl` |

### Ajoutées par ce dépôt — absentes du kit

| Pièce | Qté | Matière | À quoi ça sert |
|---|---|---|---|
| `cam_cradle_bottom` | 1 | TPU 95A | tient la caméra O4 Pro inclinée à 30° |
| `cam_cradle_top` | 1 | TPU 95A | referme dessus, fenêtre d'objectif |
| `arm_guard` | **4** | TPU 95A | clip de bras + **canal pour les 3 fils de phase** |
| `batt_pad` | 1 | TPU 95A | patin antidérapant nervuré sous la sangle |
| `xt30_grommet` | 1 | TPU 95A | passe-fil de la découpe du roof |
| `rear_bumper` | 1 | TPU 95A | capuchon de la pointe arrière |
| `gps_mount` | 1 | PLA/PETG | platine GPS surélevée — **variante Stratos seulement** |

## Électronique

| | **Stock Sub250 (O4 Pro)** | **Stratos programmable** |
|---|---|---|
| FC / ESC | **RedFox A3 45A AIO** — STM32F722 · ICM42688-P · BLHeli32, montage 20×20 | **STRATOS TINYHOOP AIO** ([`../../hardware/pcb_tinyhoop/`](../../hardware/pcb_tinyhoop/)) |
| Firmware | Betaflight | `fc_core` ([`../../fc_core/`](../../fc_core/)) — manuel · stabilisé · programmé · essaim |
| Vidéo | **DJI O4 Pro** (air unit + caméra), montage 20×20 / 25,5 | idem O4 Pro |
| Radio | récepteur **ExpressLRS** 2,4 GHz (CRSF) | idem + **SX1262 LoRa 868** pour le lien PC/essaim |
| Position | — | flow + ToF, **GPS/compas** sur `gps_mount` |
| Antennes | antenne O4 Pro + antennes RX à plat | idem |
| Condensateur | 35 V faible ESR, couché sur le pont | idem |
| Buzzer | optionnel | optionnel |

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
