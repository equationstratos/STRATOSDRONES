#!/usr/bin/env python3
"""STRATOSDRONE PCB — authoritative design database (single source of truth).

Everything downstream (schematic netlist, .kicad_pcb, JLCPCB BOM/CPL, the
firmware board_pinmap.h, the consistency check) is generated from the data
here. Edit THIS file, then re-run `make` in hardware/pcb/.

Conventions
-----------
* A Component has: ref, value, lcsc (JLCPCB part), footprint (KiCad lib:fp),
  pins {pad_number_or_name: net_name}, side ('T'/'B'), and an optional
  populate flag (False -> DNP, kept off the assembly BOM).
* Nets are implicit: any net name that appears on >=2 pins is a real net.
  PWR_FLAG-style power nets are declared in POWER_NETS for ERC sanity.
* The ESP32-P4 is referenced by SIGNAL name; P4_PAD[] maps signal -> QFN pad
  so generators emit the right pad numbers. This map was extracted from the
  official Espressif ESP32-P4 KiCad symbol (vendored in lib/).

Honesty: items the author could NOT fully verify are tagged VERIFY in
comments and collected in KNOWN_GAPS.md. Do not fabricate this board before
working through that list.
"""

# --------------------------------------------------------------------------
# ESP32-P4 signal -> QFN pad map (from vendored Espressif symbol, 104 pins+EP)
# --------------------------------------------------------------------------
def _p4_map():
    m = {}
    # low GPIOs
    for g in range(1, 9):            # GPIO1..8 -> pads 1..8
        m[f"GPIO{g}"] = g
    m["VDD_LP"] = 9
    for g in range(9, 20):           # GPIO9..19 -> pads 10..20
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
    m["GND"] = 105  # exposed pad
    return m

P4 = _p4_map()

# --------------------------------------------------------------------------
# Firmware GPIO assignment (mirrored into board_pinmap.h by gen_pinmap.py).
# Keep these names stable: the firmware #includes the generated header.
# --------------------------------------------------------------------------
PINMAP = {
    # SPI (ICM-42688-P + PMW3901)
    "SPI_SCLK": "GPIO9", "SPI_MOSI": "GPIO10", "SPI_MISO": "GPIO11",
    "CS_IMU": "GPIO12", "CS_FLOW": "GPIO13", "IMU_INT": "GPIO21",
    # I2C (SPL06 0x76, VL53L1X 0x29, camera SCCB)
    "I2C_SDA": "GPIO7", "I2C_SCL": "GPIO8", "VL53_XSHUT": "GPIO23",
    # SDIO to ESP32-C6 (esp-hosted)
    "SDIO_CLK": "GPIO18", "SDIO_CMD": "GPIO19",
    "SDIO_D0": "GPIO14", "SDIO_D1": "GPIO15", "SDIO_D2": "GPIO16", "SDIO_D3": "GPIO17",
    "C6_EN": "GPIO54",
    # motors M1..M4
    "MOTOR_1": "GPIO45", "MOTOR_2": "GPIO46", "MOTOR_3": "GPIO47", "MOTOR_4": "GPIO48",
    # misc
    "VBAT_ADC": "GPIO20", "WS2812": "GPIO24", "CAM_PWDN": "GPIO25",
    "EXP_IO": "GPIO22",
    # UART0 console (VERIFY P4 default console pins) + BOOT strap (VERIFY)
    "UART0_TX": "GPIO37", "UART0_RX": "GPIO38", "BOOT_STRAP": "GPIO35",
}

# --------------------------------------------------------------------------
# Components
# --------------------------------------------------------------------------
# Footprint candidate lists: gen_pcb picks the first that resolves in the
# installed libraries; the chosen one is reported. lib: prefix 'strat:' means
# our vendored hardware/pcb/lib, otherwise a KiCad system library.

C = []  # list of dicts


def part(ref, value, fp, pins, lcsc="", side="T", populate=True, fp_alt=None,
         rot=0, comment=None):
    C.append(dict(ref=ref, value=value, fp=fp, fp_alt=fp_alt or [], pins=pins,
                  lcsc=lcsc, side=side, populate=populate, rot=rot,
                  comment=comment or value))


def p4(sig):
    """ESP32-P4 pad number for a signal name."""
    return str(P4[sig])


