<!-- Fiche générée par fiches/gen_reference.py depuis scripts/design.py — NE PAS éditer à la main. -->

# Fiche — Câblage par bloc fonctionnel

Pour chaque bloc : les composants à poser puis, pour chacun, le câblage **broche → net**. Câble chaque broche à un **label de net global** portant le nom indiqué (colonne Net). Les broches d'un même net partagent donc le même label — pas besoin de tirer un fil d'un bout à l'autre de la feuille.

## Bloc 02 — ALIMENTATION  (33 composants)

Chapitre du guide : `02_schema_alimentation.md`

### Entrée batterie + USB-C + charge TP4056

- **J1** — BATT_PH2 · `Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal` · LCSC C160404
  - Câblage : 1→`VBAT` · 2→`GND`
- **J2** — USB-C-16P · `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` · LCSC C165948
  - Câblage : A1→`GND` · A12→`GND` · A4→`VBUS` · A5→`CC1` · A6→`USB_DP_C` · A7→`USB_DM_C` · A9→`VBUS` · B1→`GND` · B12→`GND` · B4→`VBUS` · B5→`CC2` · B6→`USB_DP_C` · B7→`USB_DM_C` · B9→`VBUS` · S1→`GND`
- **R1** — 5.1k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25905
  - Câblage : 1→`CC1` · 2→`GND`
- **R2** — 5.1k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25905
  - Câblage : 1→`CC2` · 2→`GND`
- **D1** — USBLC6-2SC6 · `Package_TO_SOT_SMD:SOT-23-6` · LCSC C7519
  - Câblage : 1→`USB_DP_C` · 2→`GND` · 3→`USB_DM_C` · 4→`USB_DM_MCU` · 5→`VBUS` · 6→`USB_DP_MCU`
- **U4** — TP4056-42-ESOP8 · `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.81mm` · LCSC C16581
  - Câblage : 1→`GND` · 2→`PROG` · 3→`GND` · 4→`VBUS` · 5→`VBAT` · 6→`STDBY_N` · 7→`CHRG_N` · 8→`VBUS` · 9→`GND`
- **R3** — 1.2k · `Resistor_SMD:R_0402_1005Metric` · LCSC C4180
  - Câblage : 1→`PROG` · 2→`GND`
- **C1** — 10uF · `Capacitor_SMD:C_0805_2012Metric` · LCSC C15850
  - Câblage : 1→`VBUS` · 2→`GND`
- **C2** — 10uF · `Capacitor_SMD:C_0805_2012Metric` · LCSC C15850
  - Câblage : 1→`VBAT` · 2→`GND`
- **D2** — SS34-DNP · `Diode_SMD:D_SMA` · LCSC C8678  _(DNP)_
  - Câblage : 1→`VBAT` · 2→`VBUS`

### Buck 3V3 (SY8089)

- **U5** — SY8089AAAC · `Package_TO_SOT_SMD:SOT-23-5` · LCSC C78988
  - Câblage : 1→`3V3_EN` · 2→`GND` · 3→`SW3V3` · 4→`VBAT` · 5→`FB3V3`
- **L1** — 10uH · `Inductor_SMD:L_0805_2012Metric` · LCSC C408412
  - Câblage : 1→`SW3V3` · 2→`3V3`
- **C3** — 10uF · `Capacitor_SMD:C_0805_2012Metric` · LCSC C15850
  - Câblage : 1→`VBAT` · 2→`GND`
- **C4** — 22uF · `Capacitor_SMD:C_0805_2012Metric` · LCSC C45783
  - Câblage : 1→`3V3` · 2→`GND`
- **R4** — 453k · `Resistor_SMD:R_0402_1005Metric` · LCSC C123734
  - Câblage : 1→`3V3` · 2→`FB3V3`
- **R5** — 100k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25741
  - Câblage : 1→`FB3V3` · 2→`GND`
- **R6** — 100k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25741
  - Câblage : 1→`3V3_EN` · 2→`VBAT`

### DC-DC cœur ~1.2V (TLV62569)

- **U10** — TLV62569DBVR · `Package_TO_SOT_SMD:SOT-23-5` · LCSC C141836
  - Câblage : 1→`EN_DCDC` · 2→`GND` · 3→`SW_CORE` · 4→`3V3` · 5→`FB_DCDC`
