# 02 — Schéma : bloc ALIMENTATION (33 composants)

On commence par l'alimentation : c'est la colonne vertébrale et ça t'apprend la
méthode qu'on répétera pour tous les blocs.

> 📄 **Câblage exact** : garde ouverte la fiche
> **[fiches/blocs.md](fiches/blocs.md)**, section « Bloc 02 — ALIMENTATION ».
> Elle liste, pour **chaque** composant, sa valeur, son empreinte, son code LCSC
> et le **câblage broche→net**. Ce chapitre explique la logique et les pièges ;
> la fiche donne les valeurs à taper.

## La méthode (à réutiliser pour tous les blocs schéma)

1. **Poser un symbole** : touche `A` (Add Symbol), cherche le composant, clique
   pour le placer.
   - Résistances/condensateurs/inductances : `Device:R`, `Device:C`, `Device:L`.
   - Diodes : `Device:D` (ou `Diode:...`) ; MOSFET : `Device:Q_NMOS_DGS`.
   - Connecteurs : bibliothèque `Connector`.
2. **Nommer** : double-clic sur le symbole → mets la **Référence** (ex. `U5`) et
   la **Valeur** (ex. `SY8089AAAC`) **exactement** comme dans la fiche.
3. **Relier par labels** : plutôt que de tirer des fils partout, pose un
   **label global** (`Ctrl+L` ou icône « Net label / Global label ») sur chaque
   broche, avec le **nom de net** de la fiche. Deux labels identiques = reliés.
   - Pour les rails d'alim (`3V3`, `GND`, `VBAT`, `VBUS`, `VDD_CORE`, `VDD_MIPI`),
     utilise de préférence des **symboles d'alimentation** (`P` → Power Port,
     ex. `power:GND`, `power:+3V3` renommé, ou un power port générique portant le
     nom exact). Le résultat est le même : c'est le **nom** qui compte.
4. **PWR_FLAG** : sur les nets d'alimentation « sources » (VBAT, VBUS, 3V3, GND,
   VDD_CORE, VDD_MIPI), pose un symbole **`power:PWR_FLAG`** une fois par net.
   Ça évite les faux positifs ERC « net non piloté ». (Liste exacte : variable
   `POWER_NETS` de `design.py`.)
5. **Sauvegarde** (`Ctrl+S`) souvent.

> 💡 Les broches d'un condensateur/résistance ne sont pas polarisées : pad 1 et
> pad 2 sont interchangeables **sauf** pour les composants polarisés (diodes,
> certains électrolytiques). Respecte l'orientation indiquée pour D1, D2, D3–D6.

## Sous-bloc A — Entrée batterie + USB-C + charge

- **J1** : connecteur JST-PH 2 points, la batterie 1S LiPo. **pin 1 = VBAT (+)**,
  pin 2 = GND.
- **J2** : réceptacle **USB-C 16 broches** (`Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`).
  Les paires VBUS/GND doublées (A4/A9/B4/B9 = VBUS ; A1/A12/B1/B12/S1 = GND) sont
  normales sur l'USB-C. Les data : `USB_DP_C` / `USB_DM_C`.
- **R1, R2 = 5.1 kΩ** sur **CC1** et **CC2** vers GND : ce sont les pull-downs
  qui déclarent la carte comme **consommateur** (sink) → le chargeur fournit 5 V.
- **D1 = USBLC6-2SC6** : protection **ESD** des lignes USB. Côté connecteur :
  `USB_DP_C`/`USB_DM_C` ; côté MCU : `USB_DP_MCU`/`USB_DM_MCU`.
- **U4 = TP4056** (chargeur 1S) — ⚠️ **pièges vérifiés** :
  - pin 6 = **STDBY_N** (sortie état, collecteur ouvert) — **pas** relié à VBAT.
  - pin 8 = **CE** relié à **VBUS** (charge toujours activée quand alimenté).
  - pin 1 (TEMP) à GND = NTC désactivé (voulu).
  - **R3 = 1.2 kΩ** sur PROG fixe le courant ≈ 1.0 A (≈0.9 C pour le pack 1100 mAh).