# ---- ESP32-P4 main MCU -------------------------------------------------
_p4_pins = {}
# Supply-input rails -> 3V3 (3.0-3.6V).  VDD_LDO and VDD_DCDCC are ordinary
# supply inputs here (NOT switch nodes): per the ESP32-P4 HW Design Guidelines
# they take a 10uF cap on the trace + 0.1uF at each pin (provided by the shared
# 3V3 bulk/bypass array).  The CPU core rail VDD_HP_0/2/3 is deliberately NOT in
# this list -- it is generated by the external DC-DC U10 (see VDD_CORE below).
for s in ["VDD_LP", "VDD_IO_0", "VDD_IO_4",
          "VDD_IO_5", "VDD_IO_6",
          "VDD_LDO", "VDD_DCDCC", "VDD_ANA", "VDD_BAT", "VDD_USBPHY"]:
    _p4_pins[p4(s)] = "3V3"
_p4_pins[p4("GND")] = "GND"
# Internal-LDO OUTPUT rails -- the P4 generates these from VDD_LDO; they are
# OUTPUTS and must NOT be tied to 3V3 (the previous revision did, which both
# fought the internal LDOs and -- for PSRAM -- put 3.3V on a 1.95V-max pin).
# Per the ESP32-P4 schematic checklist (schematic-checklist-esp32p4.rst) and
# confirmed on the ESP32-P4-Function-EV-Board reference (which pairs the same
# ESP32-P4NRW32X with an external GD25Q128 flash + in-package PSRAM):
#   * VDDO_FLASH (default 3.3V) powers the flash IO bank VDD_FLASH_IO *and* the
#     external QSPI flash -- one shared rail (VDD_FLASHIO).  Comes up at reset
#     by default so the chip can boot from flash.
#   * VDDO_PSRAM (1.8V) powers the in-package PSRAM IO pins VDD_PSRAM_0/1.
#   * VDDO_3 is a configurable LDO (0.5-2.7V); firmware sets it to 2.5V to feed
#     VDD_MIPI_DPHY (MIPI D-PHY).  VDDO_4 is the other configurable LDO, unused
#     here -> left unconnected (disabled output floats safely).
_p4_pins[p4("VDDO_FLASH")] = "VDD_FLASHIO"
_p4_pins[p4("VDD_FLASH_IO")] = "VDD_FLASHIO"
_p4_pins[p4("VDDO_PSRAM")] = "VDD_PSRAM"
_p4_pins[p4("VDD_PSRAM_0")] = "VDD_PSRAM"
_p4_pins[p4("VDD_PSRAM_1")] = "VDD_PSRAM"
_p4_pins[p4("VDDO_3")] = "VDD_MIPI"   # configurable LDO -> 2.5V for MIPI D-PHY
# ESP32-P4 CPU core rail (~1.2V) -- powered by EXTERNAL DC-DC U10 (TLV62569),
# topology per the official ESP32-P4 HW Design Guidelines (esp32p4-ldo-dcdc.inc
# + TLV62569 rev3.0 reference schematic).  THE PREVIOUS REVISION WAS CHIP-FATAL:
#   * VDD_HP_0/2/3 were tied to 3V3 -> ~2.75x overvoltage on the core = dead chip.
#     They must tie to the DC-DC output VDD_CORE instead.
#   * EN_DCDC was hard-tied to 3V3; it must drive U10's enable (0V in download
#     mode / before firmware, then internally controlled by the P4).
#   * FB_DCDC was shorted onto VDD_CORE; it is the DC-DC feedback node (the
#     R30/R31 divider midpoint), a net distinct from the output rail.
for s in ["VDD_HP_0", "VDD_HP_2", "VDD_HP_3"]:
    _p4_pins[p4(s)] = "VDD_CORE"
