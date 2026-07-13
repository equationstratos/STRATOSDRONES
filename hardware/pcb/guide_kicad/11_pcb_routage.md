# 11 — PCB : routage

C'est l'étape la plus longue. Ordre conseillé : **paires différentielles d'abord**
(elles imposent leur tracé), puis alim, puis le reste des signaux.

> 📄 Le repo a un guide de routage dédié : **[`../ROUTING.md`](../ROUTING.md)**
> (stratégies, autorouteurs Freerouting/DeepPCB, et pourquoi le routage headless
> a échoué dans le sandbox). Le netlist à router est **[fiches/nets.md](fiches/nets.md)**.

## 1. Paires différentielles (en premier)

Ces signaux rapides doivent être routés en **paires appariées**, courtes, avec un
plan de référence continu dessous.

| Paire | Nets | Remarque |
|-------|------|----------|
| USB données (côté C) | `USB_DP_C` / `USB_DM_C` | de J2 à D1 |
| USB données (côté MCU) | `USB_DP_MCU` / `USB_DM_MCU` | de D1 à U1 |
| CSI horloge | `CSI_CKP` / `CSI_CKN` | J4 ↔ U1 |
| CSI data0 | `CSI_D0P` / `CSI_D0N` | J4 ↔ U1 |
| CSI data1 | `CSI_D1P` / `CSI_D1N` | J4 ↔ U1 |
| Quartz | `XTAL_P` / `XTAL_N` | Y1 ↔ U1, très court |

- Utilise l'outil **Router les paires différentielles** de KiCad (`6` puis
  sélection, ou l'icône dédiée).
- Impédance : stackup **JLC04161H-7628** (choisi au ch. 08) pour l'impédance
  contrôlée. Garde les longueurs appariées et évite les vias inutiles sur ces
  paires.
- Le générateur **exclut** ces paires de l'autoroutage justement pour les traiter
  à part — fais pareil.

## 2. Alimentation

- **VBAT, 3V3, GND** : largement portés par les **plans** (In1=GND, In2=3V3,
  B=VBAT, F=GND). Il reste à **descendre** des broches vers les plans par des
  **vias** (ex. broche 3V3 d'une puce → via → plan In2.Cu).
- **VDD_CORE** (sortie U10) : piste dédiée courte et large jusqu'aux broches
  cœur du P4 + son cap C11/C5.
- Rails LDO (`VDD_FLASHIO`, `VDD_PSRAM`, `VDD_MIPI`) : pistes courtes vers leurs
  caps (C7/C42, C38/C39, C40/C41) et les broches concernées.
- Boucles de découplage : cap → broche alim → GND aussi courtes que possible.

## 3. Signaux

Route ensuite, par bus (fiche nets.md) :

- **SPI** : `SPI_SCLK/MOSI/MISO`, `CS_IMU`, `CS_FLOW`, `IMU_INT` (U6, U9/J3 ↔ U1).
- **I²C** : `I2C_SDA`, `I2C_SCL` (U7, U8, J4, J9 ↔ U1) + `VL53_XSHUT`.
- **SDIO** (P4 ↔ C6) : `SDIO_CLK/CMD/D0..3` — court, appairé en longueur si
  possible.
- **Flash QSPI** : `FLASH_CS/CK/IO0..3` (U1 ↔ U2), courtes.
- **Moteurs** : `M1_GATE`…`M4_GATE`, drains `M*_D` (larges, courant), `LED_DIN`
  chaîné.
- Divers : `VBAT_SENSE`, `CAM_PWDN`, `EXP_IO`, `U0TXD/RXD`, `BOOT`, `CHIP_PU`…

## 4. Astuces & réalités du board dense

- Le chevelu (ratsnest, touche `F` pour l'afficher/masquer) te montre les
  liaisons restantes.
- **Autour du P4 (QFN 100), c'est dense** : le repo signale qu'un routeur greedy
  simple (une passe par net) **ne suffit pas** — il faut du **push-and-shove**
  (le routeur interactif de KiCad le fait : mode « Highlight collisions » /
  « Shove »). Voir `KNOWN_GAPS.md` §1 et `ROUTING.md`.
- Options si tu veux aider : autorouteur externe **DeepPCB.ai** (upload du
  `.dsn`), ou **Freerouting sur une vraie machine graphique** (pas headless).
  Détails et fichiers dans `../ROUTING.md`.

## 5. Re-remplir les zones

Après routage : **`B`** (remplir), pour que les plans épousent les pistes. À
refaire à chaque modif avant l'export.

## Vérification

- Chevelu vide (0 liaison non routée) — KiCad l'indique en bas.
- Zones remplies.
- On passe à la DRC au chapitre suivant.

➡️ **[12_drc_fab_et_commande.md](12_drc_fab_et_commande.md)**