- **L2** — 2.2uH · `Inductor_SMD:L_Cenker_CKCS3015` · LCSC C43389
  - Câblage : 1→`SW_CORE` · 2→`VDD_CORE`
- **C5** — 22uF · `Capacitor_SMD:C_0805_2012Metric` · LCSC C45783
  - Câblage : 1→`VDD_CORE` · 2→`GND`
- **C36** — 10uF · `Capacitor_SMD:C_0805_2012Metric` · LCSC C15850
  - Câblage : 1→`3V3` · 2→`GND`
- **C37** — 20pF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1554
  - Câblage : 1→`VDD_CORE` · 2→`FB_DCDC`
- **R30** — 453k · `Resistor_SMD:R_0402_1005Metric` · LCSC C123734
  - Câblage : 1→`VDD_CORE` · 2→`FB_DCDC`
- **R31** — 453k · `Resistor_SMD:R_0402_1005Metric` · LCSC C123734
  - Câblage : 1→`FB_DCDC` · 2→`GND`

### Diviseur VBAT -> ADC

- **R7** — 100k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25741
  - Câblage : 1→`VBAT` · 2→`VBAT_SENSE`
- **R8** — 100k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25741
  - Câblage : 1→`VBAT_SENSE` · 2→`GND`
- **C6** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`VBAT_SENSE` · 2→`GND`

### Découplage des rails LDO internes du P4

- **C7** — 1uF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C52923
  - Câblage : 1→`VDD_MIPI` · 2→`GND`
- **C42** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`VDD_MIPI` · 2→`GND`
- **C38** — 1uF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C52923
  - Câblage : 1→`VDD_FLASHIO` · 2→`GND`
- **C39** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`VDD_FLASHIO` · 2→`GND`
- **C40** — 1uF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C52923
  - Câblage : 1→`VDD_PSRAM` · 2→`GND`
- **C41** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`VDD_PSRAM` · 2→`GND`

## Bloc 03 — MCU ESP32-P4 + FLASH  (39 composants)

Chapitre du guide : `03_schema_mcu_p4_flash.md`

### MCU ESP32-P4 (U1) + flash QSPI (U2)

- **U1** — ESP32-P4NRW32 · `strat:ESP32-P4` · LCSC C22387510
  - Câblage : 7→`I2C_SDA` · 8→`I2C_SCL` · 9→`3V3` · 10→`SPI_SCLK` · 11→`SPI_MOSI` · 12→`SPI_MISO` · 13→`CS_IMU` · 14→`CS_FLOW` · 15→`SDIO_D0` · 16→`SDIO_D1` · 17→`SDIO_D2` · 18→`SDIO_D3` · 19→`SDIO_CLK` · 20→`SDIO_CMD` · 21→`3V3` · 22→`VBAT_SENSE` · 23→`IMU_INT` · 24→`EXP_IO` · 25→`VL53_XSHUT` · 26→`VDD_CORE` · 27→`FLASH_CS` · 28→`FLASH_IO1` · 29→`FLASH_IO2` · 30→`VDD_FLASHIO` · 31→`FLASH_IO3` · 32→`FLASH_CK` · 33→`FLASH_IO0` · 34→`DSI_REXT` · 41→`VDD_MIPI` · 42→`CSI_D0N` · 43→`CSI_D0P` · 44→`CSI_CKP` · 45→`CSI_CKN` · 46→`CSI_D1N` · 47→`CSI_D1P` · 48→`CSI_REXT` · 49→`USB_DM_MCU` · 50→`USB_DP_MCU` · 51→`3V3` · 52→`LED_DIN` · 53→`CAM_PWDN` · 59→`VDD_PSRAM` · 62→`3V3` · 66→`BOOT` · 67→`VDD_PSRAM` · 68→`GPIO36_STRAP` · 69→`U0TXD` · 70→`U0RXD` · 71→`VDD_FLASHIO` · 72→`VDD_PSRAM` · 73→`VDD_MIPI` · 75→`3V3` · 76→`VDD_CORE` · 77→`3V3` · 78→`FB_DCDC` · 79→`EN_DCDC` · 85→`3V3` · 87→`M1_G` · 88→`M2_G` · 89→`M3_G` · 90→`M4_G` · 91→`VDD_CORE` · 96→`3V3` · 98→`C6_EN` · 99→`XTAL_N` · 100→`XTAL_P` · 101→`3V3` · 102→`3V3` · 103→`CHIP_PU` · 104→`GPIO0` · 105→`GND`
