#!/usr/bin/env python3
"""Tie every still-unconnected plane-net pad (GND/3V3/VBAT) to its copper
pour with one clearance-checked stitch via + a short tail track.

Most plane pads are already joined by the zone fill's thermal spokes. The
ones KiCad still counts as unconnected are typically through-hole connector
pads whose hole sits in the pour's antipad, or a plane-net pad on a layer
the pour doesn't reach (e.g. a VBAT pad on F.Cu while the VBAT plane is
B.Cu). For each, drop a 0.45/0.25 via at the nearest point that the pour
*actually fills*, and a 0.2 mm track from the pad to that via — every
candidate rejected if it, or its tail, comes within clearance of any
different-net copper, sits in the antenna keepout, or clashes with an
existing hole.

Correctness is checked the honest way: KiCad's own
GetUnconnectedCount(False) before and after a real zone refill.

  python3 scripts/stitch_planes.py            # stitch + refill + save
  python3 scripts/stitch_planes.py --dry-run  # report only
"""
import argparse
import math
from collections import defaultdict

import pcbnew

BRD = __file__.rsplit("/scripts/", 1)[0] + "/stratosdrone.kicad_pcb"
MM = pcbnew.FromMM
CLEAR = MM(0.15)
TRACK_W = MM(0.2)
VIA_D, VIA_DRILL = MM(0.45), MM(0.25)
POUR_LAYER = {"GND": pcbnew.In1_Cu, "3V3": pcbnew.In2_Cu, "VBAT": pcbnew.B_Cu}
F, B = pcbnew.F_Cu, pcbnew.B_Cu
LAYERS = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
EDGE_INSET = MM(0.35)
BOARD_W, BOARD_H = MM(38.0), MM(74.0)


