# 12 — DRC, export fabrication et commande JLCPCB

Dernière ligne droite : vérifier, exporter les fichiers de fab, commander.

## 1. DRC (Design Rules Check)

Éditeur de PCB → **Inspecter → Vérification des règles de conception** →
**Exécuter**.

Cible : **zéro erreur**. Traite en priorité :

- **Clearances** insuffisantes (pistes/vias/pads trop proches).
- **Chevelu restant** (liaisons non routées) → il faut router les dernières.
- **Zones non remplies** → touche `B`.
- Trous/annulaires trop petits pour le procédé.

> Le repo note une densité forte autour du P4 (chevauchements de pads exposés,
> non bloquants pour JLCPCB — `KNOWN_GAPS.md` « Board Density »). Distingue les
> **vraies erreurs électriques** des artefacts de densité.

## 2. Sérigraphie / logo (optionnel)

La carte du repo ajoute un logo « STRATOS DRONES » sur la sérigraphie du dessous
(`scripts/add_logo.py`), dans la zone dégagée au-dessus de la fenêtre capteurs
(y < 27 mm). Tu peux ajouter un texte/logo équivalent sur **B.SilkS**, en évitant
les fenêtres optiques.

## 3. Export des gerbers + perçage

**Fichier → Tracer (Plot)** :

- Couches à tracer : `F.Cu, In1.Cu, In2.Cu, B.Cu, F.Paste, B.Paste, F.SilkS,
  B.SilkS, F.Mask, B.Mask, Edge.Cuts`.
- Format **Gerber X2**, dossier de sortie `gerbers/`.
- Clique **Générer les fichiers de perçage (Drill Files)** : format **Excellon**,
  PTH + NPTH (le repo produit `-PTH.drl` et `-NPTH.drl`).
- Zippe le dossier `gerbers/` pour l'upload.

> ⚠️ **Exporte depuis KiCad**, pas depuis `scripts/export_fab.py` : ce dernier
> exporte la carte **non routée** (il sert seulement de base). Le repo insiste
> là-dessus (`README.md` / `KNOWN_GAPS.md`).

## 4. Export BOM + CPL (pour l'assemblage PCBA)

- **BOM** : la nomenclature avec les codes **LCSC** est prête dans
  **[fiches/bom.md](fiches/bom.md)** (37 lignes, 102 composants posés). Le format
  colonnes JLC est dans `../jlcpcb/bom.csv` — tu peux t'en inspirer.
- **CPL (positions)** : **Fichier → Fabrication → Export des positions de
  composants** → CSV, unités mm, format compatible JLC. Réf : `../jlcpcb/cpl.csv`.
- Vérifie les **rotations** des composants critiques (VL53L1X, USB-C, QFN) — un
  décalage de rotation JLC est une source d'erreur classique.

## 5. Options de commande JLCPCB

D'après le `README.md` du repo :

1. PCB : **4 couches**, 1.6 mm, stackup **JLC04161H-7628** (impédance contrôlée
   USB/CSI), cuivre 0.5 oz ext / 0.5 oz int, finition **ENIG** (recommandée pour
   le QFN fin et les pads FFC).
2. Assemblage : **PCBA double face** (dessus : MCU/alim/plupart ; dessous : les 2
   capteurs). Upload `bom.csv` + `cpl.csv`.

## 6. ⚠️ Checklist AVANT de payer

**Lis [`../VERIFY_RESOLVED.md`](../VERIFY_RESOLVED.md)** (vérification approfondie
récente) puis **[`../ORDER_CHECKLIST.md`](../ORDER_CHECKLIST.md)** (checklist
finale bloquante), et enfin `../KNOWN_GAPS.md`. État des points VERIFY :

- §11 **quartz** : 🔴→🟢 **bug fatal corrigé** — l'ancien C9002 était un **12 MHz**
  (le P4 exige 40 MHz) ; remplacé par **C2831465** (40 MHz). Reste : régler C8/C9
  selon la **CL** du cristal commandé.
- §5 **straps de boot** : 🟢 GPIO35 confirmé + **R32** (pull-up GPIO36) ajoutée.
- §6 **caméra CSI** : 🟢 brochage FFC **conforme OV5647** (cible firmware) ; résidu
  faible = polarité P/N côté P4 (rattrapable firmware).
- §14 **empreinte USB-C** : 🟢 land KiCad = part HRO commandé, conforme.
- Densité / chevauchements autour du P4 (acceptable en proto, pas en série).

Les points §3, §4, §7, §8, §10, §12, §13 étaient **déjà résolus** dans `design.py`
(alim cœur, rails LDO, chargeur, capteurs, buck, REXT, fenêtre capteurs).

## 7. Comparer à la carte du repo

Ouvre `../stratosdrone.kicad_pcb` **à côté** de la tienne pour comparer placement,
zones et routage. Ton netlist doit être identique (mêmes noms de nets — c'est ce
qu'on a construit depuis le début).

---

🎉 **Terminé.** Tu as reconstruit la carte STRATOSDRONE de A à Z, à la main, dans
KiCad 9 — schéma, PCB, zones, routage et fichiers de fabrication.

⬅️ Retour au **[sommaire](README.md)**