- **U2** — W25Q128JVSIQ · `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` · LCSC C97521
  - Câblage : 1→`FLASH_CS` · 2→`FLASH_IO1` · 3→`FLASH_IO2` · 4→`GND` · 5→`FLASH_IO0` · 6→`FLASH_CK` · 7→`FLASH_IO3` · 8→`VDD_FLASHIO`

### Quartz 40 MHz / reset / boot / REXT

- **Y1** — 40MHz · `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` · LCSC C2831465
  - Câblage : 1→`XTAL_P` · 2→`GND` · 3→`XTAL_N` · 4→`GND`
- **C8** — 10pF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1555
  - Câblage : 1→`XTAL_P` · 2→`GND`
- **C9** — 10pF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1555
  - Câblage : 1→`XTAL_N` · 2→`GND`
- **R9** — 10k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25744
  - Câblage : 1→`3V3` · 2→`CHIP_PU`
- **C10** — 1uF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C52923
  - Câblage : 1→`CHIP_PU` · 2→`GND`
- **SW1** — RESET · `Button_Switch_SMD:SW_SPST_CK_RS282G05A3` · LCSC C720477
  - Câblage : 1→`CHIP_PU` · 2→`GND`
- **SW2** — BOOT · `Button_Switch_SMD:SW_SPST_CK_RS282G05A3` · LCSC C720477
  - Câblage : 1→`BOOT` · 2→`GND`
- **R10** — 10k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25744
  - Câblage : 1→`3V3` · 2→`BOOT`
- **R32** — 10k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25744
  - Câblage : 1→`3V3` · 2→`GPIO36_STRAP`
- **R11** — 4.02k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25752
  - Câblage : 1→`CSI_REXT` · 2→`GND`
- **R12** — 4.02k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25752
  - Câblage : 1→`DSI_REXT` · 2→`GND`

### Pull-ups flash QSPI

- **R13** — 10k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25744
  - Câblage : 1→`VDD_FLASHIO` · 2→`FLASH_CS`
- **R14** — 10k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25744
  - Câblage : 1→`VDD_FLASHIO` · 2→`FLASH_IO2`
- **R15** — 10k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25744
  - Câblage : 1→`VDD_FLASHIO` · 2→`FLASH_IO3`

### Pull-ups SDIO (bus vers le C6)

- **R16** — 51k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25905
  - Câblage : 1→`3V3` · 2→`SDIO_CMD`
- **R17** — 51k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25905
  - Câblage : 1→`3V3` · 2→`SDIO_D0`
- **R18** — 51k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25905
  - Câblage : 1→`3V3` · 2→`SDIO_D1`
- **R19** — 51k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25905
  - Câblage : 1→`3V3` · 2→`SDIO_D2`
- **R20** — 51k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25905
  - Câblage : 1→`3V3` · 2→`SDIO_D3`

### Pull-up boot du C6

- **R21** — 10k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25744
  - Câblage : 1→`3V3` · 2→`C6_BOOT`

### Découplage P4 + bulk

- **C11** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`VDD_CORE` · 2→`GND`
- **C12** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C13** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C14** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C15** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C16** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C17** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C18** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C19** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C20** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C21** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C22** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C23** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C24** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C25** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C26** — 10uF · `Capacitor_SMD:C_0603_1608Metric` · LCSC C19702
  - Câblage : 1→`3V3` · 2→`GND`
- **C27** — 10uF · `Capacitor_SMD:C_0603_1608Metric` · LCSC C19702
  - Câblage : 1→`3V3` · 2→`GND`

## Bloc 04 — Wi-Fi ESP32-C6  (1 composants)

Chapitre du guide : `04_schema_c6_wifi.md`

### Co-processeur Wi-Fi (esp-hosted, esclave SDIO)

