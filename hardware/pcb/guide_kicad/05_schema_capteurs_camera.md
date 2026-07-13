# 05 — Schéma : capteurs + caméra (12 composants)

Les capteurs de vol et la caméra. Attention aux **pinouts** (plusieurs bugs ont
déjà été corrigés ici, voir `KNOWN_GAPS.md` §6, §8, §9).

> 📄 Fiche **[fiches/blocs.md](fiches/blocs.md)**, section « Bloc 05 — CAPTEURS +
> CAMÉRA » : câblage broche→net vérifié de chaque capteur.

## 1. IMU ICM-42688-P (U6) — SPI

- Empreinte : `Package_DFN_QFN:DHVQFN-14-1EP_2.5x3mm_P0.5mm_EP1x1.5mm`
  (substitut générique — le vrai LGA-14 reste à dessiner, `KNOWN_GAPS.md` §8 ;
  le **netlist**, lui, est correct).
- Câblage vérifié (fiche) : 1 `SPI_MISO`, 4 `IMU_INT`, **5 `3V3` (VDDIO)**,
  **8 `3V3` (VDD)**, 12 `CS_IMU`, 13 `SPI_SCLK`, 14 `SPI_MOSI`, le reste `GND`.
  > ⚠️ Les broches 5 et 8 sont les **alims** — elles vont au 3V3, pas à GND.
- **C28 = C29 = 100 nF** de découplage (3V3/GND).

## 2. Baromètre SPL06-001 (U7) — I²C (0x76)

- Empreinte : `Package_LGA:Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering`.
- Câblage vérifié : 1/2/7 `GND`, **3 `I2C_SDA`**, **4 `I2C_SCL`**, 5 `3V3` (CSB
  haut = mode I²C), 6 `3V3` (VDDIO), 8 `3V3` (VDD). SDO (pin 2) à GND ⇒ adresse
  **0x76**.
- **C30 = 100 nF**.

## 3. ToF VL53L1X (U8) — I²C (0x29), **face DESSOUS**

- Empreinte : `Sensor_Distance:ST_VL53L1x` (empreinte officielle KiCad).
- **Face : B (dessous)** — regarde vers le sol. Dans le symbole, mets le champ
  qui l'indiquera au PCB ; concrètement tu le passeras sur la couche B au
  placement (ch. 09).
- Câblage vérifié : 1 `3V3`, 5 `VL53_XSHUT`, 7 `TOF_INT`, 9 `I2C_SDA`,
  10 `I2C_SCL`, 11 `3V3`, le reste `GND`. Broche 8 = DNC (laissée **flottante**).
- **C31 = 100 nF** (face dessous aussi).

## 4. Flux optique PMW3901 (U9) — SPI, **face DESSOUS**

- Empreinte : **`strat:PMW3901MB-TXQT`** (vendored, ajoutée au ch. 01).
- Pas de symbole vendored → utilise un **symbole générique** (ex. un boîtier
  8 broches `Device:...`) avec les broches nommées selon la fiche : 1 `3V3`,
  2 `GND`, 3 `SPI_SCLK`, 4 `SPI_MOSI`, 5 `SPI_MISO`, 6 `CS_FLOW`, 7 `GND`,
  8 `3V3`.
- **C32 = 100 nF** (face dessous).
- **J3 = header 2×4 (DNP)** : solution de repli = module externe **CJMCU-3901**
  (mêmes signaux SPI). On pose l'empreinte mais **non montée** (DNP). Voir
  `KNOWN_GAPS.md` §9 : soit tu poses **U9**, soit tu utilises **J3**, pas les deux.

## 5. Caméra MIPI-CSI (J4) — FFC 15 broches

- Empreinte : `Connector_FFC-FPC:Hirose_FH12-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal`.
- Câblage : paires CSI `CSI_D0N/D0P`, `CSI_D1N/D1P`, `CSI_CKN/CKP` intercalées de
  `GND`, plus `CAM_PWDN`, `CAM_GPIO`, `I2C_SCL`, `I2C_SDA`, `3V3`.
  > ✅ **Vérifié conforme OV5647** (`../VERIFY_RESOLVED.md` §6) : le firmware cible
  > la caméra **OV5647** (= Raspberry Pi Camera v1.3) et le brochage FFC de J4
  > **correspond** au standard OV5647/RPi v1.3 (lanes, GND, alims, I²C).
  > Résidu faible : la **polarité P/N** côté pads du P4 n'est pas re-vérifiée
  > contre l'EVK P4 — en général rattrapable **côté firmware** (config lanes MIPI).
- **C33 = 1 µF** (3V3/GND).

## Vérification du bloc

- 12 composants. U8, U9, C31, C32 sont sur la **face dessous** (tu confirmeras au
  placement).
- Les bus `I2C_SDA/SCL` et `SPI_*` relient maintenant capteurs ↔ P4.

➡️ **[06_schema_moteurs_leds_io.md](06_schema_moteurs_leds_io.md)**