_p4_pins[p4("EN_DCDC")] = "EN_DCDC"
_p4_pins[p4("FB_DCDC")] = "FB_DCDC"
_p4_pins[p4("VDD_MIPI_DPHY")] = "VDD_MIPI"   # 2.5V from internal LDO VDDO_3
# flash QSPI
_p4_pins[p4("FLASH_CS")] = "FLASH_CS"
_p4_pins[p4("FLASH_CK")] = "FLASH_CK"
_p4_pins[p4("FLASH_D")] = "FLASH_IO0"
_p4_pins[p4("FLASH_Q")] = "FLASH_IO1"
_p4_pins[p4("FLASH_WP")] = "FLASH_IO2"
_p4_pins[p4("FLASH_HOLD")] = "FLASH_IO3"
# crystal / reset / boot
_p4_pins[p4("XTAL_P")] = "XTAL_P"
_p4_pins[p4("XTAL_N")] = "XTAL_N"
_p4_pins[p4("CHIP_PU")] = "CHIP_PU"
_p4_pins[p4("GPIO0")] = "GPIO0"
# REXT precision resistors to GND (VERIFY value)
_p4_pins[p4("CSI_REXT")] = "CSI_REXT"
_p4_pins[p4("DSI_REXT")] = "DSI_REXT"
# USB
_p4_pins[p4("USB_DM")] = "USB_DM_MCU"
_p4_pins[p4("USB_DP")] = "USB_DP_MCU"
# CSI camera pairs (lane order/polarity VERIFY)
_p4_pins[p4("CSI_CLKP")] = "CSI_CKP"
_p4_pins[p4("CSI_CLKN")] = "CSI_CKN"
_p4_pins[p4("CSI_DATAP0")] = "CSI_D0P"
_p4_pins[p4("CSI_DATAN0")] = "CSI_D0N"
_p4_pins[p4("CSI_DATAP1")] = "CSI_D1P"
_p4_pins[p4("CSI_DATAN1")] = "CSI_D1N"
# functional GPIO nets (named by role)
_role = {
    "SPI_SCLK": "SPI_SCLK", "SPI_MOSI": "SPI_MOSI", "SPI_MISO": "SPI_MISO",
    "CS_IMU": "CS_IMU", "CS_FLOW": "CS_FLOW", "IMU_INT": "IMU_INT",
    "I2C_SDA": "I2C_SDA", "I2C_SCL": "I2C_SCL", "VL53_XSHUT": "VL53_XSHUT",
    "SDIO_CLK": "SDIO_CLK", "SDIO_CMD": "SDIO_CMD", "SDIO_D0": "SDIO_D0",
    "SDIO_D1": "SDIO_D1", "SDIO_D2": "SDIO_D2", "SDIO_D3": "SDIO_D3",
    "C6_EN": "C6_EN", "MOTOR_1": "M1_G", "MOTOR_2": "M2_G", "MOTOR_3": "M3_G",
    "MOTOR_4": "M4_G", "VBAT_ADC": "VBAT_SENSE", "WS2812": "LED_DIN",
    "CAM_PWDN": "CAM_PWDN", "EXP_IO": "EXP_IO",
    "UART0_TX": "U0TXD", "UART0_RX": "U0RXD", "BOOT_STRAP": "BOOT",
}
for role, sig in PINMAP.items():
    _p4_pins[p4(sig)] = _role[role]

part("U1", "ESP32-P4NRW32", "strat:ESP32-P4", _p4_pins, lcsc="C22387510",
     comment="ESP32-P4 dual RISC-V, 32MB in-pkg PSRAM, H.264 HW enc")

# ---- 16MB QSPI NOR flash ----------------------------------------------
part("U2", "W25Q128JVSIQ", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "FLASH_CS", "2": "FLASH_IO1", "3": "FLASH_IO2", "4": "GND",
      "5": "FLASH_IO0", "6": "FLASH_CK", "7": "FLASH_IO3", "8": "VDD_FLASHIO"},
     lcsc="C97521", comment="16MB QSPI NOR flash, VCC from VDDO_FLASH rail (boot flash for NRW32 = in-pkg PSRAM only)")

# ---- ESP32-C6-MINI-1 Wi-Fi co-processor (esp-hosted SDIO slave) --------
# C6 fixed SDIO-slave pins: CLK=GPIO19(pin25) CMD=GPIO18(pin24)
#   DAT0=GPIO20(26) DAT1=GPIO21(27) DAT2=GPIO22(28) DAT3=GPIO23(29)
_c6 = {"3": "3V3", "8": "C6_EN",
       "25": "SDIO_CLK", "24": "SDIO_CMD",
       "26": "SDIO_D0", "27": "SDIO_D1", "28": "SDIO_D2", "29": "SDIO_D3",
       "23": "C6_BOOT",          # GPIO9 strap (download)
       "30": "C6_U0RXD", "31": "C6_U0TXD"}
for pad in [1, 2, 11, 14, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
            48, 49, 50, 51, 52, 53]:
    _c6[str(pad)] = "GND"
part("U3", "ESP32-C6-MINI-1", "strat:ESP32-C6-MINI-1", _c6, lcsc="C3013606",
     comment="Wi-Fi 6 co-processor (esp-hosted SDIO)")

# ==========================================================================
# POWER
# ==========================================================================
part("J1", "BATT_PH2", "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
     {"1": "VBAT", "2": "GND"}, lcsc="C160404", comment="1S LiPo JST-PH2 (pin1=+)")

