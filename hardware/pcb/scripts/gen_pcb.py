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


# ---- explicit placement for major parts (mm; narrow portrait board 32x66,
# origin at corner). x right (0..32), y down (0..66); y=0 is the camera nose.
# Layout mirrors a real Tello mainboard: optical cluster at the nose, P4 + C6
# in shielded zones down the spine, power at the rear, motor pads at the four
# corners (wires out to the body arms), USB on the left side edge.
PLACE = {
    "J4": (16, 5, 0, "T"),       # camera FFC — nose
    "U3": (16, 14, 0, "T"),      # ESP32-C6 module, antenna toward the nose edge
    "U1": (16, 30, 0, "T"),      # ESP32-P4, spine centre (under CPU shield)
    "U2": (10, 24, 0, "T"),      # flash
    "Y1": (22, 24, 0, "T"),      # crystal
    "U6": (11, 37, 0, "T"),      # IMU
    "U7": (22, 37, 0, "T"),      # baro
    "U8": (16, 35, 0, "B"),      # VL53L1X ToF (bottom, downward)
    "U9": (16, 42, 0, "B"),      # PMW3901 flow (bottom, downward)
    "J3": (24, 44, 0, "B"),      # flow fallback header (bottom)
    "U4": (9, 50, 0, "T"),       # TP4056 charger
    "U5": (20, 50, 0, "T"),      # buck
    "L1": (24, 52, 0, "T"),
    "J2": (3.5, 24, 90, "T"),    # USB-C, left side edge (like Tello micro-USB)
    "J1": (16, 62, 0, "T"),      # battery JST, rear edge
    "LED1": (6, 16, 0, "T"),
    "LED2": (26, 16, 0, "T"),
    "SW1": (27, 30, 0, "T"),     # reset
    "SW2": (27, 36, 0, "T"),     # boot
    "J9": (5, 44, 0, "T"),       # expansion
    "J10": (10, 60, 0, "T"),     # P4 uart pads
    "J11": (22, 60, 0, "T"),     # c6 uart pads
    # motor FETs + pads at the four corners (wire out to the body arms)
    "Q1": (27, 10, 0, "T"), "J5": (28, 5, 0, "T"),
    "Q2": (27, 56, 0, "T"), "J6": (28, 61, 0, "T"),
    "Q3": (5, 56, 0, "T"),  "J7": (4, 61, 0, "T"),
    "Q4": (5, 10, 0, "T"),  "J8": (4, 5, 0, "T"),
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
    # auto-flow unplaced passives into the rear region so the MCU/sensor spine
    # stays readable (final placement is a manual step — see KNOWN_GAPS).
    auto_x, auto_y = 2.5, 45.0
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
            if auto_x > 29.5:
                auto_x = 2.5
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
    inject_silk(OUT)
    print("poured GND/3V3/VBAT/GND planes (In1/In2/B/F, unfilled — fill in KiCad)")
    print("added Tello-style silkscreen (shield outlines, section labels)")
    os._exit(0 if not missing else 2)


def inject_silk(path):
    """Cosmetic Tello-mainboard silkscreen: shield-can outlines, section
    labels, motor +/- marks, a front arrow and the board name. Text-injected
    (no pcbnew) to stay crash-free. Purely on F.SilkS/B.SilkS."""
    import uuid as _uuid
    txt = open(path).read()
    b = design.BOARD
    w = b["w"]
    items = []

    def rect(x0, y0, x1, y1, layer="F.SilkS", wdt=0.15):
        for (xa, ya, xb, yb) in [(x0, y0, x1, y0), (x1, y0, x1, y1),
                                 (x1, y1, x0, y1), (x0, y1, x0, y0)]:
            items.append(
                f'  (gr_line (start {xa} {ya}) (end {xb} {yb}) '
                f'(stroke (width {wdt}) (type solid)) (layer "{layer}") (tstamp {_uuid.uuid4()}))')

    def text(s, x, y, size=1.2, layer="F.SilkS", rot=0, mirror=False):
        j = " (justify mirror)" if mirror else ""
        items.append(
            f'  (gr_text "{s}" (at {x} {y} {rot}) (layer "{layer}") (tstamp {_uuid.uuid4()})\n'
            f'    (effects (font (size {size} {size}) (thickness {size*0.15:.2f}))'
            f' (justify left bottom{("" if not mirror else " mirror")})))')

    # shield-can outlines down the spine (camera / RF / CPU), like the Tello
    rect(2.5, 2.0, w - 2.5, 9.5)     # optical / camera section
    rect(3.0, 10.5, w - 3.0, 20.0)   # RF (ESP32-C6) shield
    rect(2.5, 21.5, w - 2.5, 40.0)   # CPU (ESP32-P4 + sensors) shield
    # labels
    text("STRATOSDRONE", 4.5, 1.6, 1.4)
    text("CAM", 13.0, 8.8, 1.0)
    text("RF", 14.0, 19.2, 1.0)
    text("CPU", 13.5, 39.2, 1.0)
    text("FRONT ^", 11.0, 4.2, 1.0)
    # motor pad polarity marks near the four corners
    for (x, y, lbl) in [(28, 3, "M1"), (28, 63.5, "M2"), (4, 63.5, "M3"), (4, 3, "M4")]:
        text(lbl, x - 3.0, y, 0.9)
    # bottom-side: sensor window label
    text("FLOW + ToF", 9.0, 39.0, 1.0, layer="B.SilkS", mirror=True)

    idx = txt.rstrip().rfind(")")
    out = txt[:idx] + "\n" + "\n".join(items) + "\n" + txt[idx:]
    open(path, "w").write(out)


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
    # mounting holes (NPTH M2) at the rectangular pitch, centered
    cx, cy = w / 2, h / 2
    px = b.get("mount_pitch_x", b.get("mount_pitch", 36.0)) / 2
    py = b.get("mount_pitch_y", b.get("mount_pitch", 36.0)) / 2
    for dx in (-px, px):
        for dy in (-py, py):
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
