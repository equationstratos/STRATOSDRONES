#!/usr/bin/env python3
"""STRATOS TINYHOOP AIO — authoritative design database (single source of truth).

The all-in-one board for the TinyHoop MK1 (Fr4n10-001): the 2.5" wide-X,
programmable/swarm FPV. Same whoop-standard 25.5x25.5 M2 mounting as the FPV
AIO, same PCB-as-code pipeline (edit THIS file, then `make` — the KiCad
stages need pcbnew + kicad-cli; this file is pure Python and self-checks).

This board IS the STRATOS FPV AIO (hardware/pcb_fpv) plus the pieces the
show/swarm mission needs — so it is defined by *importing* that verified
database and layering the deltas, rather than re-copying 500 lines:

  + PMW3901 optical flow + VL53L1X ToF RE-ADDED (down-facing, bottom side) —
    the verified blocks from the Fr4n7 board (hardware/pcb): STABILIZED mode
    (position hold, drone-show hover) needs them back.
  + SX1262 LoRa module (Ebyte E22-900M22S, EU868) on the shared SPI bus with
    dedicated CS/BUSY/DIO1/RST — the no-Wi-Fi fleet link. CASTELLATED and
    OPTIONAL: a solo build leaves it unpopulated.
  + GPS/compass connector J15 (UART + shared I2C) for outdoor absolute
    positioning (M4).
  ~ VBAT divider recomputed for 2S-3S: /5 (4x100k top, 100k bottom) so 12.6V
    -> 2.52V at the ADC (the FPV AIO used /3 for 2S only).
  ~ Board grown to 34x34 (mount pattern unchanged) — the FPV AIO's 4 ESC
    stages + P4 + C6, now plus flow/ToF/LoRa/GPS, do not fit in 32x32.

Honesty: everything inherited keeps its status. NEW parts (SX1262 module pad
map, GPS connector) are VERIFY / fab-blocking — see KNOWN_GAPS.md. The ESC
FET current rating for 1203-1303 motors at up to 3S is a VERIFY too.
"""
import importlib.util
import os

# ---- import the verified STRATOS FPV AIO database as the base ----
_HERE = os.path.dirname(os.path.abspath(__file__))
_FPV = os.path.join(_HERE, "..", "..", "pcb_fpv", "scripts", "design.py")
_spec = importlib.util.spec_from_file_location("design_fpv", _FPV)
fpv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fpv)

part = fpv.part          # appends to the shared component list fpv.C
p4 = fpv.p4
C = fpv.all_components()  # same list object; part() keeps appending to it

# ---- extend the firmware pin map (new signals on free P4 GPIOs) ----
PINMAP = dict(fpv.PINMAP)
PINMAP.update({
    "CS_FLOW":   "GPIO13",   # PMW3901 chip-select (SPI, shared bus)
    "LORA_CS":   "GPIO26", "LORA_BUSY": "GPIO27",
    "LORA_DIO1": "GPIO28", "LORA_RST":  "GPIO29",
    "GPS_TX":    "GPIO30", "GPS_RX":    "GPIO31",
    "VL53_XSHUT": "GPIO23",  # ToF shutdown/address gate
})

# wire the new signals into the already-placed ESP32-P4 (U1) pin dict
_u1 = next(c for c in C if c["ref"] == "U1")
_new_roles = {
    "CS_FLOW": "CS_FLOW", "VL53_XSHUT": "VL53_XSHUT",
    "LORA_CS": "LORA_CS", "LORA_BUSY": "LORA_BUSY",
    "LORA_DIO1": "LORA_DIO1", "LORA_RST": "LORA_RST",
    "GPS_TX": "GPS_TX", "GPS_RX": "GPS_RX",
}
for _role, _net in _new_roles.items():
    _pad = p4(PINMAP[_role])
    assert _pad not in _u1["pins"], f"P4 pad {_pad} already used ({_role})"
    _u1["pins"][_pad] = _net

