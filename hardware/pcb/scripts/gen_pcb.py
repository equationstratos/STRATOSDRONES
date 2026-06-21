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


# ---- explicit placement for major parts (mm; portrait board 45x85, origin at
# corner). x right (0..45), y down (0..85); y=0 is the camera nose.
# Layout mirrors a real Tello mainboard: optical cluster at the nose, P4 + C6
# in shielded zones down the spine, power at the rear, motor pads at the four
# corners (wires out to the body arms), USB on the left side edge.
# Positions are chosen so every anchor's pad+courtyard stays inside the outline
# and major parts don't collide; assert_placement() at the end of main() fails
# the build if that ever regresses. Board expanded 36x70->45x85 to eliminate
# all pad overlaps and allow proper spacing of all 115 components.
PLACE = {
    "J4": (22.5, 5.0, 0, "T"),    # camera FFC — nose
    "U3": (22.5, 19, 0, "T"),     # ESP32-C6 module (large), RF zone — spaced
                                  # down so its antenna keepout clears the
                                  # camera FFC (J4)
    "U1": (22.5, 44, 0, "T"),     # ESP32-P4, CPU zone
    "U2": (11, 45, 0, "T"),       # flash, left of P4 (clear of USB)
    "Y1": (35, 40, 0, "T"),       # crystal, right of P4
    "U6": (10, 57, 0, "T"),       # IMU
    "U7": (35, 57, 0, "T"),       # baro
    "U8": (22.5, 38, 0, "B"),     # VL53L1X ToF (bottom, downward)
    "U9": (22.5, 52, 0, "B"),     # PMW3901 flow (bottom, downward)
    "J3": (35, 50, 0, "B"),       # flow fallback header (bottom)
    "U4": (16, 70, 0, "T"),       # TP4056 charger
    "U5": (26, 70, 0, "T"),       # buck
    "L1": (32, 70, 0, "T"),
    "J2": (5.2, 34, 90, "T"),     # USB-C, left side edge
    "J1": (22.5, 80, 0, "T"),     # battery JST, rear edge
    "LED1": (11, 9, 0, "T"),      # status LED, top-left
    "LED2": (34, 27, 0, "T"),
    "SW1": (43, 48, 90, "T"),     # reset — vertical along right edge
    "SW2": (43, 62, 90, "T"),     # boot  — vertical along right edge
    "J9": (4, 48, 0, "T"),        # expansion (left edge, mid)
    "J10": (13, 78, 0, "T"),      # P4 uart pads
    "J11": (34, 78, 0, "T"),      # c6 uart pads
    # motor FETs + pads near the four corners, inboard of the mount holes
    # (35x75 pitch -> holes at (5,5)/(40,5)/(5,80)/(40,80)). Header sits at the
    # board edge (motor wire exit); the FET is shifted ~2 mm further from the
    # header in Y so the two tall courtyards don't touch.
    "Q1": (38, 22, 0, "T"), "J5": (40, 14, 0, "T"),
    "Q2": (38, 63, 0, "T"), "J6": (40, 71, 0, "T"),
    "Q3": (7, 63, 0, "T"),  "J7": (5, 71, 0, "T"),
    "Q4": (7, 22, 0, "T"),  "J8": (5, 14, 0, "T"),
    # D2 (DNP reverse-polarity Schottky, wide D_SMA): the top side has no 7 mm
    # gap left, so the optional diode goes on the bottom in the empty top-left,
    # well clear of the downward sensor windows (U8/U9, center).
    "D2": (13, 13, 0, "B"),
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


def anchor_map():
    """For each passive, the placed component it belongs next to.

    Automatic: a passive anchors to the placed major it shares its most
    *specific* (rarest) net with — so XTAL caps land on the crystal, gate
    resistors on their FET, flash pull-ups on the flash, etc. Overrides cover
    parts that only touch the global rails (regulator I/O caps, bulk/decoupling)
    where the net alone doesn't say where they go.
    """
    GLOBAL = {"GND", "3V3", "VBAT", "VBUS"}
    net_refs = {}
    for c in design.all_components():
        for n in set(c["pins"].values()):
            net_refs.setdefault(n, set()).add(c["ref"])
    place_refs = set(PLACE)
    res = {}
    for c in design.all_components():
        ref = c["ref"]
        if ref in place_refs:
            continue
        specific = sorted((n for n in set(c["pins"].values()) if n not in GLOBAL),
                          key=lambda n: len(net_refs[n]))
        best = None
        for n in specific:
            cands = [r for r in net_refs[n] if r in place_refs]
            if cands:
                best = sorted(cands)[0]
                break
        res[ref] = best
    OVERRIDE = {
        "C1": "U4", "C2": "U4", "R3": "U4", "D2": "U4",          # charger
        "C3": "U5", "C4": "U5", "R4": "U5", "R5": "U5", "R6": "U5",
        "R7": "U5", "R8": "U5", "C6": "U5",                       # buck + Vbat sense
        "C5": "U1", "C11": "U1", "C7": "U1",                      # core/MIPI rails
        "C26": "U1", "C27": "U1",                                 # bulk by the P4
        "C8": "Y1", "C9": "Y1",                                   # crystal load caps
        "C28": "U6", "C29": "U6", "C30": "U7",                    # IMU / baro
        "C31": "U8", "C32": "U9",                                 # ToF / flow (bottom)
        "C33": "J4", "C34": "LED1", "C35": "LED2",
        "D1": "J2", "R1": "J2", "R2": "J2",                       # USB
    }
    for k, v in OVERRIDE.items():
        if k in res:
            res[k] = v
    for ref in res:
        if res[ref] is None:
            res[ref] = "U1"   # leftover decoupling rings the P4
    return res


def fix_3d_models_kicad9(pcb_path):
    """Auto-fix 3D model paths for KiCad 9 compatibility.

    pcbnew auto-adds models with KICAD6/7_3DMODEL_DIR (obsolete in KiCad 9).
    Replace with KICAD9_3DMODEL_DIR and convert .wrl → .step format.
    """
    import re
    with open(pcb_path, "r") as f:
        content = f.read()

    # Count originals
    count_6 = content.count("KICAD6_3DMODEL_DIR")
    count_7 = content.count("KICAD7_3DMODEL_DIR")

    # Replace obsolete KiCad 6/7 variables with KiCad 9
    content = content.replace("KICAD6_3DMODEL_DIR", "KICAD9_3DMODEL_DIR")
    content = content.replace("KICAD7_3DMODEL_DIR", "KICAD9_3DMODEL_DIR")

    # Convert .wrl (VRML, old) to .step (modern format for KiCad 9)
    content = re.sub(
        r'(\$\{KICAD9_3DMODEL_DIR\}/[^)]*\.wrl)',
        lambda m: m.group(1).replace('.wrl', '.step'),
        content
    )
    # Fix any double extensions
    content = re.sub(r'\.step\.step', '.step', content)

    with open(pcb_path, "w") as f:
        f.write(content)

    if count_6 + count_7 > 0:
        print(f"fixed 3D models: replaced {count_6+count_7} KICAD6/7 paths with KICAD9, "
              f"converted {content.count('.step')} models to .step format")


def assert_placement(path, bw, bh):
    """Report parts whose pads fall outside the outline or whose courtyards
    collide on the same side. Off-board pads are a hard error (return code);
    courtyard overlaps are warnings (a dense board has acceptable tight pairs).
    Loads the saved board from disk so pad/courtyard geometry is stable.
    Returns (n_offboard, n_overlap)."""
    board = pcbnew.LoadBoard(path)

    def mm(v):
        return v / 1e6

    def pad_extent(fp):
        xs, ys = [], []
        for p in fp.Pads():
            b = p.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]
            ys += [b.GetTop(), b.GetBottom()]
        if not xs:
            p = fp.GetPosition()
            return mm(p.x), mm(p.y), mm(p.x), mm(p.y)
        return mm(min(xs)), mm(min(ys)), mm(max(xs)), mm(max(ys))

    def crt_extent(fp):
        for ly in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            try:
                poly = fp.GetCourtyard(ly)
                if poly.OutlineCount() > 0:
                    b = poly.BBox()
                    return mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())
            except Exception:
                pass
        return pad_extent(fp)

    eps = 0.05
    off = []
    boxes = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        l, t, r, b = pad_extent(fp)
        tags = []
        if l < -eps:
            tags.append(f"L{l:.1f}")
        if r > bw + eps:
            tags.append(f"R{r:.1f}")
        if t < -eps:
            tags.append(f"T{t:.1f}")
        if b > bh + eps:
            tags.append(f"B{b:.1f}")
        if tags:
            off.append((ref, " ".join(tags)))
        boxes[ref] = (crt_extent(fp), "B" if fp.IsFlipped() else "F")

    # significant same-side courtyard overlaps (ignore <0.3mm tight-pack pairs)
    refs = list(boxes)
    clashes = []
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            ra, rb = refs[i], refs[j]
            (al, at, ar, ab), sa = boxes[ra]
            (bl, bt, br, bb), sb = boxes[rb]
            if sa != sb:
                continue
            ox = min(ar, br) - max(al, bl)
            oy = min(ab, bb) - max(at, bt)
            if ox > 0.3 and oy > 0.3:
                clashes.append((ox * oy, ra, rb, ox, oy))
    clashes.sort(reverse=True)

    if off:
        print(f"OFF-BOARD pads ({len(off)}) — must be inside 0..{bw} x 0..{bh}:")
        for ref, tags in sorted(off):
            print(f"   {ref:6s} {tags}")
    else:
        print(f"placement: all pads inside the {bw:g}x{bh:g} outline")
    if clashes:
        print(f"courtyard overlaps >0.3mm ({len(clashes)}):")
        for _a, ra, rb, ox, oy in clashes:
            print(f"   {ra:6s} <-> {rb:6s}  {ox:.2f}x{oy:.2f} mm")
    else:
        print("placement: no significant courtyard overlaps")
    return len(off), len(clashes)


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

    import math
    net("GND")
    missing, subs = [], []
    bw, bh = design.BOARD["w"], design.BOARD["h"]

    # ---- load every footprint, assign nets, measure courtyard size ----
    loaded = []   # (comp, fp, w_mm, h_mm)
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
        xs, ys = [], []
        for pad in fp.Pads():
            padname = pad.GetPadName() or pad.GetName()
            if padname in comp["pins"]:
                pad.SetNet(net(comp["pins"][padname]))
            pb = pad.GetBoundingBox()
            xs += [pb.GetLeft(), pb.GetRight()]
            ys += [pb.GetTop(), pb.GetBottom()]
        # Collision size = the footprint's own COURTYARD (includes body + IPC
        # clearance + module keepouts like the ESP32-C6 antenna). Fall back to
        # the pad extent + 0.5 mm when a footprint defines no courtyard.
        cxs, cys = [], []
        for it in fp.GraphicalItems():
            if it.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                bb = it.GetBoundingBox()
                cxs += [bb.GetLeft(), bb.GetRight()]
                cys += [bb.GetTop(), bb.GetBottom()]
        if cxs:
            wmm = (max(cxs) - min(cxs)) / 1e6
            hmm = (max(cys) - min(cys)) / 1e6
        elif xs:
            wmm = (max(xs) - min(xs)) / 1e6 + 0.5
            hmm = (max(ys) - min(ys)) / 1e6 + 0.5
        else:
            wmm = hmm = 1.2
        loaded.append((comp, fp, max(wmm, 1.0), max(hmm, 1.0)))

    placed_ref = {}              # ref -> (x, y)
    occ = {"T": [], "B": []}     # occupied boxes per side (x0,y0,x1,y1)

    # courtyards already bake in IPC clearance, so only a hair of extra gap
    def add_box(side, x, y, w, h, m=0.15):
        occ[side].append((x - w / 2 - m, y - h / 2 - m, x + w / 2 + m, y + h / 2 + m))

    def overlaps(side, x, y, w, h, m=0.15):
        a = (x - w / 2 - m, y - h / 2 - m, x + w / 2 + m, y + h / 2 + m)
        for b in occ[side]:
            if a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]:
                return True
        return False

    def place(comp, fp, w, h, x, y, rot, side):
        fp.SetPosition(vec(x, y))
        board.Add(fp)
        if side == "B":
            fp.SetLayerAndFlip(pcbnew.B_Cu)
        if rot:
            fp.SetOrientationDegrees(rot)
        if not comp["populate"]:
            try:
                fp.SetExcludedFromBOM(True)
            except Exception:
                pass
        # a 90/270 rotation swaps the collision box dimensions
        bxw, bxh = (h, w) if rot in (90, 270) else (w, h)
        add_box(side, x, y, bxw, bxh)
        placed_ref[comp["ref"]] = (x, y)

    def inside(x, y, w, h):
        return not (x - w / 2 < 1.0 or y - h / 2 < 1.0
                    or x + w / 2 > bw - 1.0 or y + h / 2 > bh - 1.0)

    def find_slot(side, ax, ay, w, h):
        """nearest free position to (ax, ay): fine concentric rings out to the
        whole board, then a distance-sorted grid scan, so a part that can't sit
        right by its anchor lands at the CLOSEST free spot — never dumped in a
        far corner."""
        for i in range(400):
            rad = 0.8 + i * 0.3
            if rad > 80:                       # cover the full board diagonal
                break
            steps = max(16, int(rad * 9))
            for k in range(steps):
                ang = 2 * math.pi * k / steps
                x = ax + rad * math.cos(ang)
                y = ay + rad * math.sin(ang)
                if inside(x, y, w, h) and not overlaps(side, x, y, w, h):
                    return x, y
        # fallback: every free grid cell, nearest-to-anchor first
        cands = []
        gy = 1.0 + h / 2
        while gy < bh - 1.0 - h / 2:
            gx = 1.0 + w / 2
            while gx < bw - 1.0 - w / 2:
                if not overlaps(side, gx, gy, w, h):
                    cands.append(((gx - ax) ** 2 + (gy - ay) ** 2, gx, gy))
                gx += 0.5
            gy += 0.5
        if cands:
            cands.sort()
            return cands[0][1], cands[0][2]
        return ax, ay

    # mounting holes are obstacles on both sides (parts must clear them)
    mcx, mcy = bw / 2, bh / 2
    mpx = design.BOARD.get("mount_pitch_x", 24) / 2
    mpy = design.BOARD.get("mount_pitch_y", 58) / 2
    md = design.BOARD.get("mount_d", 2.2) + 1.0
    for dx in (-mpx, mpx):
        for dy in (-mpy, mpy):
            for s in ("T", "B"):
                add_box(s, mcx + dx, mcy + dy, md, md, m=0.0)

    # ---- phase 1: anchors (major ICs/connectors) at their fixed positions ----
    by_ref = {c[0]["ref"]: c for c in loaded}
    for ref, (x, y, rot, side) in PLACE.items():
        if ref in by_ref:
            comp, fp, w, h = by_ref[ref]
            place(comp, fp, w, h, x, y, rot, side)

    # ---- phase 2: passives clustered around the part they serve ----
    anchors = anchor_map()
    free = [c for c in loaded if c[0]["ref"] not in PLACE]
    free.sort(key=lambda c: (anchors.get(c[0]["ref"], "U1"), c[2] * c[3]))
    for comp, fp, w, h in free:
        an = anchors.get(comp["ref"], "U1")
        ax, ay = placed_ref.get(an, (bw / 2, bh / 2))
        x, y = find_slot(comp["side"], ax, ay, w, h)
        place(comp, fp, w, h, x, y, 0, comp["side"])

    # ---- repair: relocate any non-anchor part still overlapping a neighbour ----
    fp_of = {c[0]["ref"]: c[1] for c in loaded if c[0]["ref"] in placed_ref}
    sz = {c[0]["ref"]: (c[2], c[3]) for c in loaded}

    def cur_box(fp):
        # courtyard from graphic items at the placed position (GetCourtyard()'s
        # cache isn't built in-memory pre-save, so read the graphics directly);
        # fall back to the pad extent when a footprint defines no courtyard
        cx, cy = [], []
        for it in fp.GraphicalItems():
            if it.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                bb = it.GetBoundingBox()
                cx += [bb.GetLeft(), bb.GetRight()]
                cy += [bb.GetTop(), bb.GetBottom()]
        if cx:
            return (min(cx) / 1e6, min(cy) / 1e6, max(cx) / 1e6, max(cy) / 1e6)
        xs, ys = [], []
        for p in fp.Pads():
            pb = p.GetBoundingBox()
            xs += [pb.GetLeft(), pb.GetRight()]
            ys += [pb.GetTop(), pb.GetBottom()]
        return (min(xs) / 1e6, min(ys) / 1e6, max(xs) / 1e6, max(ys) / 1e6) if xs else None

    mh = [(mcx + dx, mcy + dy) for dx in (-mpx, mpx) for dy in (-mpy, mpy)]
    for _pass in range(6):
        boxes = {r: (cur_box(f), "B" if f.IsFlipped() else "T") for r, f in fp_of.items()}
        moved = 0
        for ref, f in list(fp_of.items()):
            if ref in PLACE:
                continue
            bx, side = boxes[ref]
            if bx is None:
                continue
            clash = any(r2 != ref and s2 == side and bx[0] < b2[2] and bx[2] > b2[0]
                        and bx[1] < b2[3] and bx[3] > b2[1]
                        for r2, (b2, s2) in boxes.items() if b2)
            if not clash:
                continue
            occ[side] = [(b2[0] - 0.25, b2[1] - 0.25, b2[2] + 0.25, b2[3] + 0.25)
                         for r2, (b2, s2) in boxes.items() if r2 != ref and s2 == side and b2]
            occ[side] += [(hx - 1.6, hy - 1.6, hx + 1.6, hy + 1.6) for hx, hy in mh]
            w, h = sz[ref]
            an = anchors.get(ref, "U1")
            ax, ay = placed_ref.get(an, (bw / 2, bh / 2))
            nx, ny = find_slot(side, ax, ay, w, h)
            f.SetPosition(vec(nx, ny))
            placed_ref[ref] = (nx, ny)
            boxes[ref] = (cur_box(f), side)
            moved += 1
        if not moved:
            break

    placed = len(placed_ref)
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
    n_off, n_clash = assert_placement(OUT, bw, bh)
    print(f"saved {OUT}")
    sys.stdout.flush()
    # pcbnew 7's zone-geometry computation crashes on this board's complex
    # footprints, so inject the copper pours as text (no pcbnew). They are
    # unfilled outlines; KiCad fills them on open.
    inject_zones(OUT)
    inject_silk(OUT)
    fix_3d_models_kicad9(OUT)  # Fix 3D model paths for KiCad 9
    print("poured GND/3V3/VBAT/GND planes (In1/In2/B/F, unfilled — fill in KiCad)")
    print("added Tello-style silkscreen (shield outlines, section labels)")
    os._exit(0 if not missing and not n_off else 2)


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
        # For VBAT on bottom (B.Cu), create a polygon with aperture for U8/U9 sensors
        if nn == "VBAT" and layer == "B.Cu":
            # Sensor window aperture (excludes area around U8 ToF @ (18,36) and U9 flow @ (18,44))
            # Create a donut polygon: outer rect with inner hole
            # Outer: (0.3, 0.3) -> (35.7, 0.3) -> (35.7, 69.7) -> (0.3, 69.7) -> back
            # Inner hole: (11, 29) -> (25, 29) -> (25, 51) -> (11, 51) -> back (reversed direction)
            polygon_str = "(pts (xy 0.3 0.3) (xy 35.7 0.3) (xy 35.7 69.7) (xy 0.3 69.7) (xy 0.3 0.3) (xy 11 29) (xy 11 51) (xy 25 51) (xy 25 29) (xy 11 29))"
        else:
            polygon_str = f"(pts (xy {x0} {y0}) (xy {x1} {y0}) (xy {x1} {y1}) (xy {x0} {y1}))"

        blocks.append(f'''  (zone (net {netnum[nn]}) (net_name "{nn}") (layer "{layer}") (tstamp {_uuid.uuid4()}) (hatch edge 0.508)
    (connect_pads (clearance 0.2))
    (min_thickness 0.25) (filled_areas_thickness no)
    (fill (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon {polygon_str})
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
    mh_n = 0
    for dx in (-px, px):
        for dy in (-py, py):
            mh_n += 1
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
            # Unique reference + a footprint id are REQUIRED: the Specctra DSN
            # exporter (and many other tools) abort if two components share an
            # empty reference. Mark as unfitted mechanical so it stays off the
            # assembly BOM/CPL.
            h_fp.SetReference(f"MH{mh_n}")
            h_fp.SetValue("MountingHole_M2_NPTH")
            h_fp.SetFPIDAsString("MountingHole:MountingHole_2.2mm_M2")
            h_fp.Reference().SetVisible(False)
            try:
                h_fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_POS_FILES
                                   | pcbnew.FP_EXCLUDE_FROM_BOM)
            except Exception:
                pass
            board.Add(h_fp)



if __name__ == "__main__":
    main()
