#!/usr/bin/env python3
"""Export JLCPCB fabrication artifacts from the design + generated board.

Outputs into hardware/pcb/jlcpcb/:
  bom.csv          JLCPCB "Comment, Designator, Footprint, LCSC Part #"
  cpl.csv          JLCPCB pick-and-place "Designator, Mid X, Mid Y, Layer, Rotation"
  gerbers/         Gerber + drill set (preliminary — board still needs routing)

BOM/CPL are authoritative for assembly and come straight from design.py +
the placed board. Gerbers are a *preliminary* set: the board's signal nets
are not yet routed and zones are unfilled, so regenerate the gerbers from
KiCad after completing routing (see README.md) before ordering.

Run:  python3 export_fab.py
"""
import csv
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
BRD = os.path.join(PCB_DIR, "stratosdrone.kicad_pcb")
OUT = os.path.join(PCB_DIR, "jlcpcb")

sys.path.insert(0, HERE)
import design  # noqa: E402


def export_bom():
    rows = []
    # group identical parts (same value + footprint + lcsc) for assembly
    groups = {}
    for c in design.all_components():
        if not c["populate"] or not c["lcsc"]:
            continue
        key = (c["value"], c["lcsc"], c["fp"])
        groups.setdefault(key, []).append(c["ref"])
    for (value, lcsc, fp), refs in sorted(groups.items(), key=lambda x: x[0][0]):
        rows.append({
            "Comment": value,
            "Designator": ",".join(sorted(refs, key=_natkey)),
            "Footprint": fp.split(":")[-1],
            "LCSC Part #": lcsc,
        })
    path = os.path.join(OUT, "bom.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Comment", "Designator", "Footprint", "LCSC Part #"])
        w.writeheader()
        w.writerows(rows)
    print(f"bom.csv: {len(rows)} assembly lines, "
          f"{sum(len(r['Designator'].split(',')) for r in rows)} placed parts")
    return path


def _natkey(ref):
    import re
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def export_cpl():
    board = pcbnew.LoadBoard(BRD)
    populate = {c["ref"]: c for c in design.all_components()}
    rows = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        c = populate.get(ref)
        if not c or not c["populate"] or not c["lcsc"]:
            continue
        pos = fp.GetPosition()
        layer = "bottom" if fp.IsFlipped() else "top"
        rows.append({
            "Designator": ref,
            "Mid X": f"{pcbnew.ToMM(pos.x):.3f}",
            "Mid Y": f"{pcbnew.ToMM(pos.y):.3f}",
            "Layer": layer,
            "Rotation": f"{fp.GetOrientationDegrees():.0f}",
        })
    rows.sort(key=lambda r: _natkey(r["Designator"]))
    path = os.path.join(OUT, "cpl.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writeheader()
        w.writerows(rows)
    print(f"cpl.csv: {len(rows)} placements")
    os._exit_pending = False
    return path


def export_gerbers():
    gdir = os.path.join(OUT, "gerbers")
    os.makedirs(gdir, exist_ok=True)
    # kicad-cli 7 gerber + drill export (preliminary; board not yet routed)
    layers = ("F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,"
              "F.Mask,B.Mask,Edge.Cuts")
    try:
        subprocess.run(["kicad-cli", "pcb", "export", "gerbers",
                        "--layers", layers, "--no-protel-ext",
                        "-o", gdir + "/", BRD], check=True,
                       capture_output=True, text=True)
        subprocess.run(["kicad-cli", "pcb", "export", "drill",
                        "--format", "excellon", "--excellon-separate-th",
                        "-o", gdir + "/", BRD], check=True,
                       capture_output=True, text=True)
        n = len([f for f in os.listdir(gdir) if not f.startswith(".")])
        print(f"gerbers/: {n} files (PRELIMINARY — re-export after routing)")
    except subprocess.CalledProcessError as e:
        print("gerber export failed:", e.stderr[:300])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    export_bom()
    export_gerbers()
    export_cpl()   # loads board last (pcbnew shutdown crash workaround below)
    sys.stdout.flush()
    os._exit(0)
