# 07 — ERC + association des empreintes

Le schéma est fini. Avant de passer au PCB : vérifier les règles électriques
(ERC), puis coller une **empreinte** à chaque composant.

## 1. ERC (Electrical Rules Check)

Éditeur de schéma → **Inspecter → Vérification des règles électriques**
(ou l'icône « coccinelle »). Clique **Exécuter**.

### Ce qui doit disparaître

- **« net non piloté par une source »** sur `3V3`, `VBAT`, `VBUS`, `GND`,
  `VDD_CORE`, `VDD_MIPI` → ajoute un **`power:PWR_FLAG`** sur le net concerné.
- **Broches non connectées** que tu veux vraiment laisser en l'air (ex. P4
  VDDO_4, VL53L1X pin 8 DNC) → pose le symbole **« No Connect »** (`Q`) dessus.

### Ce qui est normal (ne pas s'affoler)

- Les **6 nets à une seule broche** (`CAM_GPIO`, `CHRG_N`, `GPIO0`, `LED_DOUT`,
  `STDBY_N`, `TOF_INT`) : ce sont des points de test / sorties état / straps.
  Tu peux poser un No-Connect ou les laisser en warning documenté.
- Des warnings de type « type de pin » sur des modules (P4, C6) selon la
  définition du symbole.

🎯 **Objectif** : zéro **erreur**. Les quelques warnings ci-dessus sont tolérés
et documentés.

## 2. Numérotation (au besoin)

Si tu as laissé des références « U? » : **Outils → Annoter le schéma**. Mais
comme on a mis les références à la main (U1, R5…) pour coller à `design.py`,
**n'utilise PAS** la ré-annotation automatique qui les rencommerait. Vérifie
juste qu'il n'y a pas de doublon ni de « ? ».

## 3. Associer les empreintes

Deux méthodes — la plus simple ici : renseigner l'empreinte **dans chaque
symbole** (champ *Footprint*), ce que tu as peut-être déjà fait en posant les
composants. Sinon, l'outil dédié :

**Outils → Assigner les empreintes** (Footprint Assignment).

Pour chaque composant, choisis l'empreinte **exacte** de la fiche
**[fiches/empreintes.md](fiches/empreintes.md)**. Rappels des cas particuliers :

| Composant | Empreinte | Bibliothèque |
|-----------|-----------|--------------|
| U1 (P4) | `ESP32-P4` | `Espressif` (vendored) |
| U3 (C6) | `ESP32-C6-MINI-1` | `Espressif` (vendored) |
| U9 (flux) | `PMW3901MB-TXQT` | `strat` (vendored) |
| U8 (ToF) | `ST_VL53L1x` | `Sensor_Distance` (KiCad) |
| U7 (baro) | `Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering` | `Package_LGA` |
| J2 (USB-C) | `USB_C_Receptacle_HRO_TYPE-C-31-M-12` | `Connector_USB` |
| J4 (caméra) | `Hirose_FH12-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal` | `Connector_FFC-FPC` |

> La fiche empreintes.md liste **toutes** les correspondances (37 empreintes),
> avec la source de chacune. Les 0402/0805/SOT-23/SOIC sont dans les libs KiCad
> standard.

## 4. (Vérif utile) Comparer au netlist du repo

Tu peux exporter ton netlist (**Fichier → Exporter → Netlist**) et le comparer
mentalement à **[fiches/nets.md](fiches/nets.md)** : mêmes noms de nets, mêmes
broches. C'est le meilleur moyen de confirmer que ton schéma **est** celui de la
carte du repo.

## 5. Passer au PCB

Ouvre l'éditeur de PCB → **Outils → Mettre à jour le PCB depuis le schéma**
(`F8`). Tous les composants arrivent en tas avec leur **chevelu** (ratsnest =
les liaisons à router). C'est le point de départ du placement.

➡️ **[08_pcb_setup_et_contour.md](08_pcb_setup_et_contour.md)**