# ==========================================================================
# RE-ADDED SENSORS (bottom side) — the STABILIZED-mode position-hold pair,
# verified blocks lifted verbatim from hardware/pcb/scripts/design.py.
# ==========================================================================
part("U8", "VL53L1X", "Sensor_Distance:ST_VL53L1x",
     {"1": "3V3", "2": "GND", "3": "GND", "4": "GND", "5": "VL53_XSHUT",
      "6": "GND", "7": "TOF_INT", "9": "I2C_SDA", "10": "I2C_SCL",
      "11": "3V3", "12": "GND"},
     lcsc="C2970716", side="B",
     comment="VL53L1x LGA-12 verified vs ST datasheet; pin8 DNC left floating")
part("C80", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"},
     lcsc="C1525", side="B")

part("U9", "PMW3901MB", "strat:PMW3901MB-TXQT",
     {"1": "3V3", "2": "GND", "3": "SPI_SCLK", "4": "SPI_MOSI", "5": "SPI_MISO",
      "6": "CS_FLOW", "7": "GND", "8": "3V3"},
     lcsc="C2920328", side="B",
     comment="VERIFY COB-28 pinout; reflow-on-JLC unverified -> fallback J16")
part("C81", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"},
     lcsc="C1525", side="B")
part("J16", "FLOW_HDR", "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical",
     {"1": "3V3", "2": "CS_FLOW", "3": "GND", "4": "SPI_SCLK",
      "5": "SPI_MOSI", "6": "SPI_MISO", "7": "GND", "8": "3V3"},
     populate=False, side="B", comment="fallback flow module (populate U9 OR J16)")

# ==========================================================================
# LoRa — SX1262 module (Ebyte E22-900M22S), EU868 fleet link. Castellated,
# OPTIONAL populate. Shares SPI2 (SCLK/MOSI/MISO) with its own CS + BUSY +
# DIO1 + reset. u.FL antenna, keepout opposite the C6 antenna edge.
#
# VERIFY (fab-blocking): the E22-900M22S castellated pad map below is written
# from the module's published pinout, NOT a datasheet-in-hand reflow trial.
# The module carries its own SX1262 + TCXO + PA/LNA + RF switch; the board
# only routes SPI + 4 control lines + 3V3 + GND + antenna.
# ==========================================================================
part("U12", "E22-900M22S", "RF_Module:E22-900M22S",
     {"1": "GND", "2": "GND",
      "3": "LORA_BUSY", "4": "LORA_DIO1", "5": "LORA_DIO2_NC", "6": "LORA_DIO3_NC",
      "7": "3V3", "8": "LORA_MISO", "9": "LORA_MOSI", "10": "SPI_SCLK",
      "11": "LORA_CS", "12": "LORA_RST", "13": "LORA_TXEN", "14": "LORA_RXEN",
      "15": "GND", "16": "ANT", "17": "GND"},
     lcsc="", populate=False, fp_alt=["Connector_PinHeader_1.27mm:PinHeader_2x09_P1.27mm_Vertical"],
     comment="VERIFY E22-900M22S castellated pad map + antenna keepout before fab")
# the module shares the bus data lines: LORA_MISO/MOSI merge onto SPI_MISO/MOSI
part("R40", "0", "Resistor_SMD:R_0402_1005Metric", {"1": "SPI_MISO", "2": "LORA_MISO"},
     lcsc="C17168", comment="bus link (0R): SX1262 MISO onto shared SPI")
part("R41", "0", "Resistor_SMD:R_0402_1005Metric", {"1": "SPI_MOSI", "2": "LORA_MOSI"},
     lcsc="C17168", comment="bus link (0R): SX1262 MOSI onto shared SPI")
part("C82", "100nF", "Capacitor_SMD:C_0402_1005Metric", {"1": "3V3", "2": "GND"}, lcsc="C1525")
part("C83", "10uF", "Capacitor_SMD:C_0805_2012Metric", {"1": "3V3", "2": "GND"}, lcsc="C15850",
     comment="SX1262 TX current burst reservoir")
