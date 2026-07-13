# 03 — Schéma : MCU ESP32-P4 + flash (38 composants)

Le cœur de la carte. Grosse puce (100 broches + pad exposé), donc on prend son
temps.

> 📄 **Câblage exact** : fiche **[fiches/blocs.md](fiches/blocs.md)**, section
> « Bloc 03 — MCU ESP32-P4 + FLASH ». Le mapping complet **broche→net** du P4 y
> est (100 broches), extrait de `design.py`.

## 1. Poser le P4 (U1)

- Symbole : **`Espressif:ESP32-P4`** (touche `A`). Réf `U1`, valeur `ESP32-P4NRW32`.
- Le symbole est probablement découpé en **plusieurs unités** (A, B, C…). Place
  toutes les unités (elles partagent la même réf U1).

### Alimentation du P4 — les règles à ne pas rater

Ces points sont **vérifiés** dans `KNOWN_GAPS.md` (§3 et §4). Respecte-les :

| Broches P4 | Net à mettre | Pourquoi |
|-----------|--------------|----------|
| VDD_HP_0 / VDD_HP_2 / VDD_HP_3 (cœur) | **`VDD_CORE`** | ~1.2 V du DC-DC U10. **JAMAIS 3V3** (puce morte). |
| VDD_LP, VDD_IO_0/4/5/6, VDD_LDO, VDD_DCDCC, VDD_ANA, VDD_BAT, VDD_USBPHY | `3V3` | entrées d'alim 3.0–3.6 V |
| VDDO_FLASH **et** VDD_FLASH_IO | `VDD_FLASHIO` | sortie LDO interne (3.3 V), alimente la flash |
| VDDO_PSRAM, VDD_PSRAM_0/1 | `VDD_PSRAM` | 1.8 V (PSRAM en boîtier). **Pas 3V3** (max 1.95 V). |
| VDDO_3, VDD_MIPI_DPHY | `VDD_MIPI` | 2.5 V (LDO interne configurable) |
| VDDO_4 | *(non connecté)* | LDO inutilisé |
| EN_DCDC | `EN_DCDC` | pilote l'enable de U10 |
| FB_DCDC | `FB_DCDC` | retour du DC-DC (point milieu R30/R31) |
| GND (pad exposé, broche 105) | `GND` | + thermique |

Les nets `VDD_CORE`, `EN_DCDC`, `FB_DCDC`, `VDD_MIPI`, `VDD_FLASHIO`,
`VDD_PSRAM` bouclent avec les composants d'alim du chapitre 02.

### Le reste des broches du P4

Recopie **toutes** les autres broches depuis la fiche blocs.md (U1). Les grandes
familles :

- **Flash QSPI** : `FLASH_CS`, `FLASH_CK`, `FLASH_IO0..3`.
- **Quartz** : `XTAL_P`, `XTAL_N`. **Reset/boot** : `CHIP_PU`, `GPIO0`, `BOOT`.
- **REXT** : `CSI_REXT`, `DSI_REXT` (résistances de précision vers GND).
- **USB** : `USB_DM_MCU`, `USB_DP_MCU` (viennent de D1).
- **Caméra CSI** (paires) : `CSI_CKP/CKN`, `CSI_D0P/D0N`, `CSI_D1P/D1N`.
- **Bus & GPIO fonctionnels** : SPI (`SPI_SCLK/MOSI/MISO`, `CS_IMU`, `CS_FLOW`,
  `IMU_INT`), I²C (`I2C_SDA/SCL`, `VL53_XSHUT`), SDIO vers le C6 (`SDIO_CLK/CMD`,
  `SDIO_D0..3`, `C6_EN`), moteurs (`M1_GATE`…`M4_GATE`), divers (`VBAT_SENSE`,
  `LED_DIN`, `CAM_PWDN`, `EXP_IO`, `U0TXD`, `U0RXD`).

> 🎯 **Astuce anti-erreur** : coche chaque broche du P4 dans la fiche au fur et à
> mesure. C'est la partie où une inversion coûte cher.

## 2. Flash QSPI (U2, W25Q128)

- Symbole : générique 8 broches (`Memory_Flash:W25Q128JVSIQ` s'il existe, sinon
  `Device:...` 8 broches / une puce SOIC-8 générique). Empreinte
  `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`.
- Câblage (fiche) : 1 `FLASH_CS`, 2 `FLASH_IO1`, 3 `FLASH_IO2`, 4 `GND`,
  5 `FLASH_IO0`, 6 `FLASH_CK`, 7 `FLASH_IO3`, 8 **`VDD_FLASHIO`** (⚠️ pas 3V3 :
  alimentée par le rail flash du P4).

## 3. Quartz / reset / boot / REXT

- **Y1 = 40 MHz** (4 broches) : 1 `XTAL_P`, 2 `GND`, 3 `XTAL_N`, 4 `GND`.
- **C8 = C9 = 10 pF** : charges du quartz (sur XTAL_P / XTAL_N vers GND).
  > Ajuste-les selon la CL réelle du quartz choisi (`KNOWN_GAPS.md` §11).
- **Reset** : **R9 = 10 kΩ** (3V3→`CHIP_PU`), **C10 = 1 µF** (`CHIP_PU`→GND),
  **SW1 = bouton** (`CHIP_PU`→GND).
- **Boot** : **SW2 = bouton** (`BOOT`→GND), **R10 = 10 kΩ** (3V3→`BOOT`).
  > ⚠️ On suppose que le strap de boot = GPIO35 → à **vérifier** (`KNOWN_GAPS.md` §5).
- **REXT** : **R11 = 4.02 kΩ** (`CSI_REXT`→GND), **R12 = 4.02 kΩ** (`DSI_REXT`→GND)
  — valeurs imposées par le checklist Espressif (`KNOWN_GAPS.md` §12).

## 4. Pull-ups

- **Flash** : **R13/R14/R15 = 10 kΩ** de `VDD_FLASHIO` vers `FLASH_CS`,
  `FLASH_IO2`, `FLASH_IO3` (le pull suit le rail flash, pas 3V3).
- **SDIO** : **R16–R20 = 51 kΩ** de `3V3` vers `SDIO_CMD`, `SDIO_D0..3`.
- **C6 boot** : **R21 = 10 kΩ** de `3V3` vers `C6_BOOT` (run normal du C6).

## 5. Découplage du P4

- **C11 = 100 nF** sur `VDD_CORE`.
- **C12 à C25 = 100 nF** (14 pièces) : découplage des rails 3V3 du P4, un par
  cluster de broches d'alim. À placer **au plus près** des broches lors du PCB.
- **C26 = C27 = 10 µF** (0603) : réservoir (bulk) 3V3.

## Vérification du bloc

- 38 composants posés (fiche blocs.md).
- Les nets `VDD_CORE`, `EN_DCDC`, `FB_DCDC`, `VDD_MIPI`, `VDD_FLASHIO`,
  `VDD_PSRAM` doivent maintenant apparaître **des deux côtés** (alim ch.02 ↔ P4).

➡️ **[04_schema_c6_wifi.md](04_schema_c6_wifi.md)**
