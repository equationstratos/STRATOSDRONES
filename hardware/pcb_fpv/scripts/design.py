#!/usr/bin/env python3
"""STRATOS FPV AIO — authoritative design database (single source of truth).

The SHARED brushless 2S AIO board for the two outdoor-FPV models (fpv85 =
Fr4n8-001, fpv2 = Fr4n9-001): one board, whoop-standard 25.5x25.5 M2 mounting,
two printed frames. Same pipeline as hardware/pcb: edit THIS file, then
`make` (needs KiCad pcbnew + kicad-cli — the CI job runs it in the
kicad/kicad:8.0 container; this file itself is pure Python).

What changed vs the Fr4n7 board (hardware/pcb/scripts/design.py):
  * 2S input (XT30 pigtail pads) — TP4056 1S charger REMOVED (charge the pack
    on a USB-C 2S balance charger, off-board).
  * SY8089 (Vin max 5.5V) replaced by wide-Vin bucks: AP63203 -> 3V3 and
    AP63205 -> 5V (VTX + camera + ELRS RX + LEDs).
  * The 4x brushed low-side FETs are replaced by 4x INTEGRATED BRUSHLESS ESC
    stages (EFM8BB21 + FD6288T 3-phase driver + 6x AO3400 N-FET per motor) —
    the open BLHeli_S/Bluejay architecture used by real whoop AIOs. The MCU
    signals stay on GPIO45-48 (DShot = same pins, different protocol).
  * ExpressLRS radio: J12 CRSF socket (5V/GND/TX/RX) for an off-the-shelf
    ELRS receiver. Analog FPV: J13 VTX bay pads (5V/GND/VIDEO/SmartAudio) +
    J14 nano-camera pads (5V/GND/VIDEO) — the cam->VTX path is pure hardware.
  * Indoor sensors removed (VL53L1X ToF, PMW3901 flow): outdoors they are
    dead weight; position hold degrades to IMU+baro (documented honestly).
    The P4 MIPI camera FFC stays as an OPTIONAL populate (Wi-Fi H.264 bonus).

Honesty: every part carried over from the Fr4n7 board keeps its verified pin
map. Every NEW part (bucks, EFM8, FD6288T, JST-SH sockets) is tagged VERIFY —
pin tables written from architecture knowledge, NOT datasheets-in-hand.
KNOWN_GAPS.md lists them as FAB-BLOCKING. Do not order before that pass.
"""

# --------------------------------------------------------------------------
# ESP32-P4 signal -> QFN pad map (identical to hardware/pcb — verified there)
# --------------------------------------------------------------------------
def _p4_map():
    m = {}
    for g in range(1, 9):
        m[f"GPIO{g}"] = g
    m["VDD_LP"] = 9
    for g in range(9, 20):
        m[f"GPIO{g}"] = g + 1
    m["VDD_IO_0"] = 21
    m["GPIO20"] = 22
    m["GPIO21"] = 23
    m["GPIO22"] = 24
    m["GPIO23"] = 25
    m["VDD_HP_0"] = 26
    m["FLASH_CS"] = 27
    m["FLASH_Q"] = 28
    m["FLASH_WP"] = 29
    m["VDD_FLASH_IO"] = 30
    m["FLASH_HOLD"] = 31
    m["FLASH_CK"] = 32
    m["FLASH_D"] = 33
    m["DSI_REXT"] = 34
    m["DSI_DATAP1"] = 35
    m["DSI_DATAN1"] = 36
    m["DSI_CLKN"] = 37
    m["DSI_CLKP"] = 38
    m["DSI_DATAP0"] = 39
    m["DSI_DATAN0"] = 40
    m["VDD_MIPI_DPHY"] = 41
    m["CSI_DATAN0"] = 42
    m["CSI_DATAP0"] = 43
    m["CSI_CLKP"] = 44
    m["CSI_CLKN"] = 45
    m["CSI_DATAN1"] = 46
    m["CSI_DATAP1"] = 47
    m["CSI_REXT"] = 48
    m["USB_DM"] = 49
    m["USB_DP"] = 50
    m["VDD_USBPHY"] = 51
    m["GPIO24"] = 52
    m["GPIO25"] = 53
    m["NC54"] = 54
    m["GPIO26"] = 55
    m["GPIO27"] = 56
    m["GPIO28"] = 57
    m["GPIO29"] = 58
    m["VDD_PSRAM_0"] = 59
    m["GPIO30"] = 60
    m["GPIO31"] = 61
    m["VDD_IO_4"] = 62
    m["GPIO32"] = 63
    m["GPIO33"] = 64
    m["GPIO34"] = 65
    m["GPIO35"] = 66
    m["VDD_PSRAM_1"] = 67
    m["GPIO36"] = 68
    m["GPIO37"] = 69
    m["GPIO38"] = 70
    m["VDDO_FLASH"] = 71
    m["VDDO_PSRAM"] = 72
    m["VDDO_3"] = 73
    m["VDDO_4"] = 74
    m["VDD_LDO"] = 75
    m["VDD_HP_2"] = 76
    m["VDD_DCDCC"] = 77
    m["FB_DCDC"] = 78
    m["EN_DCDC"] = 79
    m["GPIO39"] = 80
    m["GPIO40"] = 81
    m["GPIO41"] = 82
    m["GPIO42"] = 83
    m["GPIO43"] = 84
    m["VDD_IO_5"] = 85
    m["GPIO44"] = 86
    m["GPIO45"] = 87
    m["GPIO46"] = 88
    m["GPIO47"] = 89
    m["GPIO48"] = 90
    m["VDD_HP_3"] = 91
    m["GPIO49"] = 92
    m["GPIO50"] = 93
    m["GPIO51"] = 94
    m["GPIO52"] = 95
    m["VDD_IO_6"] = 96
    m["GPIO53"] = 97
    m["GPIO54"] = 98
    m["XTAL_N"] = 99
    m["XTAL_P"] = 100
    m["VDD_ANA"] = 101
    m["VDD_BAT"] = 102
    m["CHIP_PU"] = 103
    m["GPIO0"] = 104
    m["GND"] = 105
    return m