# USB-C 16-pin receptacle (power + USB2 only); CC pulldowns make it a sink.
part("J2", "USB-C-16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A4": "VBUS", "A5": "CC1", "A6": "USB_DP_C", "A7": "USB_DM_C",
      "A9": "VBUS", "A12": "GND",
      "B1": "GND", "B4": "VBUS", "B5": "CC2", "B6": "USB_DP_C", "B7": "USB_DM_C",
      "B9": "VBUS", "B12": "GND",
      "S1": "GND"},
     lcsc="C165948", fp_alt=["Connector_USB:USB_C_Receptacle_GCT_USB4085"],
     comment="USB-C charge + USB-Serial-JTAG")
part("R1", "5.1k", "Resistor_SMD:R_0402_1005Metric", {"1": "CC1", "2": "GND"}, lcsc="C25905")
part("R2", "5.1k", "Resistor_SMD:R_0402_1005Metric", {"1": "CC2", "2": "GND"}, lcsc="C25905")
part("D1", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DP_C", "2": "GND", "3": "USB_DM_C", "4": "USB_DM_MCU",
      "5": "VBUS", "6": "USB_DP_MCU"}, lcsc="C7519", comment="USB ESD")

# TP4056 1S charger.  Pinout verified vs the Nanjing Top Power TP4056-42-ESOP8
# datasheet pin table and cross-checked against an independent KiCad symbol
# (corecode/kicad-libs tp4056.kicad_sym): 1 TEMP, 2 PROG, 3 GND, 4 VCC, 5 BAT,
# 6 STDBY (open-collector, active low), 7 CHRG (open-collector, active low),
# 8 CE (input, active high), EP=GND (datasheet-recommended thermal/ground pad).
# TEMP grounded = NTC disabled; PROG 1.2k ~ 1A; CE tied straight to VCC since
# this design has no software charge-enable line (always-enabled when powered,
# matching the common reference application circuit).
# Previous map shorted STDBY straight to VBAT (pin 6) and had no CE drive at
# all (pin 8 aliased to STDBY_N) -- both fixed here.
part("U4", "TP4056-42-ESOP8", "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.81mm",
     {"1": "GND", "2": "PROG", "3": "GND", "4": "VBUS", "5": "VBAT", "6": "STDBY_N",
      "7": "CHRG_N", "8": "VBUS", "9": "GND"}, lcsc="C16581",
     comment="TP4056 pinout verified vs datasheet + independent KiCad symbol")
part("R3", "1.2k", "Resistor_SMD:R_0402_1005Metric", {"1": "PROG", "2": "GND"}, lcsc="C4180")
part("C1", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "VBUS", "2": "GND"}, lcsc="C15850")
part("C2", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "VBAT", "2": "GND"}, lcsc="C15850")
# optional bench-power Schottky VBUS->VBAT (DNP: populate only to run w/o battery)
part("D2", "SS34-DNP", "Diode_SMD:D_SMA", {"2": "VBUS", "1": "VBAT"},
     lcsc="C8678", populate=False, comment="bench power only; DO NOT populate with a battery")

# SY8089 buck VBAT -> 3V3 / 2A.  FB = 0.6V; 3V3 = 0.6*(1+R4/R5)
# SOT-23-5 pinout (1 EN, 2 GND, 3 LX/SW, 4 IN/VIN, 5 FB) confirmed against
# the Silergy SY8089/SY8089A application note pin table -- matches the
# existing map exactly, no change needed.
part("U5", "SY8089AAAC", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "3V3_EN", "2": "GND", "3": "SW3V3", "4": "VBAT", "5": "FB3V3"},
     lcsc="C78988", comment="SY8089 pinout verified vs Silergy application note")
# LCSC C408412 is actually a Sunlord MWSA0503S-100MT = 10uH/2.8A(min)sat,
# NOT 2.2uH as the value field previously claimed -- JLCPCB SMT assembly
# stuffs whichever physical part the LCSC code resolves to, so the real
# board would have shipped with 10uH regardless of the printed value.
# 10uH is higher than the ~2.2-4.7uH typically recommended for this IC
# class at 2A/~1.5MHz (lower ripple current, slower transient response)
# but well within safe operating range -- not a stability or rating issue,
# current margin (2.8A min sat vs 2A regulator max) is adequate. Value
# corrected to match the real part; swap for a 2.2-3.3uH/>=2.5A 0805 part
# if faster transient response is wanted.
part("L1", "10uH", "Inductor_SMD:L_0805_2012Metric", {"1": "SW3V3", "2": "3V3"},
     lcsc="C408412", comment="buck inductor, value corrected to match real LCSC part")