- **U3** — ESP32-C6-MINI-1 · `strat:ESP32-C6-MINI-1` · LCSC C3013606
  - Câblage : 1→`GND` · 2→`GND` · 3→`3V3` · 8→`C6_EN` · 11→`GND` · 14→`GND` · 23→`C6_BOOT` · 24→`SDIO_CMD` · 25→`SDIO_CLK` · 26→`SDIO_D0` · 27→`SDIO_D1` · 28→`SDIO_D2` · 29→`SDIO_D3` · 30→`C6_U0RXD` · 31→`C6_U0TXD` · 36→`GND` · 37→`GND` · 38→`GND` · 39→`GND` · 40→`GND` · 41→`GND` · 42→`GND` · 43→`GND` · 44→`GND` · 45→`GND` · 46→`GND` · 47→`GND` · 48→`GND` · 49→`GND` · 50→`GND` · 51→`GND` · 52→`GND` · 53→`GND`

## Bloc 05 — CAPTEURS + CAMÉRA  (12 composants)

Chapitre du guide : `05_schema_capteurs_camera.md`

### IMU ICM-42688-P (SPI)

- **U6** — ICM-42688-P · `Package_DFN_QFN:DHVQFN-14-1EP_2.5x3mm_P0.5mm_EP1x1.5mm` · LCSC C2840095
  - Câblage : 1→`SPI_MISO` · 2→`GND` · 3→`GND` · 4→`IMU_INT` · 5→`3V3` · 6→`GND` · 7→`GND` · 8→`3V3` · 9→`GND` · 10→`GND` · 11→`GND` · 12→`CS_IMU` · 13→`SPI_SCLK` · 14→`SPI_MOSI` · 15→`GND`
- **C28** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`
- **C29** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`

### Baromètre SPL06-001 (I²C 0x76)

- **U7** — SPL06-001 · `Package_LGA:Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering` · LCSC C2684428
  - Câblage : 1→`GND` · 2→`GND` · 3→`I2C_SDA` · 4→`I2C_SCL` · 5→`3V3` · 6→`3V3` · 7→`GND` · 8→`3V3`
- **C30** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`3V3` · 2→`GND`

### ToF VL53L1X (I²C 0x29, dessous)

- **U8** — VL53L1X · `Sensor_Distance:ST_VL53L1x` · LCSC C2970716  _(dessous)_
  - Câblage : 1→`3V3` · 2→`GND` · 3→`GND` · 4→`GND` · 5→`VL53_XSHUT` · 6→`GND` · 7→`TOF_INT` · 9→`I2C_SDA` · 10→`I2C_SCL` · 11→`3V3` · 12→`GND`
- **C31** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525  _(dessous)_
  - Câblage : 1→`3V3` · 2→`GND`

### Flux optique PMW3901 (SPI, dessous) + header de repli

- **U9** — PMW3901MB · `strat:PMW3901MB-TXQT` · LCSC C2920328  _(dessous)_
  - Câblage : 1→`3V3` · 2→`GND` · 3→`SPI_SCLK` · 4→`SPI_MOSI` · 5→`SPI_MISO` · 6→`CS_FLOW` · 7→`GND` · 8→`3V3`
- **C32** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525  _(dessous)_
  - Câblage : 1→`3V3` · 2→`GND`
- **J3** — FLOW_HDR · `Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical`  _(dessous)_  _(DNP)_
  - Câblage : 1→`3V3` · 2→`CS_FLOW` · 3→`GND` · 4→`SPI_SCLK` · 5→`SPI_MOSI` · 6→`SPI_MISO` · 7→`GND` · 8→`3V3`

### Caméra MIPI-CSI (FFC 15 broches)

- **J4** — CAM_FFC15 · `Connector_FFC-FPC:Hirose_FH12-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal` · LCSC C2884418
  - Câblage : 1→`GND` · 2→`CSI_D0N` · 3→`CSI_D0P` · 4→`GND` · 5→`CSI_D1N` · 6→`CSI_D1P` · 7→`GND` · 8→`CSI_CKN` · 9→`CSI_CKP` · 10→`GND` · 11→`CAM_PWDN` · 12→`CAM_GPIO` · 13→`I2C_SCL` · 14→`I2C_SDA` · 15→`3V3`
- **C33** — 1uF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C52923
  - Câblage : 1→`3V3` · 2→`GND`

## Bloc 06 — MOTEURS + LEDS + IO  (27 composants)

Chapitre du guide : `06_schema_moteurs_leds_io.md`

### 4 drivers moteurs (NFET low-side + flyback + pads)

