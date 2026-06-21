#!/usr/bin/env python3
"""Autoroute the STRATOSDRONE board with Freerouting (headless / AI-assisted).

Pipeline
--------
1. Export a Specctra ``.dsn`` from the placed board, with the two OUTER-layer
   copper pours (``F.Cu`` GND, ``B.Cu`` VBAT) temporarily removed so the router
   sees two free signal layers.  The inner planes ``In1.Cu`` (GND) and
   ``In2.Cu`` (3V3) stay, so those nets reach copper through short vias.
2. Run Freerouting under ``xvfb`` (virtual display — avoids the Headless
   exception its telemetry/version-check path throws) to produce a ``.ses``.
3. Import the routed wires + vias from the ``.ses`` back onto the FULL board
   (all four zones intact) with a self-contained parser — no GUI needed.
4. Save.  Zone filling + gerber export is done afterwards by
   ``fill_zones_export.py``.

Freerouting consumes/relocates its input file, so we always route on a throwaway
copy and keep a master DSN.  The jar is located from a short search path; pass
``--jar`` to override, ``--passes N`` to set router effort.

Run:  python3 scripts/route_board.py [--passes 20] [--jar /path/fr.jar]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
BRD = os.path.join(PCB_DIR, "stratosdrone.kicad_pcb")
DSN = os.path.join(PCB_DIR, "stratosdrone.dsn")   # committed handoff artifact
SES = os.path.join(PCB_DIR, "stratosdrone.ses")   # committed routing result
WORK = "/tmp/frrun"

JAR_CANDIDATES = [
    "/tmp/fr-v2.1.0.jar", "/tmp/freerouting-2.1.0.jar",
    "/home/user/freerouting.jar", "/tmp/fr-v1.9.0.jar",
]


def find_jar(override=None):
    if override:
        return override
    for j in JAR_CANDIDATES:
        if os.path.exists(j):
            return j
    raise SystemExit("Freerouting jar not found; pass --jar /path/to/freerouting.jar")


# nets carried by copper planes + zone fill (not the signal autorouter):
# GND -> In1.Cu + F.Cu pour, 3V3 -> In2.Cu plane, VBAT -> B.Cu pour.
# (VBUS / VDD_* have no plane and route normally as signals.)
PLANE_NETS = ("GND", "3V3", "VBAT")


def export_dsn(dst, strip_planes=False):
    """Export Specctra DSN.

    Always drops the F.Cu/B.Cu pours so the router has free signal layers.
    With ``strip_planes`` the big power nets (GND/3V3/VBAT/VBUS) are removed
    from the DSN ``(network ...)`` so Freerouting only routes signals — those
    nets are then carried by the four copper planes + zone fill + stitch vias.
    """
    b = pcbnew.LoadBoard(BRD)
    removed = []
    for z in list(b.Zones()):
        if z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            removed.append((z.GetNetname(), b.GetLayerName(z.GetLayer())))
            b.Remove(z)
    b.BuildConnectivity()
    if not pcbnew.ExportSpecctraDSN(b, dst) or not os.path.exists(dst):
        raise SystemExit("ExportSpecctraDSN failed")
    # KiCad exports every copper layer as (type signal); the inner plane layers
    # must be (type power) or Freerouting wastes effort trying to route signals
    # across the plane-covered inner copper and effectively routes nothing.
    _mark_inner_planes_power(dst, ("In1.Cu", "In2.Cu"))
    if strip_planes:
        _strip_nets_from_dsn(dst, PLANE_NETS)
    print(f"  exported DSN ({os.path.getsize(dst)} B); freed outer pours: {removed}"
          + ("; power nets routed by planes" if strip_planes else ""))
    return dst


def _mark_inner_planes_power(path, layers):
    t = open(path).read()
    for ly in layers:
        t = re.sub(r'(\(layer\s+' + re.escape(ly) + r'\s*\(type\s+)signal',
                   r'\1power', t)
    open(path, "w").write(t)


def _tighten_rules(path, width_um, clear_um):
    """Shrink the DSN track width + clearances to JLCPCB-fine values so the
    dense placement is routable. KiCad's default export (0.2 mm / 0.2 mm) is too
    loose for this board's pitch; 0.13 mm / 0.13 mm is well within JLC spec."""
    t = open(path).read()
    t = re.sub(r'\(width\s+[0-9.]+\)', f'(width {width_um})', t)
    # keep the very small smd_smd clearance; only relax the general ones
    t = re.sub(r'\(clearance\s+[0-9.]+\)', f'(clearance {clear_um})', t)
    t = re.sub(r'\(clearance\s+[0-9.]+\s+\(type default_smd\)\)',
               f'(clearance {clear_um} (type default_smd))', t)
    open(path, "w").write(t)


