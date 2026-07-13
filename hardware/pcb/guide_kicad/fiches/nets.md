<!-- Fiche générée par fiches/gen_reference.py depuis scripts/design.py — NE PAS éditer à la main. -->

# Fiche — Netlist (noms de nets à respecter)

84 nets distincts. **Utilise ces noms exacts en labels globaux** dans le schéma : c'est ce qui garantit que ton netlist correspond à celui de la carte du repo.

> ⚠️ Nets à une seule broche (à vérifier / points de test, normal ici) : `CAM_GPIO`, `CHRG_N`, `GPIO0`, `LED_DOUT`, `STDBY_N`, `TOF_INT`

| Net | Broches (ref.pad) |
|-----|-------------------|
| `3V3` | C12.1, C13.1, C14.1, C15.1, C16.1, C17.1, C18.1, C19.1, C20.1, C21.1, C22.1, C23.1, C24.1, C25.1, C26.1, C27.1, C28.1, C29.1, C30.1, C31.1, C32.1, C33.1, C36.1, C4.1, J10.4, J3.1, J3.8, J4.15, J9.1, L1.2, R10.1, R16.1, R17.1, R18.1, R19.1, R20.1, R21.1, R32.1, R4.1, R9.1, U1.9, U1.21, U1.62, U1.85, U1.96, U1.75, U1.77, U1.101, U1.102, U1.51, U10.4, U3.3, U6.5, U6.8, U7.5, U7.6, U7.8, U8.1, U8.11, U9.1, U9.8 |
| `3V3_EN` | R6.1, U5.1 |
| `BOOT` | R10.2, SW2.1, U1.66 |
| `C6_BOOT` | J11.4, R21.2, U3.23 |
| `C6_EN` | U1.98, U3.8 |
| `C6_U0RXD` | J11.3, U3.30 |
| `C6_U0TXD` | J11.2, U3.31 |
| `CAM_GPIO` | J4.12 |
| `CAM_PWDN` | J4.11, U1.53 |
| `CC1` | J2.A5, R1.1 |
| `CC2` | J2.B5, R2.1 |
| `CHIP_PU` | C10.1, R9.2, SW1.1, U1.103 |
| `CHRG_N` | U4.7 |
| `CSI_CKN` | J4.8, U1.45 |
| `CSI_CKP` | J4.9, U1.44 |
| `CSI_D0N` | J4.2, U1.42 |
| `CSI_D0P` | J4.3, U1.43 |
| `CSI_D1N` | J4.5, U1.46 |
| `CSI_D1P` | J4.6, U1.47 |
| `CSI_REXT` | R11.1, U1.48 |
| `CS_FLOW` | J3.2, U1.14, U9.6 |
| `CS_IMU` | U1.13, U6.12 |
| `DSI_REXT` | R12.1, U1.34 |
| `EN_DCDC` | U1.79, U10.1 |
| `EXP_IO` | J9.6, U1.24 |
| `FB3V3` | R4.2, R5.1, U5.5 |
| `FB_DCDC` | C37.2, R30.2, R31.1, U1.78, U10.5 |
| `FLASH_CK` | U1.32, U2.6 |
| `FLASH_CS` | R13.2, U1.27, U2.1 |
| `FLASH_IO0` | U1.33, U2.5 |
| `FLASH_IO1` | U1.28, U2.2 |
| `FLASH_IO2` | R14.2, U1.29, U2.3 |
| `FLASH_IO3` | R15.2, U1.31, U2.7 |
| `GND` | C1.2, C10.2, C11.2, C12.2, C13.2, C14.2, C15.2, C16.2, C17.2, C18.2, C19.2, C2.2, C20.2, C21.2, C22.2, C23.2, C24.2, C25.2, C26.2, C27.2, C28.2, C29.2, C3.2, C30.2, C31.2, C32.2, C33.2, C34.2, C35.2, C36.2, C38.2, C39.2, C4.2, C40.2, C41.2, C42.2, C5.2, C6.2, C7.2, C8.2, C9.2, D1.2, J1.2, J10.1, J11.1, J2.A1, J2.A12, J2.B1, J2.B12, J2.S1, J3.3, J3.7, J4.1, J4.4, J4.7, J4.10, J9.2, LED1.3, LED2.3, Q1.2, Q2.2, Q3.2, Q4.2, R1.2, R11.2, R12.2, R2.2, R26.2, R27.2, R28.2, R29.2, R3.2, R31.2, R5.2, R8.2, SW1.2, SW2.2, U1.105, U10.2, U2.4, U3.1, U3.2, U3.11, U3.14, U3.36, U3.37, U3.38, U3.39, U3.40, U3.41, U3.42, U3.43, U3.44, U3.45, U3.46, U3.47, U3.48, U3.49, U3.50, U3.51, U3.52, U3.53, U4.1, U4.3, U4.9, U5.2, U6.2, U6.3, U6.6, U6.7, U6.9, U6.10, U6.11, U6.15, U7.1, U7.2, U7.7, U8.2, U8.3, U8.4, U8.6, U8.12, U9.2, U9.7, Y1.2, Y1.4 |
| `GPIO0` | U1.104 |
| `GPIO36_STRAP` | R32.2, U1.68 |
| `I2C_SCL` | J4.13, J9.5, U1.8, U7.4, U8.10 |
| `I2C_SDA` | J4.14, J9.4, U1.7, U7.3, U8.9 |
| `IMU_INT` | U1.23, U6.4 |
| `LED_D12` | LED1.4, LED2.2 |
| `LED_DIN` | LED1.2, U1.52 |
| `LED_DOUT` | LED2.4 |
| `M1_D` | D3.2, J5.2, Q1.1 |
| `M1_G` | R22.1, U1.87 |
| `M1_GATE` | Q1.3, R22.2, R26.1 |
| `M2_D` | D4.2, J6.2, Q2.1 |
| `M2_G` | R23.1, U1.88 |
| `M2_GATE` | Q2.3, R23.2, R27.1 |
| `M3_D` | D5.2, J7.2, Q3.1 |
| `M3_G` | R24.1, U1.89 |
| `M3_GATE` | Q3.3, R24.2, R28.1 |
| `M4_D` | D6.2, J8.2, Q4.1 |
| `M4_G` | R25.1, U1.90 |
| `M4_GATE` | Q4.3, R25.2, R29.1 |
| `PROG` | R3.1, U4.2 |
| `SDIO_CLK` | U1.19, U3.25 |
| `SDIO_CMD` | R16.2, U1.20, U3.24 |
| `SDIO_D0` | R17.2, U1.15, U3.26 |
| `SDIO_D1` | R18.2, U1.16, U3.27 |
| `SDIO_D2` | R19.2, U1.17, U3.28 |
| `SDIO_D3` | R20.2, U1.18, U3.29 |
| `SPI_MISO` | J3.6, U1.12, U6.1, U9.5 |
| `SPI_MOSI` | J3.5, U1.11, U6.14, U9.4 |
| `SPI_SCLK` | J3.4, U1.10, U6.13, U9.3 |
| `STDBY_N` | U4.6 |
| `SW3V3` | L1.1, U5.3 |
| `SW_CORE` | L2.1, U10.3 |
| `TOF_INT` | U8.7 |
| `U0RXD` | J10.3, U1.70 |
| `U0TXD` | J10.2, U1.69 |
| `USB_DM_C` | D1.3, J2.A7, J2.B7 |
| `USB_DM_MCU` | D1.4, U1.49 |
| `USB_DP_C` | D1.1, J2.A6, J2.B6 |
| `USB_DP_MCU` | D1.6, U1.50 |
| `VBAT` | C2.1, C3.1, C34.1, C35.1, D2.1, D3.1, D4.1, D5.1, D6.1, J1.1, J5.1, J6.1, J7.1, J8.1, J9.3, LED1.1, LED2.1, R6.2, R7.1, U4.5, U5.4 |
| `VBAT_SENSE` | C6.1, R7.2, R8.1, U1.22 |
| `VBUS` | C1.1, D1.5, D2.2, J2.A4, J2.A9, J2.B4, J2.B9, U4.4, U4.8 |
| `VDD_CORE` | C11.1, C37.1, C5.1, L2.2, R30.1, U1.26, U1.76, U1.91 |
| `VDD_FLASHIO` | C38.1, C39.1, R13.1, R14.1, R15.1, U1.71, U1.30, U2.8 |
| `VDD_MIPI` | C42.1, C7.1, U1.73, U1.41 |
| `VDD_PSRAM` | C40.1, C41.1, U1.72, U1.59, U1.67 |
| `VL53_XSHUT` | U1.25, U8.5 |
| `XTAL_N` | C9.1, U1.99, Y1.3 |
| `XTAL_P` | C8.1, U1.100, Y1.1 |
