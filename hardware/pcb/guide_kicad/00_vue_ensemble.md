# 00 — Vue d'ensemble

## Ce qu'on construit

La carte contrôleur du STRATOSDRONE : un PCB **4 couches, 38 × 74 mm**, format
**portrait « Tello »** (~1:2), qui se glisse dans la coque imprimée
(`../../frame/tello_style/`). C'est le cerveau du drone :

- **MCU principal ESP32-P4** (U1) : double cœur RISC-V, PSRAM 32 Mo intégrée,
  encodeur H.264 matériel — il gère le vol **et** la caméra.
- **Co-processeur Wi-Fi ESP32-C6-MINI-1** (U3), relié au P4 en **SDIO**
  (protocole esp-hosted) : c'est lui qui fait le Wi-Fi 6.
- **Flash QSPI 16 Mo** (U2, W25Q128) pour le firmware du P4.
- **Caméra MIPI-CSI** au nez de la carte (connecteur FFC 15 broches, J4).
- **Capteurs de vol** : IMU (U6), baromètre (U7), télémètre ToF (U8, dessous),
  flux optique (U9, dessous).
- **Alimentation 1S** : entrée batterie LiPo (J1) + charge USB-C (U4 TP4056),
  buck 3V3 (U5), DC-DC dédié au cœur du P4 (U10).
- **4 sorties moteurs brushed** (Q1–Q4) aux quatre coins, 2 LEDs d'état
  (LED1/LED2), connecteurs d'extension et de debug.

## Architecture physique (repères de placement)

L'origine `y = 0` est au **nez** (la caméra). En descendant :

```
   y=0  ┌─────────────┐   ← nez : connecteur caméra FFC (J4)
        │  CAPTEURS    │   IMU / baro / ToF+flux (dessous)
        │  ESP32-C6    │   zone RF (module Wi-Fi, U3 ~y=18)
        │  ESP32-P4    │   zone CPU (U1 ~y=39) + flash + quartz
        │  ALIM        │   buck 3V3, DC-DC cœur, découplage
   y=74  │  USB-C / BAT │   ← arrière : charge + connecteur batterie
        └─────────────┘
   coins : 4 pads moteurs + 4 trous de montage M2
```

Les deux capteurs qui regardent vers le **sol** (U8 ToF, U9 flux optique) sont
sur la **face arrière (dessous)**, avec une **fenêtre sans cuivre** dans le plan
de masse du dessous pour qu'ils aient un champ de vision dégagé.

## Les 4 couches

| Couche | Rôle |
|--------|------|
| **F.Cu** (dessus) | signaux + plan GND de remplissage |
| **In1.Cu** (interne 1) | plan **GND** |
| **In2.Cu** (interne 2) | plan **3V3** |
| **B.Cu** (dessous) | signaux + plan **VBAT** (avec fenêtre capteurs) |

## Plan de travail A → Z

On procède comme un vrai design KiCad : **schéma d'abord, PCB ensuite.**

1. **Projet + bibliothèques** (ch. 01) — créer le projet, ajouter les symboles et
   empreintes, dont les 3 vendored du repo (ESP32-P4, ESP32-C6, PMW3901).
2. **Schéma, bloc par bloc** (ch. 02→06) — poser les composants et les câbler
   avec des **labels de net globaux** portant les noms exacts de `design.py`.
   On avance par blocs fonctionnels : alim → MCU → Wi-Fi → capteurs → moteurs/IO.
3. **ERC + empreintes** (ch. 07) — vérifier les règles électriques, associer une
   empreinte à chaque composant.
4. **PCB** (ch. 08→11) — stackup 4 couches, contour 38×74, placement, zones de
   cuivre, routage (avec les paires différentielles USB/CSI en premier).
5. **DRC + fabrication** (ch. 12) — contrôle des règles, export des gerbers, du
   perçage, de la BOM et du CPL pour **JLCPCB**.

## Ce dont tu as besoin

- **KiCad 9** (installé). Le chapitre 01 détaille l'installation si besoin.
- Ce dossier `guide_kicad/` (le guide + les fiches).
- Le dossier `../lib/` du repo (symboles + empreintes vendored).
- De la patience : ~112 composants. Fais-le **par bloc**, sauvegarde souvent,
  lance l'ERC régulièrement.

## Règle d'or : les noms de nets

Tout le secret pour obtenir **exactement** la même carte que le repo, c'est de
nommer les nets **à l'identique** de `design.py`. Chaque fois que tu poses un
label, prends le nom dans **[`fiches/nets.md`](fiches/nets.md)** ou
**[`fiches/blocs.md`](fiches/blocs.md)**. Deux broches qui portent le même nom de
label sont électriquement reliées — c'est comme ça qu'on câble sans tirer des
fils partout.

➡️ Chapitre suivant : **[01_projet_et_librairies.md](01_projet_et_librairies.md)**
