#!/usr/bin/env python3
"""Consistency gate: the generated board must match design.py exactly.

Verifies, against stratos_fpv_aio.kicad_pcb:
  1. every populated component is present as a footprint
  2. every pad's assigned net matches design.py
  3. the firmware board_pinmap.h GPIO numbers match design.PINMAP

Exit non-zero on any mismatch (used by CI). Run:  python3 check_consistency.py
"""
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PCB_DIR))
BRD = os.path.join(PCB_DIR, "stratos_fpv_aio.kicad_pcb")
PINMAP_H = os.path.join(REPO, "firmware", "components", "board", "include", "board_pinmap.h")

sys.path.insert(0, HERE)
import design  # noqa: E402


def check_board():
    board = pcbnew.LoadBoard(BRD)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    errors = []
    for c in design.all_components():
        ref = c["ref"]
        if ref not in fps:
            errors.append(f"{ref}: missing from board")
            continue
        fp = fps[ref]
        padnets = {}
        for pad in fp.Pads():
            name = pad.GetPadName() or pad.GetName()
            padnets.setdefault(name, pad.GetNetname())
        for padname, want in c["pins"].items():
            got = padnets.get(padname)
            if got is None:
                errors.append(f"{ref}.{padname}: pad not found on footprint")
            elif got != want:
                errors.append(f"{ref}.{padname}: net '{got}' != design '{want}'")
    return errors


def check_pinmap():
    if not os.path.exists(PINMAP_H):
        return [f"{PINMAP_H} not generated"]
    txt = open(PINMAP_H).read()
    macros = dict(re.findall(r"#define\s+(PIN_\w+)\s+(\d+)", txt))
    want = {
        "PIN_SPI_SCLK": "SPI_SCLK", "PIN_SPI_MOSI": "SPI_MOSI", "PIN_SPI_MISO": "SPI_MISO",
        "PIN_CS_IMU": "CS_IMU", "PIN_CS_FLOW": "CS_FLOW", "PIN_IMU_INT": "IMU_INT",
        "PIN_I2C_SDA": "I2C_SDA", "PIN_I2C_SCL": "I2C_SCL", "PIN_VL53_XSHUT": "VL53_XSHUT",
        "PIN_MOTOR_1": "MOTOR_1", "PIN_MOTOR_2": "MOTOR_2", "PIN_MOTOR_3": "MOTOR_3",
        "PIN_MOTOR_4": "MOTOR_4", "PIN_VBAT_ADC": "VBAT_ADC", "PIN_WS2812": "WS2812",
        "PIN_CAM_PWDN": "CAM_PWDN", "PIN_SDIO_CLK": "SDIO_CLK", "PIN_SDIO_CMD": "SDIO_CMD",
        "PIN_SDIO_D0": "SDIO_D0", "PIN_SDIO_D1": "SDIO_D1", "PIN_SDIO_D2": "SDIO_D2",
        "PIN_SDIO_D3": "SDIO_D3", "PIN_C6_EN": "C6_EN",
    }
    errors = []
    for macro, role in want.items():
        exp = design.PINMAP[role].replace("GPIO", "")
        if macros.get(macro) != exp:
            errors.append(f"{macro}={macros.get(macro)} != design {role}=GPIO{exp}")
    return errors


def main():
    errs = check_board() + check_pinmap()
    if errs:
        print(f"CONSISTENCY FAIL ({len(errs)}):")
        for e in errs[:40]:
            print("  ", e)
        sys.stdout.flush()
        os._exit(1)
    print("consistency OK: board nets and board_pinmap.h match design.py")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