def _strip_nets_from_dsn(path, nets):
    """Remove whole ``(net NAME ...)`` blocks (and class members) for NAMES
    from the DSN ``network`` so the autorouter ignores them."""
    src = open(path).read()
    out, i, n = [], 0, len(src)
    while i < n:
        m = src.find("(net ", i)
        if m < 0:
            out.append(src[i:]); break
        # net name token
        j = m + 5
        while src[j] in " \t":
            j += 1
        k = j
        while src[k] not in " \t\n(":
            k += 1
        name = src[j:k]
        if name in nets:
            # skip this balanced (net ...) block
            depth, p = 0, m
            while p < n:
                if src[p] == "(":
                    depth += 1
                elif src[p] == ")":
                    depth -= 1
                    if depth == 0:
                        p += 1
                        break
                p += 1
            out.append(src[i:m])
            i = p
        else:
            out.append(src[i:k])
            i = k
    open(path, "w").write("".join(out))


# --------------------------------------------------------------------------
# 2. Freerouting under xvfb
# --------------------------------------------------------------------------
def run_freerouting(jar, master_dsn, passes):
    if os.path.isdir(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    # Headless-safe config: telemetry/contact off (its version-check NPEs on a
    # null network reply), analytics disabled, GUI on (gui=false breaks input
    # loading in 2.1.0), dialogs auto-confirm so nothing blocks under xvfb.
    base = "/tmp/freerouting/freerouting.json"
    cfg = json.load(open(base)) if os.path.exists(base) else {
        "profile": {}, "gui": {}, "usage_and_diagnostic_data": {}}
    cfg.setdefault("profile", {}).update(allow_telemetry=False, allow_contact=False)
    cfg.setdefault("gui", {}).update(enabled=True, dialog_confirmation_timeout=3)
    cfg.setdefault("usage_and_diagnostic_data", {}).update(disable_analytics=True)
    cfg.setdefault("router", {}).setdefault("scoring", {}).update(via_costs=12)
    json.dump(cfg, open(os.path.join(WORK, "freerouting.json"), "w"), indent=2)

    in_dsn = os.path.join(WORK, "in.dsn")
    out_ses = os.path.join(WORK, "out.ses")
    shutil.copy(master_dsn, in_dsn)
    cmd = ["xvfb-run", "-a", "java", "-jar", jar,
           "-de", in_dsn, "-do", out_ses, "-mp", str(passes)]
    print(f"  running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=WORK, timeout=1800,
                   stdout=open(os.path.join(WORK, "log.txt"), "w"),
                   stderr=subprocess.STDOUT)
    if not os.path.exists(out_ses) or os.path.getsize(out_ses) == 0:
        raise SystemExit("Freerouting produced no SES — see /tmp/frrun/log.txt")
    shutil.copy(out_ses, SES)
    print(f"  routed SES ({os.path.getsize(SES)} B)")
    return SES


# --------------------------------------------------------------------------
# 3. SES -> board (self-contained parser; no GUI / ImportSpecctraSES needed)
# --------------------------------------------------------------------------
def _tokens(text):
    return re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)


def _parse(tokens):
    """S-expression -> nested lists."""
    stack = [[]]
    for t in tokens:
        if t == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif t == ")":
            stack.pop()
        else:
            stack[-1].append(t.strip('"') if t.startswith('"') else t)
    return stack[0]