part("C3", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "VBAT", "2": "GND"}, lcsc="C15850")
part("C4", "22uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "3V3", "2": "GND"}, lcsc="C45783")
part("R4", "453k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": "FB3V3"}, lcsc="C123734")
part("R5", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "FB3V3", "2": "GND"}, lcsc="C25741")
part("R6", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3_EN", "2": "VBAT"}, lcsc="C25741",
     comment="buck enable pull-up (always on)")

# ---- ESP32-P4 CPU core DC-DC (~1.2V, external buck U10) -----------------
# Topology + values transcribed from the official ESP32-P4 Hardware Design
# Guidelines TLV62569 reference schematic (rev 3.0 and later) -- the Espressif-
# verified core supply.  Chain: 3V3 (+C36) -> U10.VIN; U10.SW -> L2 -> VDD_CORE;
# VDD_CORE -> C5 (output) and R30 -> FB_DCDC; FB_DCDC -> R31 -> GND and U10.FB;
# C37 sits across R30 (feed-forward).  R30 == R31 => Vout = 2*Vfb, reproducing
# the reference's 1:1 divider and thus Espressif's intended core voltage *by
# construction* (no need to independently know the exact core voltage).  Per the
# guideline, for chip rev v3.0+ the FB resistor and FB capacitor MUST be
# populated (done).  Substitutions vs the reference -- all using parts already
# validated/in-stock for this board and all electrically non-critical: input cap
# 10uF instead of 4.7uF (more headroom); divider 453k/453k instead of 499k/499k
# (identical 1:1 ratio -> identical Vout, feed-forward zero within ~10%); feed-
# forward cap 20pF instead of 22pF (<10%).
part("U10", "TLV62569DBVR", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "EN_DCDC", "2": "GND", "3": "SW_CORE", "4": "3V3", "5": "FB_DCDC"},
     lcsc="C141836", comment="ESP32-P4 core DC-DC (Espressif-verified TLV62569 ref design)")
part("L2", "2.2uH", "Inductor_SMD:L_Cenker_CKCS3015", {"1": "SW_CORE", "2": "VDD_CORE"},
     lcsc="C43389", comment="core DC-DC inductor, Sunlord SWPA3015S2R2MT 2.2uH/2A 3x3mm")
part("C5", "22uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "VDD_CORE", "2": "GND"},
     lcsc="C45783", comment="core DC-DC output cap (22uF per ref)")
part("C36", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "3V3", "2": "GND"},
     lcsc="C15850", comment="core DC-DC input cap (10uF; ref calls 4.7uF)")
part("C37", "20pF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_CORE", "2": "FB_DCDC"},
     lcsc="C1554", comment="core DC-DC feed-forward cap (20pF; ref calls 22pF)")
part("R30", "453k", "Resistor_SMD:R_0402_1005Metric", {"1": "VDD_CORE", "2": "FB_DCDC"},
     lcsc="C123734", comment="core DC-DC FB divider top (453k; ref calls 499k, ratio is what matters)")
part("R31", "453k", "Resistor_SMD:R_0402_1005Metric", {"1": "FB_DCDC", "2": "GND"},
     lcsc="C123734", comment="core DC-DC FB divider bottom (453k, matched to R30)")

