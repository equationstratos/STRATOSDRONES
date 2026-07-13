# Guide KiCad — reconstruire la PCB STRATOSDRONE de A à Z

Ce dossier est un **guide pas-à-pas en français** pour redessiner **à la main**,
dans **KiCad 9**, la carte contrôleur du STRATOSDRONE, à l'identique de celle du
repo (`../stratosdrone.kicad_pcb`).

La carte du repo est aujourd'hui **générée par code** : la source de vérité est
`../scripts/design.py` (111 composants, 83 nets). Il n'existe pas de vrai schéma
câblé à la main. Ce guide te fait donc dessiner toi-même le schéma puis le PCB,
en respectant exactement le même netlist — pour que tu comprennes et maîtrises
chaque bloc.

## Comment utiliser ce guide

1. Lis d'abord **[`00_vue_ensemble.md`](00_vue_ensemble.md)** : l'architecture de
   la carte et le plan de travail.
2. Suis les chapitres **dans l'ordre**. Chaque chapitre = une étape concrète dans
   KiCad, avec les clics, les valeurs et les pièges.
3. Garde les **fiches de référence** (dossier [`fiches/`](fiches/)) ouvertes à
   côté : elles contiennent, extraits fidèlement de `design.py`, la liste des
   composants, le **câblage broche→net de chaque bloc**, les empreintes et la BOM.

## Sommaire

| # | Chapitre | Contenu |
|---|----------|---------|
| — | [00_vue_ensemble](00_vue_ensemble.md) | Architecture, specs carte, plan A→Z |
| 01 | [01_projet_et_librairies](01_projet_et_librairies.md) | Créer le projet, ajouter les bibliothèques (dont les vendored du repo) |
| 02 | [02_schema_alimentation](02_schema_alimentation.md) | Batterie, USB-C, charge, buck 3V3, DC-DC cœur |
| 03 | [03_schema_mcu_p4_flash](03_schema_mcu_p4_flash.md) | ESP32-P4, quartz, reset/boot, flash QSPI, découplage |
| 04 | [04_schema_c6_wifi](04_schema_c6_wifi.md) | Co-processeur Wi-Fi ESP32-C6 (SDIO) |
| 05 | [05_schema_capteurs_camera](05_schema_capteurs_camera.md) | IMU, baro, ToF, flux optique, caméra CSI |
| 06 | [06_schema_moteurs_leds_io](06_schema_moteurs_leds_io.md) | Drivers moteurs, LEDs, connecteurs |
| 07 | [07_erc_et_empreintes](07_erc_et_empreintes.md) | ERC, association des empreintes |
| 08 | [08_pcb_setup_et_contour](08_pcb_setup_et_contour.md) | Stackup 4 couches, règles, contour, trous M2 |
| 09 | [09_pcb_placement](09_pcb_placement.md) | Placement dessus/dessous, fenêtre capteurs |
| 10 | [10_pcb_zones](10_pcb_zones.md) | Plans de masse/alim + ouverture capteurs |
| 11 | [11_pcb_routage](11_pcb_routage.md) | Paires différentielles, alim, signaux |
| 12 | [12_drc_fab_et_commande](12_drc_fab_et_commande.md) | DRC, export gerbers/BOM/CPL, commande JLCPCB |

## Fiches de référence (générées)

Ne pas éditer à la main : elles sont produites par
[`fiches/gen_reference.py`](fiches/gen_reference.py) depuis `../scripts/design.py`.
Après toute modification de `design.py`, régénère-les :

```bash
python3 fiches/gen_reference.py
```

| Fiche | Contenu |
|-------|---------|
| [fiches/composants.md](fiches/composants.md) | Tableau complet des 111 composants |
| [fiches/nets.md](fiches/nets.md) | Netlist : chaque net et ses broches (noms à respecter) |
| [fiches/blocs.md](fiches/blocs.md) | Câblage broche→net, bloc par bloc |
| [fiches/empreintes.md](fiches/empreintes.md) | Empreintes et leur bibliothèque source |
| [fiches/bom.md](fiches/bom.md) | Nomenclature groupée avec codes LCSC |

## ⚠️ Avant de commander la carte

Ce design a des points à vérifier (pinouts caméra, straps de boot, etc.) :
lis **[`../KNOWN_GAPS.md`](../KNOWN_GAPS.md)** avant toute fabrication. Le
chapitre 12 rappelle la checklist.