def _find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def import_ses(ses_path):
    b = pcbnew.LoadBoard(BRD)
    tree = _parse(_tokens(open(ses_path).read()))
    session = tree[0]
    routes = _find(session, "routes")
    if not routes:
        raise SystemExit("SES has no (routes ...) block")
    routes = routes[0]
    # SES coordinates are in (unit / divisor): KiCad/Freerouting emit
    # "(resolution um 10)" -> 1 unit = 0.1 um = 100 nm. Verified empirically:
    # board C26 @ (18.701, 50.382) mm <-> SES (187013, -503816); wire width
    # 1300 = 0.13 mm. Specctra Y is inverted vs KiCad, so negate Y.
    res = _find(routes, "resolution")
    unit = res[0][1] if res else "um"
    div = float(res[0][2]) if res and len(res[0]) > 2 else 1.0
    per = {"um": 1000.0, "mm": 1_000_000.0, "inch": 25_400_000.0}[unit] / div  # nm/unit

    def nmx(v):
        return int(round(float(v) * per))

    def nmy(v):                     # Specctra Y is inverted vs KiCad
        return int(round(-float(v) * per))

    netout = _find(routes, "network_out")
    if not netout:
        raise SystemExit("SES has no (network_out ...) — nothing routed")
    netout = netout[0]

    # layer-name -> id map for every copper layer on the board
    lmap = {}
    for lid in range(pcbnew.PCB_LAYER_ID_COUNT):
        if pcbnew.IsCopperLayer(lid):
            try:
                lmap[b.GetLayerName(lid)] = lid
            except AttributeError:
                pass
            lmap[pcbnew.BOARD.GetStandardLayerName(lid)] = lid

    nseg = nvia = 0
    for net in _find(netout, "net"):
        name = net[1]
        ni = b.FindNet(name)
        if ni is None:
            print(f"  WARN net {name!r} not on board, skipping")
            continue
        code = ni.GetNetCode()
        # wires
        for wire in _find(net, "wire"):
            for path in _find(wire, "path"):
                lname = path[1]
                lid = lmap.get(lname)
                if lid is None:
                    continue
                width = nmx(path[2])
                coords = path[3:]
                pts = [(nmx(coords[i]), nmy(coords[i + 1]))
                       for i in range(0, len(coords) - 1, 2)]
                for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                    t = pcbnew.PCB_TRACK(b)
                    t.SetStart(pcbnew.VECTOR2I(x1, y1))
                    t.SetEnd(pcbnew.VECTOR2I(x2, y2))
                    t.SetWidth(width)
                    t.SetLayer(lid)
                    t.SetNetCode(code)
                    b.Add(t)
                    nseg += 1
        # vias
        for via in _find(net, "via"):
            # (via "Padstack_name" X Y)  — name encodes size; X Y follow
            nums = [tok for tok in via[1:] if re.match(r'^-?\d', str(tok))]
            if len(nums) >= 2:
                x, y = nmx(nums[-2]), nmy(nums[-1])
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(x, y))
                v.SetWidth(pcbnew.FromMM(0.45))
                v.SetDrill(pcbnew.FromMM(0.25))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNetCode(code)
                b.Add(v)
                nvia += 1
    b.BuildConnectivity()
    pcbnew.SaveBoard(BRD, b)
    print(f"  imported {nseg} track segments + {nvia} vias onto board")
    return nseg, nvia


# --------------------------------------------------------------------------
# 4. Connect the plane nets (GND/3V3/VBAT) to their copper planes
# --------------------------------------------------------------------------
# Which layer each plane net's *outer* pour lives on; a pad already on that
# layer connects to the pour directly (no via).  3V3 has only the inner In2
# plane, so every 3V3 pad needs a stitch via.
OUTER_POUR_LAYER = {"GND": pcbnew.F_Cu, "VBAT": pcbnew.B_Cu}