P4 = _p4_map()

# --------------------------------------------------------------------------
# Firmware GPIO assignment (mirrored into out/board_pinmap_fpv.h).
# Carried over from Fr4n7 wherever the function survives; NEW: CRSF + VTX.
# --------------------------------------------------------------------------
PINMAP = {
    # SPI (ICM-42688-P IMU only — the PMW3901 flow sensor is gone)
    "SPI_SCLK": "GPIO9", "SPI_MOSI": "GPIO10", "SPI_MISO": "GPIO11",
    "CS_IMU": "GPIO12", "IMU_INT": "GPIO21",
    # I2C (SPL06 0x76 + camera SCCB)
    "I2C_SDA": "GPIO7", "I2C_SCL": "GPIO8",
    # SDIO to ESP32-C6 (esp-hosted) — identical to Fr4n7
    "SDIO_CLK": "GPIO18", "SDIO_CMD": "GPIO19",
    "SDIO_D0": "GPIO14", "SDIO_D1": "GPIO15", "SDIO_D2": "GPIO16", "SDIO_D3": "GPIO17",
    "C6_EN": "GPIO54",
    # motors M1..M4 — SAME pins as Fr4n7; brushed PWM becomes DShot (spec'd)
    "MOTOR_1": "GPIO45", "MOTOR_2": "GPIO46", "MOTOR_3": "GPIO47", "MOTOR_4": "GPIO48",
    # NEW — ExpressLRS CRSF UART + VTX SmartAudio (free GPIOs on Fr4n7)
    "CRSF_TX": "GPIO4", "CRSF_RX": "GPIO5", "VTX_SA": "GPIO6",
    # misc
    "VBAT_ADC": "GPIO20", "WS2812": "GPIO24", "CAM_PWDN": "GPIO25",
    # UART0 console + BOOT strap (VERIFY inherited from Fr4n7 gaps ledger)
    "UART0_TX": "GPIO37", "UART0_RX": "GPIO38", "BOOT_STRAP": "GPIO35",
}

# --------------------------------------------------------------------------
C = []


def part(ref, value, fp, pins, lcsc="", side="T", populate=True, fp_alt=None,
         rot=0, comment=None):
    C.append(dict(ref=ref, value=value, fp=fp, fp_alt=fp_alt or [], pins=pins,
                  lcsc=lcsc, side=side, populate=populate, rot=rot,
                  comment=comment or value))


def p4(sig):
    return str(P4[sig])


# ---- ESP32-P4 main MCU (supply topology verified on the Fr4n7 board) ----
_p4_pins = {}
for s in ["VDD_LP", "VDD_IO_0", "VDD_IO_4",
          "VDD_IO_5", "VDD_IO_6",
          "VDD_LDO", "VDD_DCDCC", "VDD_ANA", "VDD_BAT", "VDD_USBPHY"]:
    _p4_pins[p4(s)] = "3V3"