part("J17", "ANT_UFL", "RF_Connector:U.FL_Molex_MCRF-LP_73412-0110_Vertical",
     {"1": "ANT", "2": "GND"}, lcsc="", comment="LoRa u.FL antenna")

# ==========================================================================
# GPS / compass connector J15 (UART + shared I2C for the magnetometer).
# ==========================================================================
part("J15", "GPS_COMPASS", "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal",
     {"1": "5V", "2": "GND", "3": "GPS_TX", "4": "GPS_RX",
      "5": "I2C_SDA", "6": "I2C_SCL"}, lcsc="",
     fp_alt=["Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical"],
     comment="GPS+compass module (5V, GND, P4TX->GPS RX, P4RX<-GPS TX, I2C mag)")

# ==========================================================================
# VBAT divider — REPLACE the FPV AIO /3 chain with /5 for 2S-3S (max 12.6V).
# 4x100k on top, 100k bottom: 12.6V -> 2.52V at the ADC pin (< 3.3V FSR).
# ==========================================================================
# remove the inherited /3 divider resistors (R7, R33, R8) and rebuild /5
_drop = {"R7", "R33", "R8"}
C[:] = [c for c in C if c["ref"] not in _drop]
part("R7",  "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT", "2": "VBAT_D1"}, lcsc="C25741")
part("R33", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT_D1", "2": "VBAT_D2"}, lcsc="C25741")
part("R34", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT_D2", "2": "VBAT_D3"}, lcsc="C25741")
part("R35", "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT_D3", "2": "VBAT_SENSE"}, lcsc="C25741")
part("R8",  "100k", "Resistor_SMD:R_0402_1005Metric", {"1": "VBAT_SENSE", "2": "GND"}, lcsc="C25741")

# ---- board outline: grown to 34x34, 25.5 mount unchanged ----
BOARD = dict(fpv.BOARD)
BOARD.update(w=34.0, h=34.0)

POWER_NETS = fpv.POWER_NETS + ["ANT"]


def all_components():
    return C


if __name__ == "__main__":
    nets = {}
    for c in C:
        for pad, net in c["pins"].items():
            nets.setdefault(net, []).append((c["ref"], pad))
    print(f"components: {len(C)}  (FPV AIO base + TinyHoop deltas)")
    print(f"distinct nets: {len(nets)}")
    single = [n for n, v in nets.items() if len(v) == 1 and n not in ("GND",)]
    print(f"unique-pin nets (test points / VERIFY / NC): {len(single)}")

    # ESC channels still complete (inherited)
    for i in range(1, 5):
        for k in "ABC":
            assert len(nets.get(f"M{i}_{k}", [])) >= 3, f"phase M{i}_{k} incomplete"
        assert f"M{i}_G" in nets, f"missing ESC signal M{i}_G"
    # TinyHoop additions present and netted
    for n in ["CS_FLOW", "VL53_XSHUT", "LORA_CS", "LORA_BUSY", "LORA_DIO1",
              "LORA_RST", "ANT", "GPS_TX", "GPS_RX"]:
        assert n in nets, f"missing TinyHoop net {n}"
    # flow + ToF are wired to the MCU
    assert len(nets["CS_FLOW"]) >= 2, "flow CS not connected both ends"
    assert len(nets["I2C_SDA"]) >= 3, "ToF/GPS not on the I2C bus"
    # /5 divider: 4 series + 1 to ground, chain intact
    for n in ["VBAT_D1", "VBAT_D2", "VBAT_D3"]:
        assert len(nets[n]) == 2, f"divider node {n} must join exactly 2 R"
    assert len(nets["VBAT_SENSE"]) >= 2, "VBAT_SENSE incomplete"
    print("TinyHoop sanity: flow+ToF+LoRa+GPS netted, /5 divider intact  OK")

    dup = {}
    for c in C:
        assert c["ref"] not in dup, f"duplicate ref {c['ref']}"
        dup[c["ref"]] = 1
    print("refs unique  OK")
    bom = [c for c in C if c["populate"] and c["lcsc"]]
    print(f"BOM lines with LCSC: {len(bom)}")