# VBAT divider -> ADC (100k/100k)
part("R7", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT", "2": "VBAT_SENSE"}, lcsc="C25741")
part("R8", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT_SENSE", "2": "GND"}, lcsc="C25741")
part("C6", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VBAT_SENSE", "2": "GND"}, lcsc="C1525")

# Internal-LDO rail decoupling (checklist values; each rail is now separate
# from 3V3 so it needs its own bypass near the pins):
#   VDD_MIPI (2.5V): 1uF + 0.1uF (checklist also lists a 10nF HF cap -- omitted
#     only because no verified 0402 10nF part was on hand; add if desired).
#   VDD_FLASHIO (3.3V) and VDD_PSRAM (1.8V): 1uF + 0.1uF each.
part("C7", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_MIPI", "2": "GND"}, lcsc="C52923")
part("C42", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_MIPI", "2": "GND"}, lcsc="C1525")
part("C38", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "GND"}, lcsc="C52923")
part("C39", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "GND"}, lcsc="C1525")
part("C40", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_PSRAM", "2": "GND"}, lcsc="C52923")
part("C41", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_PSRAM", "2": "GND"}, lcsc="C1525")

# ==========================================================================
# P4 SUPPORT: crystal, reset, boot, REXT, decoupling
# ==========================================================================
part("Y1", "40MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
     {"1": "XTAL_P", "2": "GND", "3": "XTAL_N", "4": "GND"}, lcsc="C9002",
     comment="VERIFY load caps for chosen xtal")
part("C8", "10pF", "Capacitor_SMD:C_0402_1005Metric", {"1": "XTAL_P", "2": "GND"}, lcsc="C1555")
part("C9", "10pF", "Capacitor_SMD:C_0402_1005Metric", {"1": "XTAL_N", "2": "GND"}, lcsc="C1555")
part("R9", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": "CHIP_PU"}, lcsc="C25744")
part("C10", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "CHIP_PU", "2": "GND"}, lcsc="C52923")
part("SW1", "RESET", "Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
     {"1": "CHIP_PU", "2": "GND"}, lcsc="C720477")
part("SW2", "BOOT", "Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
     {"1": "BOOT", "2": "GND"}, lcsc="C720477", comment="VERIFY P4 boot strap = GPIO35")
part("R10", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": "BOOT"}, lcsc="C25744")
part("R11", "4.02k", "Resistor_SMD:R_0402_1005Metric", {"1": "CSI_REXT", "2": "GND"}, lcsc="C25752",
     comment="CSI termination resistor per esp32p4-schematic-checklist.rst (4.02k required)")
part("R12", "4.02k", "Resistor_SMD:R_0402_1005Metric", {"1": "DSI_REXT", "2": "GND"}, lcsc="C25752",
     comment="DSI termination resistor (DSI unused, populated for completeness)")
# flash IO pull-ups -- pulled to the flash IO rail (VDD_FLASHIO), not 3V3, so
# the pull level always tracks the flash IO voltage
part("R13", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "FLASH_CS"}, lcsc="C25744")
part("R14", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "FLASH_IO2"}, lcsc="C25744")
part("R15", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "VDD_FLASHIO", "2": "FLASH_IO3"}, lcsc="C25744")
# SDIO pull-ups (CMD + DAT0..3)
for i, net in enumerate(["SDIO_CMD", "SDIO_D0", "SDIO_D1", "SDIO_D2", "SDIO_D3"]):
    part(f"R{16+i}", "51k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": net},
         lcsc="C25905", comment="SDIO pull-up")
# C6 boot strap pull-up (normal run)
part("R21", "10k", "Resistor_SMD:R_0402_1005Metric", {"1": "3V3", "2": "C6_BOOT"}, lcsc="C25744")
part("C11", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VDD_CORE", "2": "GND"}, lcsc="C1525")

# P4 + flash decoupling: a 100nF per power pin cluster + bulk
_dc = 12
for i in range(14):
    part(f"C{_dc+i}", "100nF", "Capacitor_SMD:C_0402_1005Metric",
         {"1": "3V3", "2": "GND"}, lcsc="C1525", comment="P4 rail decoupling")
part("C26", "10uF", "Capacitor_SMD:C_0603_1608Metric", {"1": "3V3", "2": "GND"}, lcsc="C19702")
part("C27", "10uF", "Capacitor_SMD:C_0603_1608Metric", {"1": "3V3", "2": "GND"}, lcsc="C19702")

# ==========================================================================
# SENSORS
# ==========================================================================
# ICM-42688-P IMU (SPI mode).  LGA-14 pinout re-verified against the TDK
# InvenSense DS-000347 pin table and cross-checked against an independent,
# professionally-generated KiCad symbol (manufacturer/IPC-7351B-tagged,
# rishikesh2715/STM32F7_FC "Sensors & Peripherals.kicad_sch"): 1 AP_SDO/AP_AD0
# (SPI SDO), 2/3/7/10/11 RESV, 4 INT1, 5 VDDIO, 6 GND, 8 VDD, 9 INT2/FSYNC/
# CLKIN (unused -> GND per datasheet guidance for unused FSYNC), 12 AP_CS,
# 13 AP_SCLK, 14 AP_SDI.  Previous map grounded BOTH real power pins (VDDIO
# on its pin 5, VDD on its pin 8 -- chip could never power up) and wired
# every host SPI signal to reserved/wrong pads (host CS->real SDO pin, host
# SCLK->a RESV pin, host MOSI->another RESV pin, real AP_CS->GND, real
# AP_SCLK->3V3, real AP_SDI->GND).  Pad 15 is the generic footprint's
# exposed/heatsink pad (the real LGA-14 has no such pad; tied to GND as the
# conservative choice for an unused copper feature).  Footprint itself is
# still a generic DHVQFN-14 substitute, not the exact LGA-14 land pattern --
# see KNOWN_GAPS.md item 8.
part("U6", "ICM-42688-P", "Package_DFN_QFN:DHVQFN-14-1EP_2.5x3mm_P0.5mm_EP1x1.5mm",
     {"1": "SPI_MISO",       # AP_SDO/AP_AD0
      "2": "GND",            # RESV
      "3": "GND",            # RESV
      "4": "IMU_INT",        # INT1
      "5": "3V3",            # VDDIO
      "6": "GND",            # GND
      "7": "GND",            # RESV
      "8": "3V3",            # VDD
      "9": "GND",            # INT2/FSYNC/CLKIN, unused
      "10": "GND",           # RESV
      "11": "GND",           # RESV
      "12": "CS_IMU",        # AP_CS
      "13": "SPI_SCLK",      # AP_SCLK
      "14": "SPI_MOSI",      # AP_SDI
      "15": "GND"},          # exposed/heatsink pad (generic footprint only)
     lcsc="C2840095", comment="ICM-42688-P pinout verified vs datasheet + independent KiCad symbol")
part("C28", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525")
part("C29", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525")

# SPL06-001 barometer (I2C, SDO->GND = 0x76).  LGA-8 pad map re-verified
# against a real reference design using the *same* KiCad footprint
# (iNavFlight/hardware BARO1/SPL06.kicad_pcb) and the Bosch/Goertek
# SPL06-001 pin table: 1 GND, 2 SDO (addr select), 3 SDA, 4 SCL, 5 CSB
# (tie high for I2C mode), 6 VDDIO, 7 GND, 8 VDD.  Previous map had real
# pin 6 (VDDIO) tied to GND (IO supply dead), real pin 3 (SDA) hard-wired
# to 3V3 (a bus short the instant anything pulls the shared SDA line low),
# and the host's I2C_SDA net wired to real pin 1 (GND) -- shorting the
# shared I2C bus to ground through this chip, which would have broken
# every other device on the same bus, not just this sensor.
part("U7", "SPL06-001", "Package_LGA:Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering",
     {"1": "GND", "2": "GND", "3": "I2C_SDA", "4": "I2C_SCL",
      "5": "3V3", "6": "3V3", "7": "GND", "8": "3V3"},
     lcsc="C2684428", comment="SPL06-001 pinout verified vs reference design using same footprint")
part("C30", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525")

# VL53L1X ToF (I2C 0x29, XSHUT gated).  Bottom side.  LGA-12 verified vs the
# ST VL53L1X datasheet pin table: 1 AVDDVCSEL, 2 AVSSVCSEL, 3/4/6/12 GND,
# 5 XSHUT, 7 GPIO1 (INT, open-drain), 8 DNC (leave floating), 9 SDA, 10 SCL,
# 11 AVDD.  Footprint is KiCad's official Sensor_Distance:ST_VL53L1x land.
part("U8", "VL53L1X", "Sensor_Distance:ST_VL53L1x",
     {"1": "3V3", "2": "GND", "3": "GND", "4": "GND", "5": "VL53_XSHUT",
      "6": "GND", "7": "TOF_INT", "9": "I2C_SDA", "10": "I2C_SCL",
      "11": "3V3", "12": "GND"},
     lcsc="C2970716", side="B",
     comment="VL53L1x LGA-12 verified vs ST datasheet; pin8 DNC left floating")
part("C31", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525", side="B")

# PMW3901 optical flow (SPI).  Bottom side, COB-28 custom footprint.
part("U9", "PMW3901MB", "strat:PMW3901MB-TXQT",
     {"1": "3V3", "2": "GND", "3": "SPI_SCLK", "4": "SPI_MOSI", "5": "SPI_MISO",
      "6": "CS_FLOW", "7": "GND", "8": "3V3"},
     lcsc="C2920328", side="B",
     comment="VERIFY COB-28 pinout; reflow-on-JLC unverified -> fallback J3")
part("C32", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525", side="B")
# fallback CJMCU-3901 breakout header (DNP, parallels U9)
part("J3", "FLOW_HDR", "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical",
     {"1": "3V3", "2": "CS_FLOW", "3": "GND", "4": "SPI_SCLK",
      "5": "SPI_MOSI", "6": "SPI_MISO", "7": "GND", "8": "3V3"},
     populate=False, side="B", comment="fallback flow module (populate U9 OR J3)")

# ==========================================================================
# CAMERA — 15-pin 0.5mm FFC (Raspberry-Pi camera pinout). Pinout VERIFY.
# ==========================================================================
part("J4", "CAM_FFC15", "Connector_FFC-FPC:Hirose_FH12-15S-0.5SH_1x15-1MP_P0.50mm_Horizontal",
     {"1": "GND", "2": "CSI_D0N", "3": "CSI_D0P", "4": "GND",
      "5": "CSI_D1N", "6": "CSI_D1P", "7": "GND", "8": "CSI_CKN",
      "9": "CSI_CKP", "10": "GND", "11": "CAM_PWDN", "12": "CAM_GPIO",
      "13": "I2C_SCL", "14": "I2C_SDA", "15": "3V3"},
     lcsc="C2884418", comment="VERIFY RPi 15-pin FFC pinout & CSI lane order/polarity")
part("C33", "1uF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C52923")

# ==========================================================================
# MOTORS — 4x low-side NFET + flyback, corner pads
# ==========================================================================
for i in range(1, 5):
    g = f"M{i}_G"
    d = f"M{i}_D"
    part(f"Q{i}", "AO3400A", "Package_TO_SOT_SMD:SOT-23",
         {"1": d, "2": "GND", "3": "M%d_GATE" % i}, lcsc="C20917",
         comment="motor low-side NFET (1=D,2=S,3=G)")
    part(f"R{21+i}", "100R", "Resistor_SMD:R_0402_1005Metric",
         {"1": g, "2": "M%d_GATE" % i}, lcsc="C25092", comment="gate series")
    part(f"R{25+i}", "100k", "Resistor_SMD:R_0402_1005Metric",
         {"1": "M%d_GATE" % i, "2": "GND"}, lcsc="C25741", comment="gate pulldown (props off at boot)")
    part(f"D{2+i}", "SS34", "Diode_SMD:D_SMA",
         {"2": d, "1": "VBAT"}, lcsc="C8678", comment="flyback (cathode=VBAT)")
    part(f"J{4+i}", f"MOTOR{i}", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
         {"1": "VBAT", "2": d}, lcsc="", comment=f"motor {i} pads (VBAT + drain)")

# ==========================================================================
# STATUS LEDs — 2x WS2812B-2020 from VBAT
# ==========================================================================
part("LED1", "WS2812B-2020", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm",
     {"1": "VBAT", "2": "LED_DIN", "3": "GND", "4": "LED_D12"},
     lcsc="C965555", comment="status LED 1 (DOUT->LED2)")
part("LED2", "WS2812B-2020", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm",
     {"1": "VBAT", "2": "LED_D12", "3": "GND", "4": "LED_DOUT"},
     lcsc="C965555", comment="status LED 2")
part("C34", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VBAT", "2": "GND"}, lcsc="C1525")
part("C35", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "VBAT", "2": "GND"}, lcsc="C1525")

# ==========================================================================
# EXPANSION + DEBUG test pads
# ==========================================================================
part("J9", "EXP", "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical",
     {"1": "3V3", "2": "GND", "3": "VBAT", "4": "I2C_SDA", "5": "I2C_SCL", "6": "EXP_IO"},
     lcsc="", comment="expansion (deck) connector")
part("J10", "DBG", "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical",
     {"1": "GND", "2": "U0TXD", "3": "U0RXD", "4": "3V3"},
     lcsc="", comment="P4 UART0 console pads")
part("J11", "C6DBG", "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical",
     {"1": "GND", "2": "C6_U0TXD", "3": "C6_U0RXD", "4": "C6_BOOT"},
     lcsc="", comment="C6 slave-flash pads")

# Power-net declarations (for ERC PWR_FLAG placement by the schematic gen)
POWER_NETS = ["VBAT", "VBUS", "3V3", "GND", "VDD_CORE", "VDD_MIPI"]

# Board outline (mm), rounded rect, 4x M2 mounting holes at 36mm square pitch
# Tello-style mainboard: narrow PORTRAIT board (≈1:2), like the real Tello
# main PCB — optical cluster at the nose, shielded MCU/RF zones in the middle,
# motor pads at the four corners, USB on the side edge. y=0 is the camera nose.
BOARD = dict(w=36.0, h=70.0, corner_r=4.0,
             mount_pitch_x=26.0, mount_pitch_y=60.0, mount_d=2.2)


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