_p4_pins[p4("GND")] = "GND"
_p4_pins[p4("VDDO_FLASH")] = "VDD_FLASHIO"
_p4_pins[p4("VDD_FLASH_IO")] = "VDD_FLASHIO"
_p4_pins[p4("VDDO_PSRAM")] = "VDD_PSRAM"
_p4_pins[p4("VDD_PSRAM_0")] = "VDD_PSRAM"
_p4_pins[p4("VDD_PSRAM_1")] = "VDD_PSRAM"
_p4_pins[p4("VDDO_3")] = "VDD_MIPI"
for s in ["VDD_HP_0", "VDD_HP_2", "VDD_HP_3"]:
    _p4_pins[p4(s)] = "VDD_CORE"
_p4_pins[p4("EN_DCDC")] = "EN_DCDC"
_p4_pins[p4("FB_DCDC")] = "FB_DCDC"
_p4_pins[p4("VDD_MIPI_DPHY")] = "VDD_MIPI"
_p4_pins[p4("FLASH_CS")] = "FLASH_CS"
_p4_pins[p4("FLASH_CK")] = "FLASH_CK"
_p4_pins[p4("FLASH_D")] = "FLASH_IO0"
_p4_pins[p4("FLASH_Q")] = "FLASH_IO1"
_p4_pins[p4("FLASH_WP")] = "FLASH_IO2"
_p4_pins[p4("FLASH_HOLD")] = "FLASH_IO3"
_p4_pins[p4("XTAL_P")] = "XTAL_P"
_p4_pins[p4("XTAL_N")] = "XTAL_N"
_p4_pins[p4("CHIP_PU")] = "CHIP_PU"
_p4_pins[p4("GPIO0")] = "GPIO0"
_p4_pins[p4("CSI_REXT")] = "CSI_REXT"
_p4_pins[p4("DSI_REXT")] = "DSI_REXT"
_p4_pins[p4("USB_DM")] = "USB_DM_MCU"
_p4_pins[p4("USB_DP")] = "USB_DP_MCU"
_p4_pins[p4("CSI_CLKP")] = "CSI_CKP"
_p4_pins[p4("CSI_CLKN")] = "CSI_CKN"
_p4_pins[p4("CSI_DATAP0")] = "CSI_D0P"
_p4_pins[p4("CSI_DATAN0")] = "CSI_D0N"
_p4_pins[p4("CSI_DATAP1")] = "CSI_D1P"
_p4_pins[p4("CSI_DATAN1")] = "CSI_D1N"
_role = {
    "SPI_SCLK": "SPI_SCLK", "SPI_MOSI": "SPI_MOSI", "SPI_MISO": "SPI_MISO",
    "CS_IMU": "CS_IMU", "IMU_INT": "IMU_INT",
    "I2C_SDA": "I2C_SDA", "I2C_SCL": "I2C_SCL",
    "SDIO_CLK": "SDIO_CLK", "SDIO_CMD": "SDIO_CMD", "SDIO_D0": "SDIO_D0",
    "SDIO_D1": "SDIO_D1", "SDIO_D2": "SDIO_D2", "SDIO_D3": "SDIO_D3",
    "C6_EN": "C6_EN", "MOTOR_1": "M1_G", "MOTOR_2": "M2_G", "MOTOR_3": "M3_G",
    "MOTOR_4": "M4_G", "VBAT_ADC": "VBAT_SENSE", "WS2812": "LED_DIN",
    "CAM_PWDN": "CAM_PWDN",
    "CRSF_TX": "CRSF_TX", "CRSF_RX": "CRSF_RX", "VTX_SA": "VTX_SA",
    "UART0_TX": "U0TXD", "UART0_RX": "U0RXD", "BOOT_STRAP": "BOOT",
}
for role, sig in PINMAP.items():
    _p4_pins[p4(sig)] = _role[role]

part("U1", "ESP32-P4NRW32", "strat:ESP32-P4", _p4_pins, lcsc="C22387510",
     comment="ESP32-P4 dual RISC-V, 32MB in-pkg PSRAM, H.264 HW enc")

# ---- 16MB QSPI NOR flash (verified block, carried over) -----------------
part("U2", "W25Q128JVSIQ", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "FLASH_CS", "2": "FLASH_IO1", "3": "FLASH_IO2", "4": "GND",
      "5": "FLASH_IO0", "6": "FLASH_CK", "7": "FLASH_IO3", "8": "VDD_FLASHIO"},
     lcsc="C97521", comment="16MB QSPI NOR flash (VDDO_FLASH rail)")