def probe(x, y, w=1000):
    v = pcbnew.VECTOR2I(int(x), int(y))
    return pcbnew.SHAPE_SEGMENT(v, v, w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    b = pcbnew.LoadBoard(BRD)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    before = b.GetConnectivity().GetUnconnectedCount(False)
    print(f"unconnected before: {before}")

    pours = defaultdict(list)
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() in POUR_LAYER:
            pours[z.GetNetname()].append(z)
    keepouts = [z for z in b.Zones() if z.GetIsRuleArea()]
    for fp in b.GetFootprints():
        for z in fp.Zones():
            if z.GetIsRuleArea():
                keepouts.append(z)

    pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
    tracks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]

    grid = defaultdict(list)
    S = MM(2)

    def add_hash(it):
        bb = it.GetBoundingBox()
        for cx in range(bb.GetLeft() // S, bb.GetRight() // S + 1):
            for cy in range(bb.GetTop() // S, bb.GetBottom() // S + 1):
                grid[(cx, cy)].append(it)

    for it in pads + tracks + vias:
        add_hash(it)

    def near(x, y, r):
        out, seen = [], set()
        for cx in range((x - r) // S, (x + r) // S + 1):
            for cy in range((y - r) // S, (y + r) // S + 1):
                for it in grid.get((cx, cy), ()):
                    if id(it) not in seen:
                        seen.add(id(it))
                        out.append(it)
        return out

    def item_on(it, L):
        if isinstance(it, pcbnew.PCB_VIA):
            return True
        if isinstance(it, pcbnew.PAD):
            return it.IsOnLayer(L) or it.GetDrillSizeX() > 0
        return it.GetLayer() == L

    def clear(shape, x, y, netcode, layers, extra=0):
        r = CLEAR + MM(1) + extra
        for it in near(x, y, r):
            if it.GetNetCode() == netcode:
                continue
            for L in layers:
                if not item_on(it, L):
                    continue
                if it.GetEffectiveShape(L).Collide(shape, int(CLEAR)):
                    return False
                break
        return True

    def hole_ok(x, y):
        for it in near(x, y, MM(1)):
            d = it.GetDrillSizeX() if isinstance(it, pcbnew.PAD) else \
                (it.GetDrill() if isinstance(it, pcbnew.PCB_VIA) else 0)
            if d <= 0:
                continue
            c = it.GetPosition()
            if math.hypot(x - c.x, y - c.y) < d / 2 + VIA_DRILL / 2 + MM(0.25):
                return False
        return True

    def in_keepout(shape, via):
        for z in keepouts:
            if via and not z.GetDoNotAllowVias():
                continue
            if not via and not z.GetDoNotAllowTracks():
                continue
            if z.Outline().Collide(shape, int(CLEAR)):
                return True
        return False

    def pour_fill(nm, x, y):
        L = POUR_LAYER[nm]
        pos = pcbnew.VECTOR2I(int(x), int(y))
        return any(z.HitTestFilledArea(L, pos, 0) for z in pours[nm])

    def edge_ok(x, y):
        return EDGE_INSET < x < BOARD_W - EDGE_INSET and \
               EDGE_INSET < y < BOARD_H - EDGE_INSET

    # candidate plane pads: those whose center is NOT on same-net fill of
    # their pour layer (the fill-covered ones are already thermal-tied).
    added = tries = 0
    plan = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            nm = p.GetNetname()
            if nm not in POUR_LAYER:
                continue
            c = p.GetPosition()
            if pour_fill(nm, c.x, c.y):
                continue                      # already covered -> connected
            tries += 1
            net = p.GetNetCode()
            best = None
            # search rings outward for a filled, clear, drillable spot
            for r_mm in (0.45, 0.6, 0.75, 0.9, 1.1, 1.3, 1.6, 2.0):
                r = MM(r_mm)
                for ang in range(0, 360, 20):
                    vx = int(c.x + r * math.cos(math.radians(ang)))
                    vy = int(c.y + r * math.sin(math.radians(ang)))
                    if not edge_ok(vx, vy):
                        continue
                    if not pour_fill(nm, vx, vy):
                        continue
                    if not hole_ok(vx, vy):
                        continue
                    vsh = probe(vx, vy, VIA_D)
                    if in_keepout(vsh, True):
                        continue
                    if not clear(vsh, vx, vy, net, LAYERS):
                        continue
                    tsh = pcbnew.SHAPE_SEGMENT(c, pcbnew.VECTOR2I(vx, vy), TRACK_W)
                    tl = F if p.IsOnLayer(F) else B
                    if in_keepout(tsh, False):
                        continue
                    if not clear(tsh, (c.x + vx) // 2, (c.y + vy) // 2, net,
                                 (tl,), extra=r):
                        continue
                    best = (vx, vy, tl)
                    break
                if best:
                    break
            if best:
                plan.append((p, net, best))
            else:
                print(f"  no spot: {fp.GetReference()}:{p.GetNumber()} "
                      f"({nm}) @({pcbnew.ToMM(c.x):.1f},{pcbnew.ToMM(c.y):.1f})")

    print(f"{tries} candidate pads, {len(plan)} stitchable")
    if args.dry_run:
        return

    for p, net, (vx, vy, tl) in plan:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(vx, vy))
        v.SetWidth(VIA_D)
        v.SetDrill(VIA_DRILL)
        v.SetLayerPair(F, B)
        v.SetNetCode(net)
        b.Add(v)
        add_hash(v)
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(p.GetPosition())
        t.SetEnd(pcbnew.VECTOR2I(vx, vy))
        t.SetWidth(TRACK_W)
        t.SetLayer(tl)
        t.SetNetCode(net)
        b.Add(t)
        add_hash(t)
        added += 1

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    after = b.GetConnectivity().GetUnconnectedCount(False)
    print(f"added {added} stitch via+tail;  unconnected: {before} -> {after}")
    if after <= before:
        pcbnew.SaveBoard(BRD, b)
        print("saved.")
    else:
        print("REGRESSED — not saving.")


if __name__ == "__main__":
    main()