- **C1 = 10 µF** sur VBUS, **C2 = 10 µF** sur VBAT.
- **D2 = SS34-DNP** : **NON POSÉ** (DNP). Diode Schottky VBUS→VBAT pour alimenter
  la carte au banc **sans batterie**. **Ne jamais la poser avec une batterie** :
  pas de partage de source.

## Sous-bloc B — Buck 3V3 (SY8089)

Convertit VBAT (3.0–4.2 V) en **3V3 / 2 A**.

- **U5 = SY8089AAAC** (SOT-23-5) : 1 EN, 2 GND, 3 SW, 4 VIN, 5 FB.
- **L1 = 10 µH** entre SW (`SW3V3`) et la sortie `3V3`.
  > La valeur imprimée est 10 µH car le vrai composant LCSC (C408412) est un
  > 10 µH — voir `KNOWN_GAPS.md` §10. Fonctionne, mais un 2.2–3.3 µH donnerait
  > une meilleure réponse transitoire.
- **C3 = 10 µF** (entrée VBAT), **C4 = 22 µF** (sortie 3V3).
- **Diviseur de retour** : **R4 = 453 kΩ** (3V3→FB3V3), **R5 = 100 kΩ**
  (FB3V3→GND) ⇒ 0.6·(1+453/100) ≈ **3.32 V**.
- **R6 = 100 kΩ** : pull-up de EN (`3V3_EN`) vers VBAT → buck **toujours actif**.

## Sous-bloc C — DC-DC cœur du P4 (TLV62569) — CRITIQUE

Le cœur CPU du P4 (**~1.2 V**) **ne se génère pas tout seul** : il faut un buck
externe dédié dont le P4 pilote l'enable et lit le retour. **Ne relie jamais le
cœur (`VDD_HP_*`) au 3V3** — ce serait ~2.75× la tension max = puce morte
(voir `KNOWN_GAPS.md` §3).

- **U10 = TLV62569DBVR** (SOT-23-5) : 1 EN(`EN_DCDC`), 2 GND, 3 SW(`SW_CORE`),
  4 VIN(`3V3`), 5 FB(`FB_DCDC`).
- **L2 = 2.2 µH** entre `SW_CORE` et **`VDD_CORE`** (la sortie).
- **C5 = 22 µF** sortie, **C36 = 10 µF** entrée.
- **Diviseur R30 = R31 = 453 kΩ** : rapport 1:1 → Vout = 2·Vfb (reproduit la
  tension cœur voulue par construction). **C37 = 20 pF** en feed-forward sur R30.
- Le net `EN_DCDC` vient du P4 (broche EN_DCDC), `FB_DCDC` = point milieu du
  diviseur, relié aussi au P4. Ces deux nets se terminent dans le bloc MCU (ch. 03).

## Sous-bloc D — Diviseur VBAT → ADC

- **R7 = R8 = 100 kΩ** : diviseur VBAT → `VBAT_SENSE` → GND (mesure de tension
  batterie par l'ADC du P4). **C6 = 100 nF** de filtrage sur `VBAT_SENSE`.

## Sous-bloc E — Découplage des rails LDO internes du P4

Le P4 a des LDO internes qui **sortent** des rails séparés (à ne pas relier au
3V3, voir `KNOWN_GAPS.md` §4). Chaque rail a son découplage :

- **VDD_MIPI** (2.5 V) : **C7 = 1 µF** + **C42 = 100 nF**.
- **VDD_FLASHIO** (3.3 V) : **C38 = 1 µF** + **C39 = 100 nF**.
- **VDD_PSRAM** (1.8 V) : **C40 = 1 µF** + **C41 = 100 nF**.

Ces trois rails prendront leur source **dans le P4** (ch. 03) ; ici on ne pose
que les condensateurs de découplage.

## Vérification du bloc

- Compare chaque composant posé à la fiche blocs.md (33 composants attendus).
- Lance un premier **ERC** (ch. 07) quand tu veux : à ce stade il signalera des
  nets « en attente » (normaux, ils se complètent dans les blocs suivants).

➡️ **[03_schema_mcu_p4_flash.md](03_schema_mcu_p4_flash.md)**