def connect_power():
    """Stitch only the plane-net pads that actually need a cross-layer link, and
    only where a via won't violate clearance.

    A pad whose net already has a copper pour on the pad's own layer is connected
    by the zone fill (thermal spokes) — no via. So GND pads on F.Cu (F.Cu carries
    the GND pour) are left alone; only 3V3 pads (plane on In2), VBAT pads not on
    B.Cu, and GND pads not on F.Cu/In1 get a stitch via — and each candidate via
    is dropped if any different-net pad/track/via sits within clearance, so we
    never manufacture the DRC errors the old blanket-stitch produced."""
    b = pcbnew.LoadBoard(BRD)
    # layers that already carry each plane net's copper (In1=GND, In2=3V3)
    POUR = {
        "GND": {pcbnew.F_Cu, pcbnew.In1_Cu},
        "3V3": {pcbnew.In2_Cu},
        "VBAT": {pcbnew.B_Cu},
    }
    cu = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
    via_w = pcbnew.FromMM(0.4)
    reach = via_w / 2 + pcbnew.FromMM(0.25)       # via centre -> other-copper edge
                                                  # (0.25 mm > JLCPCB min, headroom)

    pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
    tracks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    vias = [v for v in b.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]

    def rect_dist(px, py, bb):
        dx = max(bb.GetLeft() - px, 0, px - bb.GetRight())
        dy = max(bb.GetTop() - py, 0, py - bb.GetBottom())
        return (dx * dx + dy * dy) ** 0.5

    def seg_dist(px, py, a, bpt):
        ax, ay, bx, by = a.x, a.y, bpt.x, bpt.y
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
        cx, cy = ax + t * dx, ay + t * dy
        return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5

    def clear_at(pos, netcode):
        for p in pads:
            if p.GetNetCode() == netcode:
                continue
            if rect_dist(pos.x, pos.y, p.GetBoundingBox()) < reach:
                return False
        for t in tracks:
            if t.GetNetCode() == netcode:
                continue
            if seg_dist(pos.x, pos.y, t.GetStart(), t.GetEnd()) - t.GetWidth() / 2 < reach:
                return False
        for v in vias:
            if v.GetNetCode() == netcode:
                continue
            vp = v.GetPosition()
            if ((pos.x - vp.x) ** 2 + (pos.y - vp.y) ** 2) ** 0.5 - v.GetWidth() / 2 < reach:
                return False
        return True

    added = skipped = nonet = 0
    for fp in b.GetFootprints():
        for p in fp.Pads():
            net = p.GetNetname()
            if net not in POUR:
                continue
            on = {l for l in cu if p.IsOnLayer(l)}
            if on & POUR[net]:
                continue                        # zone fill already connects it
            pos = p.GetPosition()
            if not clear_at(pos, p.GetNetCode()):
                skipped += 1
                continue
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pos)
            v.SetWidth(via_w)
            v.SetDrill(pcbnew.FromMM(0.2))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNetCode(p.GetNetCode())
            b.Add(v)
            vias.append(v)                      # so the next via clears this one
            added += 1
    b.BuildConnectivity()
    pcbnew.SaveBoard(BRD, b)
    print(f"  added {added} clearance-checked stitch vias "
          f"({skipped} skipped as too tight; zone fill handles same-layer pads)")
    return added


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=20)
    ap.add_argument("--jar", default=None)
    ap.add_argument("--skip-route", action="store_true",
                    help="reuse existing stratosdrone.ses, just import")
    ap.add_argument("--strip-planes", action="store_true",
                    help="route signals only; carry GND/3V3/VBAT on planes+stitch vias")
    args = ap.parse_args()

    print("== STRATOSDRONE autorouter ==")
    if not args.skip_route:
        jar = find_jar(args.jar)
        print(f"[1/4] export DSN  (jar: {jar})")
        # Full board: the router routes signals on the freed F.Cu/B.Cu and
        # connects GND/3V3 pads to the inner planes via vias. Outer pours are
        # dropped for routing and re-filled around the traces afterwards.
        export_dsn(DSN, strip_planes=args.strip_planes)
        print(f"[2/4] Freerouting ({args.passes} passes)")
        run_freerouting(jar, DSN, args.passes)
    else:
        print("[1-2/4] skipped (reusing existing SES)")
    print("[3/4] import routed tracks -> board")
    nseg, nvia = import_ses(SES)
    if nseg == 0:
        raise SystemExit("no tracks imported — routing likely failed")
    print("[4/4] stitch any power pads the router left unconnected")
    nstitch = connect_power()
    print(f"DONE: {nseg} segments, {nvia} vias imported, {nstitch} power stitch vias.")
    print("Next: python3 scripts/fill_zones_export.py  (fill zones + gerbers)")


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