# ---- ESP32-C6-MINI-1 Wi-Fi co-processor (verified block) ----------------
_c6 = {"3": "3V3", "8": "C6_EN",
       "25": "SDIO_CLK", "24": "SDIO_CMD",
       "26": "SDIO_D0", "27": "SDIO_D1", "28": "SDIO_D2", "29": "SDIO_D3",
       "23": "C6_BOOT",
       "30": "C6_U0RXD", "31": "C6_U0TXD"}
for pad in [1, 2, 11, 14, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
            48, 49, 50, 51, 52, 53]:
    _c6[str(pad)] = "GND"
part("U3", "ESP32-C6-MINI-1", "strat:ESP32-C6-MINI-1", _c6, lcsc="C3013606",
     comment="Wi-Fi 6 co-processor (esp-hosted SDIO) — SDK/programming link")

# ==========================================================================
# POWER — 2S direct (no on-board charger; charge the pack off-board)
# ==========================================================================
part("J1", "BATT_2S_XT30", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     {"1": "VBAT", "2": "GND"}, lcsc="",
     comment="2S pack pads (solder the XT30 pigtail; pin1=+, 6.0-8.4V)")

part("J2", "USB-C-16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A4": "VBUS", "A5": "CC1", "A6": "USB_DP_C", "A7": "USB_DM_C",
      "A9": "VBUS", "A12": "GND",
      "B1": "GND", "B4": "VBUS", "B5": "CC2", "B6": "USB_DP_C", "B7": "USB_DM_C",
      "B9": "VBUS", "B12": "GND",
      "S1": "GND"},
     lcsc="C165948", fp_alt=["Connector_USB:USB_C_Receptacle_GCT_USB4085"],
     comment="USB-C = flashing/dev only (VBUS unused: no 1S charger on 2S board)")
part("R1", "5.1k", "Resistor_SMD:R_0402_1005Metric", {"1": "CC1", "2": "GND"}, lcsc="C25905")
part("R2", "5.1k", "Resistor_SMD:R_0402_1005Metric", {"1": "CC2", "2": "GND"}, lcsc="C25905")
part("D1", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DP_C", "2": "GND", "3": "USB_DM_C", "4": "USB_DM_MCU",
      "5": "VBUS", "6": "USB_DP_MCU"}, lcsc="C7519", comment="USB ESD")
part("C1", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "VBUS", "2": "GND"}, lcsc="C15850")

# AP63203 wide-Vin buck: VBAT(2S) -> 3V3 / 2A.
# VERIFY (fab-blocking): TSOT-26 pin map written from the AP6320x family
# application topology (GND/SW/VIN/FB/EN/BST), NOT datasheet-in-hand; the
# SY8089 of the Fr4n7 board is Vin<=5.5V and CANNOT be reused on 2S.
part("U5", "AP63203WU-7", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "GND", "2": "SW3V3", "3": "VBAT", "4": "3V3", "5": "EN3V3", "6": "BST3V3"},
     lcsc="", comment="VERIFY AP63203 TSOT-26 pin map + LCSC part before fab")
part("C2", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "SW3V3", "2": "BST3V3"},
     lcsc="C1525", comment="bootstrap")
part("L1", "10uH", "Inductor_SMD:L_0805_2012Metric", {"1": "SW3V3", "2": "3V3"},
     lcsc="C408412", comment="buck inductor (verified LCSC part, 2.8A sat)")
part("R6", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "EN3V3", "2": "VBAT"},
     lcsc="C25741", comment="enable pull-up (always on)")
part("C3", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "VBAT", "2": "GND"}, lcsc="C15850")
part("C4", "22uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "3V3", "2": "GND"}, lcsc="C45783")

# AP63205 wide-Vin buck: VBAT(2S) -> 5V / 2A (VTX + analog cam + ELRS RX + LEDs).
part("U11", "AP63205WU-7", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "GND", "2": "SW5V", "3": "VBAT", "4": "5V", "5": "EN5V", "6": "BST5V"},
     lcsc="", comment="VERIFY AP63205 TSOT-26 pin map + LCSC part before fab")
part("C43", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "SW5V", "2": "BST5V"},
     lcsc="C1525", comment="bootstrap")
part("L3", "10uH", "Inductor_SMD:L_0805_2012Metric", {"1": "SW5V", "2": "5V"},
     lcsc="C408412")