- **Q1** — AO3400A · `Package_TO_SOT_SMD:SOT-23` · LCSC C20917
  - Câblage : 1→`M1_D` · 2→`GND` · 3→`M1_GATE`
- **Q2** — AO3400A · `Package_TO_SOT_SMD:SOT-23` · LCSC C20917
  - Câblage : 1→`M2_D` · 2→`GND` · 3→`M2_GATE`
- **Q3** — AO3400A · `Package_TO_SOT_SMD:SOT-23` · LCSC C20917
  - Câblage : 1→`M3_D` · 2→`GND` · 3→`M3_GATE`
- **Q4** — AO3400A · `Package_TO_SOT_SMD:SOT-23` · LCSC C20917
  - Câblage : 1→`M4_D` · 2→`GND` · 3→`M4_GATE`
- **R22** — 100R · `Resistor_SMD:R_0402_1005Metric` · LCSC C25092
  - Câblage : 1→`M1_G` · 2→`M1_GATE`
- **R23** — 100R · `Resistor_SMD:R_0402_1005Metric` · LCSC C25092
  - Câblage : 1→`M2_G` · 2→`M2_GATE`
- **R24** — 100R · `Resistor_SMD:R_0402_1005Metric` · LCSC C25092
  - Câblage : 1→`M3_G` · 2→`M3_GATE`
- **R25** — 100R · `Resistor_SMD:R_0402_1005Metric` · LCSC C25092
  - Câblage : 1→`M4_G` · 2→`M4_GATE`
- **R26** — 100k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25741
  - Câblage : 1→`M1_GATE` · 2→`GND`
- **R27** — 100k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25741
  - Câblage : 1→`M2_GATE` · 2→`GND`
- **R28** — 100k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25741
  - Câblage : 1→`M3_GATE` · 2→`GND`
- **R29** — 100k · `Resistor_SMD:R_0402_1005Metric` · LCSC C25741
  - Câblage : 1→`M4_GATE` · 2→`GND`
- **D3** — SS34 · `Diode_SMD:D_SMA` · LCSC C8678
  - Câblage : 1→`VBAT` · 2→`M1_D`
- **D4** — SS34 · `Diode_SMD:D_SMA` · LCSC C8678
  - Câblage : 1→`VBAT` · 2→`M2_D`
- **D5** — SS34 · `Diode_SMD:D_SMA` · LCSC C8678
  - Câblage : 1→`VBAT` · 2→`M3_D`
- **D6** — SS34 · `Diode_SMD:D_SMA` · LCSC C8678
  - Câblage : 1→`VBAT` · 2→`M4_D`
- **J5** — MOTOR1 · `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`
  - Câblage : 1→`VBAT` · 2→`M1_D`
- **J6** — MOTOR2 · `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`
  - Câblage : 1→`VBAT` · 2→`M2_D`
- **J7** — MOTOR3 · `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`
  - Câblage : 1→`VBAT` · 2→`M3_D`
- **J8** — MOTOR4 · `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`
  - Câblage : 1→`VBAT` · 2→`M4_D`

### LEDs d'état WS2812B

- **LED1** — WS2812B-2020 · `LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm` · LCSC C965555
  - Câblage : 1→`VBAT` · 2→`LED_DIN` · 3→`GND` · 4→`LED_D12`
- **LED2** — WS2812B-2020 · `LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm` · LCSC C965555
  - Câblage : 1→`VBAT` · 2→`LED_D12` · 3→`GND` · 4→`LED_DOUT`
- **C34** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`VBAT` · 2→`GND`
- **C35** — 100nF · `Capacitor_SMD:C_0402_1005Metric` · LCSC C1525
  - Câblage : 1→`VBAT` · 2→`GND`

### Extension + debug

- **J9** — EXP · `Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical`
  - Câblage : 1→`3V3` · 2→`GND` · 3→`VBAT` · 4→`I2C_SDA` · 5→`I2C_SCL` · 6→`EXP_IO`
- **J10** — DBG · `Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical`
  - Câblage : 1→`GND` · 2→`U0TXD` · 3→`U0RXD` · 4→`3V3`
- **J11** — C6DBG · `Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical`
  - Câblage : 1→`GND` · 2→`C6_U0TXD` · 3→`C6_U0RXD` · 4→`C6_BOOT`
