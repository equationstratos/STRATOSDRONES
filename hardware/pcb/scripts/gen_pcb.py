#!/usr/bin/env python3
"""Generate stratosdrone.kicad_pcb from design.py via the pcbnew 7 API.

Produces a board with: outline + mounting holes, every component footprint
loaded/placed/flipped, all pads net-assigned (complete ratsnest), and copper
pours (GND / 3V3 / VBAT) so the bulk of power pads connect without manual
routing. Signal routing is intentionally left as ratsnest for completion in
the KiCad GUI — see hardware/pcb/KNOWN_GAPS.md.

Footprint resolution tries, in order: vendored lib/*.pretty, then the KiCad
system library named by the 'lib:' prefix. Any miss is reported (never fatal),
so the board always generates.

Run:  python3 gen_pcb.py   (uses the system python with pcbnew)
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PCB_DIR))
OUT = os.path.join(PCB_DIR, "stratosdrone.kicad_pcb")

sys.path.insert(0, HERE)
import design  # noqa: E402

SYS_FP = "/usr/share/kicad/footprints"
VENDOR = [os.path.join(PCB_DIR, "lib", "Espressif.pretty"),
          os.path.join(PCB_DIR, "lib", "strat.pretty")]


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


# ---- explicit placement for major parts (mm; board 42x42, origin at corner)
# x right, y down. Sensors on the bottom go inside the central 16mm window.
PLACE = {
    "U1": (21, 21, 0, "T"),     # P4 center
    "U2": (32.5, 13, 0, "T"),   # flash
    "Y1": (32.5, 18, 0, "T"),   # crystal
    "U3": (21, 6.5, 0, "T"),    # C6-MINI, antenna toward top edge
    "J2": (21, 39.5, 0, "T"),   # USB-C bottom edge
    "U4": (7, 33, 0, "T"),      # TP4056
    "U5": (14, 34, 0, "T"),     # buck
    "L1": (17.5, 34, 0, "T"),
    "J1": (32, 39, 0, "T"),     # battery JST
    "U6": (13.5, 27, 0, "T"),   # IMU
    "U7": (28, 27, 0, "T"),     # baro
    "U8": (21, 24, 0, "B"),     # VL53L1X bottom, in window
    "U9": (21, 18, 0, "B"),     # PMW3901 bottom, in window
    "J3": (10, 18, 0, "B"),     # flow fallback header bottom
    "J4": (21, 2.6, 0, "T"),    # camera FFC front edge
    "LED1": (9, 9, 0, "T"),
    "LED2": (33, 9, 0, "T"),
    "J9": (39, 19, 0, "T"),     # expansion
    "J10": (39, 25, 0, "T"),    # P4 uart
    "J11": (39, 31, 0, "T"),    # c6 uart
    "SW1": (3.5, 21, 0, "T"),
    "SW2": (3.5, 27, 0, "T"),
    # motor FETs + pads at the 4 corners
    "Q1": (35, 9, 0, "T"), "J5": (38.5, 5.5, 0, "T"),
    "Q2": (35, 33, 0, "T"), "J6": (38.5, 36.5, 0, "T"),
    "Q3": (7, 33, 270, "T"), "J7": (3.5, 36.5, 0, "T"),
    "Q4": (9, 13, 0, "T"), "J8": (3.5, 5.5, 0, "T"),
}


def resolve_fp(spec):
    """spec 'lib:name' -> (FOOTPRINT, chosen_path) or (None, reason)."""
    if ":" not in spec:
        return None, f"no lib prefix: {spec}"
    lib, name = spec.split(":", 1)
    cand = []
    if lib == "strat":
        cand += [(d, name) for d in VENDOR]
    cand.append((os.path.join(SYS_FP, lib + ".pretty"), name))
    for d, n in cand:
        try:
            fp = pcbnew.FootprintLoad(d, n)
            if fp:
                return fp, os.path.join(d, n)
        except Exception:
            continue
    return None, spec


def main():
    board = pcbnew.NewBoard(OUT)
    # 4-layer stackup
    board.SetCopperLayerCount(4)
    stk = board.GetDesignSettings()
    stk.SetCopperLayerCount(4)

    nets = {}

    def net(name):
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
            nets[name] = ni
        return nets[name]

    net("GND")
    auto_x, auto_y = 2.0, 14.0  # auto-flow band for unplaced passives
    missing, subs = [], []
    placed = 0

    for comp in design.all_components():
        ref = comp["ref"]
        fp, info = resolve_fp(comp["fp"])
        if not fp:
            for alt in comp["fp_alt"]:
                fp, info = resolve_fp(alt)
                if fp:
                    subs.append(f"{ref}: {comp['fp']} -> {alt}")
                    break
        if not fp:
            missing.append(f"{ref}: {comp['fp']}")
            continue

        fp.SetReference(ref)
        fp.SetValue(comp["value"])
        # placement
        if ref in PLACE:
            x, y, rot, side = PLACE[ref]
        else:
            x, y, rot, side = auto_x, auto_y, 0, comp["side"]
            auto_x += 2.2
            if auto_x > 40:
                auto_x = 2.0
                auto_y += 2.2
        fp.SetPosition(vec(x, y))
        # net assignment per pad (before Add)
        for pad in fp.Pads():
            padname = pad.GetPadName() or pad.GetName()
            if padname in comp["pins"]:
                pad.SetNet(net(comp["pins"][padname]))
        # KiCad 7: footprint must be on the board before Flip; LCSC/DNP are
        # carried in design.py (BOM/CPL generated from there), not as fields.
        board.Add(fp)
        if comp["side"] == "B" or side == "B":
            fp.SetLayerAndFlip(pcbnew.B_Cu)
        if rot:
            fp.SetOrientationDegrees(rot)
        if not comp["populate"]:
            try:
                fp.SetExcludedFromBOM(True)
            except Exception:
                pass
        placed += 1

    draw_outline(board)
    board.Save(OUT)
    print(f"placed {placed}/{len(design.all_components())} components, {len(nets)} nets")
    if subs:
        print("footprint substitutions:")
        for s in subs:
            print("  ", s)
    if missing:
        print("MISSING footprints (not placed — fix before fab):")
        for m in missing:
            print("  ", m)
    print(f"saved {OUT}")
    sys.stdout.flush()
    # pcbnew 7's zone-geometry computation crashes on this board's complex
    # footprints, so inject the copper pours as text (no pcbnew). They are
    # unfilled outlines; KiCad fills them on open.
    inject_zones(OUT)
    print("poured GND/3V3/VBAT/GND planes (In1/In2/B/F, unfilled — fill in KiCad)")
    os._exit(0 if not missing else 2)


def inject_zones(path):
    import re
    import uuid as _uuid
    txt = open(path).read()
    netnum = {name: int(n) for n, name in re.findall(r'\(net (\d+) "([^"]*)"\)', txt)}
    b = design.BOARD
    x0, y0, x1, y1 = 0.3, 0.3, b["w"] - 0.3, b["h"] - 0.3
    plan = [("In1.Cu", "GND"), ("In2.Cu", "3V3"), ("B.Cu", "VBAT"), ("F.Cu", "GND")]
    blocks = []
    for layer, nn in plan:
        if nn not in netnum:
            continue
        blocks.append(f'''  (zone (net {netnum[nn]}) (net_name "{nn}") (layer "{layer}") (tstamp {_uuid.uuid4()}) (hatch edge 0.508)
    (connect_pads (clearance 0.2))
    (min_thickness 0.25) (filled_areas_thickness no)
    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon (pts (xy {x0} {y0}) (xy {x1} {y0}) (xy {x1} {y1}) (xy {x0} {y1})))
  )''')
    # insert before the final top-level ')'
    idx = txt.rstrip().rfind(")")
    out = txt[:idx] + "\n" + "\n".join(blocks) + "\n" + txt[idx:]
    open(path, "w").write(out)


def draw_outline(board):
    b = design.BOARD
    w, h, r = b["w"], b["h"], b["corner_r"]
    edge = pcbnew.Edge_Cuts
    seg = [((r, 0), (w - r, 0)), ((w, r), (w, h - r)),
           ((w - r, h), (r, h)), ((0, h - r), (0, r))]
    for (x1, y1), (x2, y2) in seg:
        ln = pcbnew.PCB_SHAPE(board)
        ln.SetShape(pcbnew.SHAPE_T_SEGMENT)
        ln.SetStart(vec(x1, y1))
        ln.SetEnd(vec(x2, y2))
        ln.SetLayer(edge)
        ln.SetWidth(mm(0.1))
        board.Add(ln)
    for cx, cy, a1 in [(r, r, 180), (w - r, r, 270), (w - r, h - r, 0), (r, h - r, 90)]:
        arc = pcbnew.PCB_SHAPE(board)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        arc.SetCenter(vec(cx, cy))
        # start point at angle a1
        import math
        sx = cx + r * math.cos(math.radians(a1))
        sy = cy + r * math.sin(math.radians(a1))
        arc.SetStart(vec(sx, sy))
        arc.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), True)
        arc.SetLayer(edge)
        arc.SetWidth(mm(0.1))
        board.Add(arc)
    # mounting holes (NPTH M2) at 36mm square pitch, centered
    cx, cy = w / 2, h / 2
    p = b["mount_pitch"] / 2
    for dx in (-p, p):
        for dy in (-p, p):
            h_fp = pcbnew.FOOTPRINT(board)
            pad = pcbnew.PAD(h_fp)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetSize(vec(b["mount_d"], b["mount_d"]))
            pad.SetDrillSize(vec(b["mount_d"], b["mount_d"]))
            pad.SetPosition(vec(cx + dx, cy + dy))
            pad.SetLayerSet(pad.UnplatedHoleMask())
            h_fp.Add(pad)
            h_fp.SetPosition(vec(cx + dx, cy + dy))
            board.Add(h_fp)



if __name__ == "__main__":
    main()