part("R32", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "EN5V", "2": "VBAT"},
     lcsc="C25741", comment="enable pull-up (always on)")
part("C44", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "VBAT", "2": "GND"}, lcsc="C15850")
part("C45", "22uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "5V", "2": "GND"}, lcsc="C45783")

# ---- ESP32-P4 CPU core DC-DC (~1.2V) — Espressif-verified block, verbatim --
part("U10", "TLV62569DBVR", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "EN_DCDC", "2": "GND", "3": "SW_CORE", "4": "3V3", "5": "FB_DCDC"},
     lcsc="C141836", comment="ESP32-P4 core DC-DC (Espressif-verified TLV62569 ref design)")
part("L2", "2.2uH", "Inductor_SMD:L_Cenker_CKCS3015", {"1": "SW_CORE", "2": "VDD_CORE"},
     lcsc="C43389", comment="core DC-DC inductor 2.2uH/2A 3x3mm")
part("C5", "22uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "VDD_CORE", "2": "GND"},
     lcsc="C45783")
part("C36", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "3V3", "2": "GND"},
     lcsc="C15850")
part("C37", "20pF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_CORE", "2": "FB_DCDC"},
     lcsc="C1554")
part("R30", "453k", "Resistor_SMD:R_0402_1005Metric", {"1": "VDD_CORE", "2": "FB_DCDC"},
     lcsc="C123734")
part("R31", "453k", "Resistor_SMD:R_0402_1005Metric", {"1": "FB_DCDC", "2": "GND"},
     lcsc="C123734")

