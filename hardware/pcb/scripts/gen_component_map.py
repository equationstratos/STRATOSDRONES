#!/usr/bin/env python3
"""Render an annotated component map of the board (top + bottom views).

For each placed component it draws a box at its real position, coloured by
subsystem and labelled with the reference designator. A side legend lists
what every reference is, so you can orient yourself while assembling. Output:
hardware/pcb/preview/component_map.png

Run:  python3 gen_component_map.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

import pcbnew  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
BRD = os.path.join(PCB_DIR, "stratosdrone.kicad_pcb")
OUT = os.path.join(PCB_DIR, "preview", "component_map.png")

sys.path.insert(0, HERE)
import design  # noqa: E402

# subsystem classification + colour by reference prefix / specific refs
SUBSYS = {
    "MCU / Wi-Fi": (["U1", "U2", "U3", "Y1"], "#3b6fb6"),
    "Power / charge": (["U4", "U5", "L1", "L2", "D1", "D2", "J1", "J2"], "#c0392b"),
    "Sensors": (["U6", "U7", "U8", "U9", "J3"], "#27ae60"),
    "Camera": (["J4"], "#8e44ad"),
    "Motors": (["Q1", "Q2", "Q3", "Q4", "J5", "J6", "J7", "J8"], "#e67e22"),
    "LEDs / IO": (["LED1", "LED2", "SW1", "SW2", "J9", "J10", "J11"], "#16a085"),
}
PASSIVE = "#b0b0b0"

# human-readable names for the labelled (non-passive) parts
NAMES = {c["ref"]: c["value"] for c in design.all_components()}
DESC = {
    "U1": "ESP32-P4 (flight + camera + H.264)", "U2": "16MB QSPI flash",
    "U3": "ESP32-C6 Wi-Fi module", "Y1": "40 MHz crystal",
    "U4": "TP4056 1S charger", "U5": "SY8089 3V3 buck", "L1": "buck inductor",
    "L2": "P4 core DCDC inductor", "D1": "USB ESD", "D2": "bench Schottky (DNP)",
    "J1": "battery JST-PH", "J2": "USB-C",
    "U6": "ICM-42688-P IMU", "U7": "SPL06 barometer",
    "U8": "VL53L1X ToF (bottom)", "U9": "PMW3901 flow (bottom)",
    "J3": "flow module header (bottom, DNP)", "J4": "camera FFC (15-pin)",
    "Q1": "motor 1 FET", "Q2": "motor 2 FET", "Q3": "motor 3 FET", "Q4": "motor 4 FET",
    "J5": "motor 1 pads", "J6": "motor 2 pads", "J7": "motor 3 pads", "J8": "motor 4 pads",
    "LED1": "status LED 1", "LED2": "status LED 2", "SW1": "reset", "SW2": "boot",
    "J9": "expansion", "J10": "P4 UART pads", "J11": "C6 UART pads",
}


def ref_color(ref):
    for _, (refs, col) in SUBSYS.items():
        if ref in refs:
            return col
    return PASSIVE


def main():
    board = pcbnew.LoadBoard(BRD)
    b = design.BOARD
    W, H = b["w"], b["h"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 9))
    for ax, side, title in ((axes[0], "top", "TOP (component side)"),
                            (axes[1], "bottom", "BOTTOM (sensor side)")):
        ax.set_title(f"STRATOSDRONE Tello-style board — {title}", fontsize=11, weight="bold")
        ax.add_patch(mpatches.FancyBboxPatch(
            (0, 0), W, H, boxstyle="round,pad=0,rounding_size=4",
            fill=False, ec="black", lw=1.5))
        ax.text(W / 2, -2, "camera nose ▲ (front)" if True else "", ha="center", fontsize=8)
        ax.text(W / 2, H + 2.5, "USB-C / battery (rear)", ha="center", fontsize=8)
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            flipped = fp.IsFlipped()
            on_this = (side == "bottom") == flipped
            if not on_this:
                continue
            bb = fp.GetBoundingBox()
            x = pcbnew.ToMM(bb.GetX())
            y = pcbnew.ToMM(bb.GetY())
            w = pcbnew.ToMM(bb.GetWidth())
            h = pcbnew.ToMM(bb.GetHeight())
            # mirror x for the bottom view (looking from below)
            if side == "bottom":
                x = W - x - w
            col = ref_color(ref)
            labelled = ref in DESC
            ax.add_patch(mpatches.Rectangle(
                (x, y), w, h, facecolor=col, edgecolor="black",
                lw=0.4, alpha=0.85 if labelled else 0.5))
            if labelled and w > 1.5 and h > 1.5:
                ax.text(x + w / 2, y + h / 2, ref, ha="center", va="center",
                        fontsize=6.5, weight="bold", color="white")
        ax.set_xlim(-6, W + 6)
        ax.set_ylim(H + 6, -6)   # y down, nose at top
        ax.set_aspect("equal")
        ax.axis("off")

    # legend (subsystems) + reference list
    handles = [mpatches.Patch(color=col, label=name) for name, (_, col) in SUBSYS.items()]
    handles.append(mpatches.Patch(color=PASSIVE, label="passives (R/C/ESD)"))
    fig.legend(handles=handles, loc="lower center", ncol=7, fontsize=8, frameon=False)

    lines = [f"{r:<5} {DESC[r]}" for r in sorted(DESC, key=lambda r: (r[0], int(
        "".join(filter(str.isdigit, r)) or 0)))]
    fig.text(0.5, 0.045, "   |   ".join(lines[:0]), fontsize=6)  # spacer
    fig.suptitle("Component map — see the table below for every reference",
                 y=0.98, fontsize=9, color="#444")
    # reference table as figure text, two columns
    half = (len(lines) + 1) // 2
    fig.text(0.07, 0.005, "\n".join(lines[:half]), fontsize=6.2, family="monospace",
             va="bottom")
    fig.text(0.52, 0.005, "\n".join(lines[half:]), fontsize=6.2, family="monospace",
             va="bottom")

    plt.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.20, wspace=0.05)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print(f"wrote {OUT}")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