# VBAT divider -> ADC. 2S max 8.4V -> /3 with verified 100k parts
# (two 100k in series on top, 100k bottom): 8.4V -> 2.8V at the pin.
part("R7", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT", "2": "VBAT_DIV"}, lcsc="C25741")
part("R33", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT_DIV", "2": "VBAT_SENSE"}, lcsc="C25741")
part("R8", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT_SENSE", "2": "GND"}, lcsc="C25741")
part("C6", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VBAT_SENSE", "2": "GND"}, lcsc="C1525")

# Internal-LDO rail decoupling (verified block, carried over)
part("C7", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_MIPI", "2": "GND"}, lcsc="C52923")
part("C42", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_MIPI", "2": "GND"}, lcsc="C1525")
part("C38", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "GND"}, lcsc="C52923")
part("C39", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "GND"}, lcsc="C1525")
part("C40", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_PSRAM", "2": "GND"}, lcsc="C52923")
part("C41", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_PSRAM", "2": "GND"}, lcsc="C1525")

# ==========================================================================
# P4 SUPPORT: crystal, reset, boot, REXT, decoupling (verified, carried over)
# ==========================================================================
part("Y1", "40MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
     {"1": "XTAL_P", "2": "GND", "3": "XTAL_N", "4": "GND"}, lcsc="C9002",
     comment="VERIFY load caps for chosen xtal (inherited)")
part("C8", "10pF", "Capacitor_SMD:C_0402_1005Metric", {"1": "XTAL_P", "2": "GND"}, lcsc="C1555")
part("C9", "10pF", "Capacitor_SMD:C_0402_1005Metric", {"1": "XTAL_N", "2": "GND"}, lcsc="C1555")
part("R9", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": "CHIP_PU"}, lcsc="C25744")
part("C10", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "CHIP_PU", "2": "GND"}, lcsc="C52923")
part("SW1", "RESET", "Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
     {"1": "CHIP_PU", "2": "GND"}, lcsc="C720477")
part("SW2", "BOOT", "Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
     {"1": "BOOT", "2": "GND"}, lcsc="C720477", comment="VERIFY P4 boot strap = GPIO35 (inherited)")
part("R10", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": "BOOT"}, lcsc="C25744")
part("R11", "4.02k", "Resistor_SMD:R_0402_1005Metric", {"1": "CSI_REXT", "2": "GND"}, lcsc="C25752",
     comment="CSI termination per esp32p4 checklist")
part("R12", "4.02k", "Resistor_SMD:R_0402_1005Metric", {"1": "DSI_REXT", "2": "GND"}, lcsc="C25752",
     comment="DSI termination (DSI unused)")
part("R13", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "FLASH_CS"}, lcsc="C25744")
part("R14", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "FLASH_IO2"}, lcsc="C25744")
part("R15", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "FLASH_IO3"}, lcsc="C25744")
for i, net in enumerate(["SDIO_CMD", "SDIO_D0", "SDIO_D1", "SDIO_D2", "SDIO_D3"]):
    part(f"R{16+i}", "51k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": net},
         lcsc="C25905", comment="SDIO pull-up")
part("R21", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": "C6_BOOT"}, lcsc="C25744")
part("C11", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_CORE", "2": "GND"}, lcsc="C1525")

_dc = 12
for i in range(14):
    part(f"C{_dc+i}", "100nF", "Capacitor_SMD:C_0402_1005Metric",
         {"1": "3V3", "2": "GND"}, lcsc="C1525", comment="P4 rail decoupling")
part("C26", "10uF", "Capacitor_SMD:C_0603_1608Metric", {"1": "3V3", "2": "GND"}, lcsc="C19702")
part("C27", "10uF", "Capacitor_SMD:C_0603_1608Metric", {"1": "3V3", "2": "GND"}, lcsc="C19702")

# ==========================================================================
# SENSORS — IMU + barometer only (outdoor build; ToF/flow removed)
# ==========================================================================
part("U6", "ICM-42688-P", "Package_DFN_QFN:DHVQFN-14-1EP_2.5x3mm_P0.5mm_EP1x1.5mm",
     {"1": "SPI_MISO", "2": "GND", "3": "GND", "4": "IMU_INT",
      "5": "3V3", "6": "GND", "7": "GND", "8": "3V3",
      "9": "GND", "10": "GND", "11": "GND", "12": "CS_IMU",
      "13": "SPI_SCLK", "14": "SPI_MOSI", "15": "GND"},
     lcsc="C2840095", comment="IMU (verified pin map carried over)")
part("C28", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525")
part("C29", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525")

part("U7", "SPL06-001", "Package_LGA:Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering",
     {"1": "GND", "2": "GND", "3": "I2C_SDA", "4": "I2C_SCL",
      "5": "3V3", "6": "3V3", "7": "GND", "8": "3V3"},
     lcsc="C2684428", comment="barometer (verified pin map carried over)")
part("C30", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525")

# ==========================================================================
# CAMERA — P4 MIPI FFC, OPTIONAL populate (Wi-Fi H.264 bonus; FPV video is
# the ANALOG path below). CSI lane order/polarity gap inherited from Fr4n7.
# ==========================================================================
part("J4", "CAM_FFC15", "Connector_FFC-FPC:Hirose_FH12-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal",
     {"1": "GND", "2": "CSI_D0N", "3": "CSI_D0P", "4": "GND",
      "5": "CSI_D1N", "6": "CSI_D1P", "7": "GND", "8": "CSI_CKN",
      "9": "CSI_CKP", "10": "GND", "11": "CAM_PWDN", "12": "CAM_GPIO",
      "13": "I2C_SCL", "14": "I2C_SDA", "15": "3V3"},
     lcsc="C2884418", populate=False,
     comment="OPTIONAL MIPI camera (VERIFY RPi FFC pinout + CSI lanes — inherited)")
part("C33", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C52923")

# ==========================================================================
# MOTORS — 4x INTEGRATED BRUSHLESS ESC (EFM8BB21 + FD6288T + 6x AO3400)
# The open BLHeli_S / Bluejay architecture of real whoop AIOs, one channel
# per corner. MCU signal M{i}_G (GPIO45-48) -> EFM8 input; the EFM8 runs the
# commutation and drives the FD6288T 3-phase gate driver; 6 N-FETs form the
# bridge; phases A/B/C go to a 3-pin motor socket.
#
# VERIFY (fab-blocking): the EFM8BB21F16 (QFN20) and FD6288T (TSSOP20) pin
# NUMBERS below are architecture-level placeholders — verify BOTH against
# their datasheets (and Bluejay's reference layouts) before generating fab
# files. Net topology (what connects to what) is the standard one.
# FD6288T VCC from VBAT: datasheet minimum ~6V — fine at 2S nominal 7.4V,
# MARGINAL at the 6.0V cutoff (VERIFY; noted in KNOWN_GAPS).
# ==========================================================================
for i in range(1, 5):
    ph = {k: f"M{i}_{k}" for k in "ABC"}          # phase nets
    hi = {k: f"ESC{i}_HO{k}" for k in "ABC"}      # high-side gates
    lo = {k: f"ESC{i}_LO{k}" for k in "ABC"}      # low-side gates
    hin = {k: f"ESC{i}_H{k}" for k in "ABC"}      # EFM8 -> driver (high)
    lin = {k: f"ESC{i}_L{k}" for k in "ABC"}      # EFM8 -> driver (low)
    vb = {k: f"ESC{i}_VB{k}" for k in "ABC"}      # bootstrap rails

    # BLHeli_S MCU (flash Bluejay via the signal pad bootloader; first-time
    # programming via the C2 test pads TP)
    part(f"U{19+i}", "EFM8BB21F16G", "Package_DFN_QFN:QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm",
         {"2": "3V3", "3": "GND",
          "5": f"M{i}_G",                       # DShot signal in
          "6": hin["A"], "7": hin["B"], "8": hin["C"],
          "9": lin["A"], "10": lin["B"], "11": lin["C"],
          "13": f"ESC{i}_C2CK", "14": f"ESC{i}_C2D",
          "21": "GND"},
         lcsc="", comment=f"ESC{i} MCU — VERIFY QFN20 pad numbers vs EFM8BB21F16G datasheet")
    part(f"C{45+i}", "100nF", "Capacitor_SMD:C_0402_1005Metric",
         {"1": "3V3", "2": "GND"}, lcsc="C1525", comment=f"ESC{i} MCU decoupling")

    # 3-phase gate driver
    part(f"U{29+i}", "FD6288T", "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
         {"1": hin["A"], "2": hin["B"], "3": hin["C"],
          "4": lin["A"], "5": lin["B"], "6": lin["C"],
          "7": "GND", "8": "VBAT",
          "9": vb["A"], "10": hi["A"], "11": ph["A"],
          "12": vb["B"], "13": hi["B"], "14": ph["B"],
          "15": vb["C"], "16": hi["C"], "17": ph["C"],
          "18": lo["A"], "19": lo["B"], "20": lo["C"]},
         lcsc="", comment=f"ESC{i} 3-phase driver — VERIFY TSSOP20 pin map vs FD6288T datasheet; VCC min ~6V at 2S cutoff")
    part(f"C{49+i}", "100nF", "Capacitor_SMD:C_0402_1005Metric",
         {"1": "VBAT", "2": "GND"}, lcsc="C1525", comment=f"ESC{i} driver decoupling")
    for k in "ABC":   # bootstrap caps VB<->phase (C54..C65)
        part(f"C{54+(i-1)*3 + 'ABC'.index(k)}", "100nF", "Capacitor_SMD:C_0402_1005Metric",
             {"1": vb[k], "2": ph[k]}, lcsc="C1525", comment=f"ESC{i} bootstrap {k}")
    part(f"C{66+i}", "22uF", "Capacitor_SMD:C_0805_2012Metric",
         {"1": "VBAT", "2": "GND"}, lcsc="C45783", comment=f"ESC{i} bulk (bridge rail)")

    # bridge: 6x AO3400A N-FET (same verified part/lib as the Fr4n7 board;
    # pin convention follows that board: 1=D, 2=S, 3=G)
    for k in "ABC":
        qh = (i - 1) * 6 + "ABC".index(k) * 2 + 1
        part(f"Q{qh}", "AO3400A", "Package_TO_SOT_SMD:SOT-23",
             {"1": "VBAT", "2": ph[k], "3": hi[k]}, lcsc="C20917",
             comment=f"ESC{i} phase {k} high-side (D=VBAT S=phase G=HO)")
        part(f"Q{qh+1}", "AO3400A", "Package_TO_SOT_SMD:SOT-23",
             {"1": ph[k], "2": "GND", "3": lo[k]}, lcsc="C20917",
             comment=f"ESC{i} phase {k} low-side (D=phase S=GND G=LO)")

    # motor socket (JST-SH 3p like real micro motors; header fallback)
    part(f"J{4+i}", f"MOTOR{i}", "Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal",
         {"1": ph["A"], "2": ph["B"], "3": ph["C"]}, lcsc="",
         fp_alt=["Connector_PinHeader_1.27mm:PinHeader_1x03_P1.27mm_Vertical"],
         comment=f"motor {i} 3-phase socket")

    # C2 first-flash test pads
    part(f"TP{(i-1)*2+1}", f"E{i}C2CK", "TestPoint:TestPoint_Pad_D1.5mm",
         {"1": f"ESC{i}_C2CK"}, lcsc="", comment=f"ESC{i} C2 clock pad")
    part(f"TP{(i-1)*2+2}", f"E{i}C2D", "TestPoint:TestPoint_Pad_D1.5mm",
         {"1": f"ESC{i}_C2D"}, lcsc="", comment=f"ESC{i} C2 data pad")

# ==========================================================================
# RADIO — CRSF socket for an off-the-shelf ExpressLRS receiver
# ==========================================================================
part("J12", "CRSF_ELRS", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
     {"1": "5V", "2": "GND", "3": "CRSF_TX", "4": "CRSF_RX"}, lcsc="",
     fp_alt=["Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical"],
     comment="ELRS RX socket (5V, GND, P4-TX->RX, P4-RX<-TX) — CRSF 420kbaud")

# ==========================================================================
# ANALOG FPV — VTX bay pads + nano-camera pads (pure hardware path)
# ==========================================================================
part("J13", "VTX_BAY", "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical",
     {"1": "5V", "2": "GND", "3": "VIDEO", "4": "VTX_SA"}, lcsc="",
     comment="analog VTX module pads (5V / GND / video in / SmartAudio)")
part("J14", "CAM_ANALOG", "Connector_PinHeader_1.27mm:PinHeader_1x03_P1.27mm_Vertical",
     {"1": "5V", "2": "GND", "3": "VIDEO"}, lcsc="",
     comment="analog nano camera pads (5V / GND / video out)")

# ==========================================================================
# STATUS LEDs — moved to the 5V rail (WS2812B-2020 Vmax 5.5V << 2S VBAT!)
# ==========================================================================
part("LED1", "WS2812B-2020", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm",
     {"1": "5V", "2": "LED_DIN", "3": "GND", "4": "LED_D12"},
     lcsc="C965555", comment="status LED 1 (5V rail; 3.3V data VIH marginal — VERIFY)")
part("LED2", "WS2812B-2020", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm",
     {"1": "5V", "2": "LED_D12", "3": "GND", "4": "LED_DOUT"},
     lcsc="C965555", comment="status LED 2")
part("C34", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "5V", "2": "GND"}, lcsc="C1525")
part("C35", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "5V", "2": "GND"}, lcsc="C1525")

# ==========================================================================
# DEBUG pads (flashing + console — keep both, they are how you bring it up)
# ==========================================================================
part("J10", "DBG", "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical",
     {"1": "GND", "2": "U0TXD", "3": "U0RXD", "4": "3V3"},
     lcsc="", comment="P4 UART0 console pads")
part("J11", "C6DBG", "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical",
     {"1": "GND", "2": "C6_U0TXD", "3": "C6_U0RXD", "4": "C6_BOOT"},
     lcsc="", comment="C6 slave-flash pads")

POWER_NETS = ["VBAT", "VBUS", "3V3", "5V", "GND", "VDD_CORE", "VDD_MIPI"]

# Board outline (mm): whoop-standard square, 25.5 x 25.5 M2 mount pattern.
# 32x32 first try; if assert_placement proves the 4 ESC stages + P4 + C6
# cannot fit, grow to 35/36 square (mount pattern unchanged — both printed
# frames absorb it; decision logged in the model DESIGN.md).
BOARD = dict(w=32.0, h=32.0, corner_r=2.5,
             mount_pitch_x=25.5, mount_pitch_y=25.5, mount_d=2.2)


def all_components():
    return C


if __name__ == "__main__":
    nets = {}
    for c in C:
        for pad, net in c["pins"].items():
            nets.setdefault(net, []).append((c["ref"], pad))
    single = [n for n, v in nets.items() if len(v) == 1 and n not in ("GND",)]
    print(f"components: {len(C)}")
    print(f"distinct nets: {len(nets)}")
    print(f"unique-pin nets (likely test points or VERIFY): {len(single)}")
    for n in sorted(single):
        print("   single:", n, nets[n])
    bom = [c for c in C if c["populate"] and c["lcsc"]]
    print(f"BOM lines with LCSC: {len(bom)}")
    # FPV-specific sanity: every ESC channel fully netted, radio + video present
    for i in range(1, 5):
        for k in "ABC":
            assert len(nets.get(f"M{i}_{k}", [])) >= 3, f"phase M{i}_{k} incomplete"
        assert f"M{i}_G" in nets, f"missing ESC signal M{i}_G"
    for n in ["CRSF_TX", "CRSF_RX", "VTX_SA", "VIDEO", "5V"]:
        assert n in nets, f"missing net {n}"
    print("FPV sanity: 4 ESC channels netted, CRSF + VTX + 5V present  OK")
    dup = {}
    for c in C:
        assert c["ref"] not in dup, f"duplicate ref {c['ref']}"
        dup[c["ref"]] = 1
    print("refs unique  OK")
