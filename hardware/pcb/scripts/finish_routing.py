#!/usr/bin/env python3
"""Best-effort completion of the remaining ratsnest of stratosdrone.kicad_pcb.

A clearance-correct greedy grid router, kept as analysis + tooling. It runs
two passes, both checked against every other-net copper item:

1. Plane stitching — GND / 3V3 / VBAT islands are tied to their pour with a
   0.45/0.25 via + short tail where the pour's *actual fill* covers the via.

2. Grid A* — 0.1 mm grid on F.Cu/B.Cu (signals stay on the outer pair; the
   inner layers are solid planes and must not be slotted). Obstacles are
   every other-net pad/track/via inflated by clearance + half-track; the
   ESP32-C6 antenna rule-area and the board edge (0.35 mm inset, r=6
   corners) are hard-blocked. Two rule tiers (0.15, then JLC-fine 0.127).
   Sensitive nets (differential MIPI/USB, the crystal — see EXCLUDE) are
   deliberately left for controlled hand-routing. Every emitted segment/via
   is re-verified against the *exact* SHAPE::Collide before being added.

FINDING (verified in-sandbox, see hardware/pcb/ROUTING.md): on THIS board
this router closes almost nothing new, and the reason is not a bug. The
plane pads are already thermal-tied by the fill (stitching them changes the
unconnected count by 0), and the ~106 signal links that remain each have at
least one endpoint pad *boxed in* by the neighbouring pins' already-routed
escape tracks (measured: the destination cell has zero free neighbours).
Connecting them requires ripping up and re-routing those neighbours —
shove/push-and-shove routing, which a one-net-at-a-time greedy A* cannot do.
That needs KiCad's interactive router (hand-routing) or Freerouting on a
real desktop display (headless Freerouting is separately broken here). This
script is the reusable clearance-checker / island analyser for that work,
not a finisher for this particular layout.

Run:  python3 scripts/finish_routing.py            # route + save + report
      python3 scripts/finish_routing.py --dry-run  # report only, no save
"""
import argparse
import heapq
import math
import sys
from collections import defaultdict

import pcbnew

BRD = pcbnew.__file__ and __file__.rsplit("/scripts/", 1)[0] + "/stratosdrone.kicad_pcb"

MM = pcbnew.FromMM
G = MM(0.1)                      # grid pitch
# Routing tiers: try comfortable rules first, then JLCPCB-standard fine
# rules (0.127 mm track/clearance = 5 mil) for the links that stay stuck.
TIERS = [
    {"name": "0.15/0.15", "clear": MM(0.15), "track": MM(0.15)},
    {"name": "0.127/0.127", "clear": MM(0.127), "track": MM(0.127)},
]
CLEAR = TIERS[0]["clear"]        # updated per tier in main()
TRACK_W = TIERS[0]["track"]
VIA_D, VIA_DRILL = MM(0.45), MM(0.25)
INFL_TRK = CLEAR + TRACK_W // 2            # obstacle inflation for track routing
INFL_VIA = CLEAR + VIA_D // 2              # obstacle inflation for via spots
EDGE_INSET = MM(0.35)
CORNER_R = MM(6.0)
BOARD_W, BOARD_H = MM(38.0), MM(74.0)
POUR_LAYER = {"GND": pcbnew.In1_Cu, "3V3": pcbnew.In2_Cu, "VBAT": pcbnew.B_Cu}
F, B = pcbnew.F_Cu, pcbnew.B_Cu
IN1, IN2 = pcbnew.In1_Cu, pcbnew.In2_Cu
# Routing layers. The outer pair is preferred; the inner pair is nearly
# empty (plane pours refill around whatever crosses them) and is used as a
# tunnel when the outer fan-out around U1 is saturated — at a step-cost
# penalty so A* only dives when it has to.
LAYERS = (F, B)          # signals stay on the outer pair — never slot a plane
INNER_PENALTY = 1.2
# Nets an impedance-blind grid router must NOT touch (differential MIPI / USB,
# the crystal): leave these for controlled hand-routing.
EXCLUDE = {"CSI_D0N", "CSI_D0P", "CSI_D1N", "CSI_D1P", "CSI_CKN", "CSI_CKP",
           "CSI_REXT", "DSI_REXT", "USB_DP_MCU", "USB_DM_MCU",
           "XTAL_P", "XTAL_N"}

NX = int(BOARD_W // G) + 1       # 381 cols, cell i -> x = i*G
NY = int(BOARD_H // G) + 1       # 741 rows


# ---------------------------------------------------------------- helpers
def cell_of(x, y):
    return int(round(x / G)), int(round(y / G))


def pos_of(i, j):
    return pcbnew.VECTOR2I(i * G, j * G)


def probe(x, y, w=1000):
    """A point, as a collidable shape."""
    v = pcbnew.VECTOR2I(int(x), int(y))
    return pcbnew.SHAPE_SEGMENT(v, v, w)


def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(a, b, w)


class Board:
    def __init__(self, path):
        self.b = pcbnew.LoadBoard(path)
        pcbnew.ZONE_FILLER(self.b).Fill(self.b.Zones())
        self.pads, self.tracks, self.vias, self.pours, self.keepouts = [], [], [], [], []
        for fp in self.b.GetFootprints():
            for p in fp.Pads():
                self.pads.append(p)
            for z in fp.Zones():
                if z.GetIsRuleArea():
                    self.keepouts.append(z)
        for t in self.b.GetTracks():
            (self.vias if isinstance(t, pcbnew.PCB_VIA) else self.tracks).append(t)
        for z in self.b.Zones():
            if z.GetIsRuleArea():
                self.keepouts.append(z)
            elif z.GetNetCode() > 0:
                self.pours.append(z)
        # spatial hash for the exact checker
        self.grid = defaultdict(list)
        for it in self.pads + self.tracks + self.vias:
            self._hash(it)

    def _hash(self, it):
        bb = it.GetBoundingBox()
        s = MM(2)
        for cx in range(bb.GetLeft() // s, bb.GetRight() // s + 1):
            for cy in range(bb.GetTop() // s, bb.GetBottom() // s + 1):
                self.grid[(cx, cy)].append(it)

    def near(self, bb, margin):
        s = MM(2)
        out, seen = [], set()
        for cx in range((bb.GetLeft() - margin) // s, (bb.GetRight() + margin) // s + 1):
            for cy in range((bb.GetTop() - margin) // s, (bb.GetBottom() + margin) // s + 1):
                for it in self.grid.get((cx, cy), ()):
                    if id(it) not in seen:
                        seen.add(id(it))
                        out.append(it)
        return out

    def item_on_layer(self, it, L):
        if isinstance(it, pcbnew.PCB_VIA):
            return True                      # through vias span all coppers
        if isinstance(it, pcbnew.PAD):
            return it.IsOnLayer(L) or it.GetDrillSizeX() > 0
        return it.GetLayer() == L

    def clear_shape(self, shape, bbox, netcode, layers, clearance):
        """True if `shape` keeps `clearance` from every other-net item on
        any of `layers` (exact geometry)."""
        for it in self.near(bbox, clearance + MM(1)):
            if it.GetNetCode() == netcode:
                continue
            for L in layers:
                if not self.item_on_layer(it, L):
                    continue
                s = it.GetEffectiveShape(L)
                if s.Collide(shape, int(clearance)):
                    return False
                break
        return True

    def in_keepout(self, shape, want_via):
        for z in self.keepouts:
            if want_via and not z.GetDoNotAllowVias():
                continue
            if not want_via and not z.GetDoNotAllowTracks():
                continue
            if z.Outline().Collide(shape, int(CLEAR)):
                return True
        return False

    def hole_ok(self, pos):
        """New-via drill must keep distance from EVERY existing hole,
        same-net included — overlapping drills are a fab reject."""
        bb = pcbnew.BOX2I(pcbnew.VECTOR2I(pos.x - MM(1), pos.y - MM(1)),
                          pcbnew.VECTOR2I(MM(2), MM(2)))
        for it in self.near(bb, MM(1)):
            drill = 0
            if isinstance(it, pcbnew.PAD):
                drill = it.GetDrillSizeX()
            elif isinstance(it, pcbnew.PCB_VIA):
                drill = it.GetDrill()
            if drill <= 0:
                continue
            c = it.GetPosition()
            if math.hypot(pos.x - c.x, pos.y - c.y) < \
               drill / 2 + VIA_DRILL / 2 + MM(0.25):
                return False
        return True

    def pour_covers(self, netname, pos, margin=0):
        L = POUR_LAYER[netname]
        for z in self.pours:
            if z.GetNetname() == netname and z.IsOnLayer(L):
                if z.HitTestFilledArea(L, pos, int(margin)):
                    return True
        return False

    def add_track(self, a, b_, layer, netcode):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(a)
        t.SetEnd(b_)
        t.SetWidth(TRACK_W)
        t.SetLayer(layer)
        t.SetNetCode(netcode)
        self.b.Add(t)
        self.tracks.append(t)
        self._hash(t)
        return t

    def add_via(self, pos, netcode):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pos)
        v.SetWidth(VIA_D)
        v.SetDrill(VIA_DRILL)
        v.SetLayerPair(F, B)
        v.SetNetCode(netcode)
        self.b.Add(v)
        self.vias.append(v)
        self._hash(v)
        return v


# ------------------------------------------------------------- union-find
class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def islands(bd):
    """Per net: list of components; each component = list of items."""
    CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
    uf = UF()
    bynet = defaultdict(list)
    for it in bd.pads + bd.tracks + bd.vias + bd.pours:
        if it.GetNetCode() > 0:
            bynet[it.GetNetCode()].append(it)
    for net, its in bynet.items():
        for L in CU:
            onL = [i for i in its if
                   (i in bd.pours and i.IsOnLayer(L)) or
                   (i not in bd.pours and bd.item_on_layer(i, L))]
            zs = [i for i in onL if i in bd.pours]
            rest = [i for i in onL if i not in bd.pours]
            for z in zs:
                for o in rest:
                    if isinstance(o, (pcbnew.PAD, pcbnew.PCB_VIA)):
                        if z.HitTestFilledArea(L, o.GetPosition(), 1000):
                            uf.union(id(z), id(o))
                    elif z.HitTestFilledArea(L, o.GetStart(), 1000) or \
                            z.HitTestFilledArea(L, o.GetEnd(), 1000):
                        uf.union(id(z), id(o))
            cells = defaultdict(list)
            s = MM(2)
            for o in rest:
                bb = o.GetBoundingBox()
                for cx in range(bb.GetLeft() // s, bb.GetRight() // s + 1):
                    for cy in range(bb.GetTop() // s, bb.GetBottom() // s + 1):
                        cells[(cx, cy)].append(o)
            done = set()
            for lst in cells.values():
                for x in range(len(lst)):
                    for y in range(x + 1, len(lst)):
                        a, c = lst[x], lst[y]
                        key = (id(a), id(c))
                        if key in done or uf.find(id(a)) == uf.find(id(c)):
                            continue
                        done.add(key)
                        if a.GetEffectiveShape(L).Collide(c.GetEffectiveShape(L), 1000):
                            uf.union(id(a), id(c))
    out = {}
    for net, its in bynet.items():
        comp = defaultdict(list)
        for i in its:
            comp[uf.find(id(i))].append(i)
        comps = [m for m in comp.values()
                 if any(isinstance(x, pcbnew.PAD) for x in m)]
        if len(comps) > 1:
            out[net] = sorted(comps, key=len, reverse=True)
    return out


# ------------------------------------------------------------ raster maps
FREE, MULTI = -1, -2


def build_maps(bd):
    """occ[layer][j][i]: FREE, a netcode, or MULTI; one map for track
    inflation and a wider one for via placement."""
    def blank():
        return [[FREE] * NX for _ in range(NY)]

    occ = {L: blank() for L in LAYERS}
    occ_via = {L: blank() for L in LAYERS}
    hard = [[False] * NX for _ in range(NY)]      # keepout/edge, blocks all

    def stamp(m, net, x0, y0, x1, y1):
        i0, j0 = max(0, int(math.floor(x0 / G))), max(0, int(math.floor(y0 / G)))
        i1, j1 = min(NX - 1, int(math.ceil(x1 / G))), min(NY - 1, int(math.ceil(y1 / G)))
        for j in range(j0, j1 + 1):
            row = m[j]
            for i in range(i0, i1 + 1):
                cur = row[i]
                if cur == FREE:
                    row[i] = net
                elif cur != net:
                    row[i] = MULTI

    def stamp_item(it, L, m, infl):
        bb = it.GetBoundingBox()
        stamp(m[L], it.GetNetCode(),
              bb.GetLeft() - infl, bb.GetTop() - infl,
              bb.GetRight() + infl, bb.GetBottom() + infl)

    for it in bd.pads + bd.tracks + bd.vias:
        for L in LAYERS:
            if bd.item_on_layer(it, L):
                stamp_item(it, L, occ, INFL_TRK)
                stamp_item(it, L, occ_via, INFL_VIA)

    # board edge + rounded corners
    for j in range(NY):
        y = j * G
        for i in range(NX):
            x = i * G
            if x < EDGE_INSET or x > BOARD_W - EDGE_INSET or \
               y < EDGE_INSET or y > BOARD_H - EDGE_INSET:
                hard[j][i] = True
                continue
            in_x = x < CORNER_R or x > BOARD_W - CORNER_R
            in_y = y < CORNER_R or y > BOARD_H - CORNER_R
            if in_x and in_y:
                cx = CORNER_R if x < CORNER_R else BOARD_W - CORNER_R
                cy = CORNER_R if y < CORNER_R else BOARD_H - CORNER_R
                if math.hypot(x - cx, y - cy) > CORNER_R - EDGE_INSET:
                    hard[j][i] = True
    for z in bd.keepouts:
        bb = z.GetBoundingBox()
        m = CLEAR + TRACK_W // 2
        i0, j0 = max(0, (bb.GetLeft() - m) // G), max(0, (bb.GetTop() - m) // G)
        i1 = min(NX - 1, (bb.GetRight() + m) // G)
        j1 = min(NY - 1, (bb.GetBottom() + m) // G)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                hard[j][i] = True
    return occ, occ_via, hard


def paint_new(occ, occ_via, it, layers):
    bb = it.GetBoundingBox()
    for L in layers:
        for m, infl in ((occ, INFL_TRK), (occ_via, INFL_VIA)):
            i0 = max(0, (bb.GetLeft() - infl) // G)
            j0 = max(0, (bb.GetTop() - infl) // G)
            i1 = min(NX - 1, (bb.GetRight() + infl) // G)
            j1 = min(NY - 1, (bb.GetBottom() + infl) // G)
            for j in range(j0, j1 + 1):
                row = m[L][j]
                for i in range(i0, i1 + 1):
                    cur = row[i]
                    if cur == FREE:
                        row[i] = it.GetNetCode()
                    elif cur != it.GetNetCode():
                        row[i] = MULTI


# ------------------------------------------------------------------- A*
DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.42), (1, -1, 1.42), (-1, 1, 1.42), (-1, -1, 1.42)]
VIA_COST = 14.0


def astar(occ, occ_via, hard, net, sources, targets, walk_extra, max_pop=300_000):
    """sources/targets: sets of (i, j, layer). Returns list of (i, j, layer)."""
    tset = targets
    # heuristic: distance to nearest target (use a few anchor targets)
    anchors = list(tset)[::max(1, len(tset) // 8)]

    def h(i, j):
        return min(abs(i - a) + abs(j - b) for a, b, _ in anchors) * 1.02

    openq = []
    best = {}
    tie = 0
    for s in sources:
        best[s] = 0.0
        tie += 1
        heapq.heappush(openq, (h(s[0], s[1]), tie, 0.0, s, None))
    came = {}
    pops = 0
    while openq:
        f, _, g_, cur, par = heapq.heappop(openq)
        if best.get(cur, 1e18) < g_ - 1e-9:
            continue
        came[cur] = par
        pops += 1
        if pops > max_pop:
            return None
        if cur in tset:
            path = [cur]
            while came[path[-1]] is not None:
                path.append(came[path[-1]])
            return path[::-1]
        i, j, L = cur
        row_occ = occ[L]
        pen = INNER_PENALTY if L in (IN1, IN2) else 1.0
        for di, dj, w in DIRS:
            ni, nj = i + di, j + dj
            if not (0 <= ni < NX and 0 <= nj < NY):
                continue
            nxt = (ni, nj, L)
            ng = g_ + w * pen
            if nxt in best and best[nxt] <= ng:
                continue
            if hard[nj][ni] and nxt not in walk_extra:
                continue
            c = row_occ[nj][ni]
            if c != FREE and c != net and nxt not in walk_extra:
                continue
            best[nxt] = ng
            tie += 1
            heapq.heappush(openq, (ng + h(ni, nj), tie, ng, nxt, cur))
        # layer change — through via reaches every other copper layer at once
        if not hard[j][i]:
            via_ok = all(occ_via[LL][j][i] in (FREE, net) for LL in LAYERS)
            if via_ok:
                for oL in LAYERS:
                    if oL == L:
                        continue
                    nxt = (i, j, oL)
                    ng = g_ + VIA_COST
                    if nxt in best and best[nxt] <= ng:
                        continue
                    best[nxt] = ng
                    tie += 1
                    heapq.heappush(openq, (ng + h(i, j), tie, ng, nxt, cur))
    return None


def simplify(path):
    """Collapse collinear runs; returns [(pos, layer)] plus via positions."""
    pts = [(path[0][0], path[0][1], path[0][2])]
    for k in range(1, len(path)):
        pts.append(path[k])
    segs, vias = [], []
    run = [pts[0]]
    for a, b_ in zip(pts, pts[1:]):
        if a[2] != b_[2]:
            vias.append((a[0], a[1]))
            segs.append(run)
            run = [b_]
            continue
        if len(run) >= 2:
            di1, dj1 = run[-1][0] - run[-2][0], run[-1][1] - run[-2][1]
            di2, dj2 = b_[0] - run[-1][0], b_[1] - run[-1][1]
            if (di1, dj1) == (di2, dj2):
                run[-1] = b_
                continue
        run.append(b_)
    segs.append(run)
    return segs, vias


# ------------------------------------------------------------------ main
def main():
    global CLEAR, TRACK_W, INFL_TRK, INFL_VIA
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bd = Board(BRD)
    bd.b.BuildConnectivity()
    before = bd.b.GetConnectivity().GetUnconnectedCount(False)
    print(f"unconnected before: {before}")

    print("building obstacle maps ...")
    occ, occ_via, hard = build_maps(bd)

    isl = islands(bd)
    names = {n: bd.b.FindNet(n).GetNetname() for n in isl}
    total = sum(len(c) - 1 for c in isl.values())
    print(f"{len(isl)} split nets, {total} links to make")

    made = failed = 0
    fails = []

    # ---- pass 1: plane stitches ------------------------------------
    for net, comps in sorted(isl.items(), key=lambda kv: -len(kv[1])):
        nm = names[net]
        if nm not in POUR_LAYER:
            continue
        main_comp = comps[0]
        kept = []
        for comp in comps[1:]:
            if any(x in bd.pours for x in comp):
                continue                      # already the pour component
            done = False
            cands = []
            for it in comp:
                if isinstance(it, pcbnew.PAD):
                    p0 = it.GetPosition()
                    cands.append(p0)
                    for r in (MM(0.6), MM(1.0), MM(1.4)):
                        for ang in range(0, 360, 45):
                            cands.append(pcbnew.VECTOR2I(
                                int(p0.x + r * math.cos(math.radians(ang))),
                                int(p0.y + r * math.sin(math.radians(ang)))))
            for pos in cands:
                if not bd.pour_covers(nm, pos, VIA_D // 2):
                    continue
                if not bd.hole_ok(pos):
                    continue
                sh = probe(pos.x, pos.y, VIA_D)
                bb = pcbnew.BOX2I(pcbnew.VECTOR2I(pos.x - VIA_D, pos.y - VIA_D),
                                  pcbnew.VECTOR2I(2 * VIA_D, 2 * VIA_D))
                if bd.in_keepout(sh, True):
                    continue
                if not bd.clear_shape(sh, bb, net, (F, B), CLEAR - 100):
                    continue
                # tail track if the via isn't inside a pad of the island
                tail_from = None
                onpad = any(isinstance(x, pcbnew.PAD) and
                            x.GetEffectiveShape(F if x.IsOnLayer(F) else B)
                            .Collide(sh, 0) for x in comp)
                if not onpad:
                    near_pad = min((x for x in comp if isinstance(x, pcbnew.PAD)),
                                   key=lambda p: (p.GetPosition() - pos).EuclideanNorm())
                    LP = F if near_pad.IsOnLayer(F) else B
                    tsh = seg_shape(near_pad.GetPosition(), pos, TRACK_W)
                    tbb = pcbnew.BOX2I(pcbnew.VECTOR2I(min(near_pad.GetPosition().x, pos.x) - TRACK_W,
                                                       min(near_pad.GetPosition().y, pos.y) - TRACK_W),
                                       pcbnew.VECTOR2I(abs(near_pad.GetPosition().x - pos.x) + 2 * TRACK_W,
                                                       abs(near_pad.GetPosition().y - pos.y) + 2 * TRACK_W))
                    if bd.in_keepout(tsh, False) or \
                       not bd.clear_shape(tsh, tbb, net, (LP,), CLEAR - 100):
                        continue
                    tail_from = (near_pad.GetPosition(), LP)
                if not args.dry_run:
                    v = bd.add_via(pos, net)
                    paint_new(occ, occ_via, v, LAYERS)
                    if tail_from:
                        t = bd.add_track(tail_from[0], pos, tail_from[1], net)
                        paint_new(occ, occ_via, t, (tail_from[1],))
                made += 1
                done = True
                break
            if not done:
                kept.append(comp)             # give it an A* chance instead
        isl[net] = [main_comp] + kept

    # ---- pass 2: tiered A* for everything still split ---------------
    def comp_cells(comp):
        cells = set()
        for it in comp:
            if it in bd.pours:
                continue                      # rasterizing a pour = the board
            if isinstance(it, pcbnew.PAD):
                layers = [L for L in LAYERS if bd.item_on_layer(it, L)]
            elif isinstance(it, pcbnew.PCB_VIA):
                layers = list(LAYERS)
            else:
                layers = [it.GetLayer()] if it.GetLayer() in LAYERS else []
            bb = it.GetBoundingBox()
            for L in layers:
                sh = it.GetEffectiveShape(L)
                i0, j0 = max(0, bb.GetLeft() // G), max(0, bb.GetTop() // G)
                i1, j1 = min(NX - 1, bb.GetRight() // G), min(NY - 1, bb.GetBottom() // G)
                for j in range(j0, j1 + 1):
                    for i in range(i0, i1 + 1):
                        if sh.Collide(probe(i * G, j * G), 0):
                            cells.add((i, j, L))
        return cells

    def hop_len(net):
        comps = isl[net]
        a = comps[0][0].GetPosition() if comps[0] else None
        best = 0
        for c in comps[1:]:
            for x in c:
                if isinstance(x, pcbnew.PAD):
                    best = max(best, (x.GetPosition() - a).EuclideanNorm())
                    break
        return best

    def try_net(net, nm):
        """Route until this net is one island. Returns (#links, fail_reason)."""
        nonlocal made
        comps = isl[net]
        cs = [comp_cells(c) for c in comps]
        links = 0
        while len(comps) > 1:
            src = cs[-1]
            dst = set().union(*cs[:-1])
            walk = src | dst
            path = astar(occ, occ_via, hard, net, src, dst, walk)
            if path is None:
                return links, f"A* found no path ({len(comps)-1} link(s) left)"
            segs, via_pts = simplify(path)
            ok = True
            new_items = []
            for run in segs:
                L = run[0][2]
                for a, b_ in zip(run, run[1:]):
                    pa, pb = pos_of(a[0], a[1]), pos_of(b_[0], b_[1])
                    sh = seg_shape(pa, pb, TRACK_W)
                    bb = pcbnew.BOX2I(pcbnew.VECTOR2I(min(pa.x, pb.x) - TRACK_W,
                                                      min(pa.y, pb.y) - TRACK_W),
                                      pcbnew.VECTOR2I(abs(pa.x - pb.x) + 2 * TRACK_W,
                                                      abs(pa.y - pb.y) + 2 * TRACK_W))
                    if bd.in_keepout(sh, False) or \
                       not bd.clear_shape(sh, bb, net, (L,), CLEAR - 100):
                        ok = False
                    new_items.append(("t", pa, pb, L))
            for (i, j) in via_pts:
                pv = pos_of(i, j)
                sh = probe(pv.x, pv.y, VIA_D)
                bb = pcbnew.BOX2I(pcbnew.VECTOR2I(pv.x - VIA_D, pv.y - VIA_D),
                                  pcbnew.VECTOR2I(2 * VIA_D, 2 * VIA_D))
                if bd.in_keepout(sh, True) or not bd.hole_ok(pv) or \
                   not bd.clear_shape(sh, bb, net, (F, B), CLEAR - 100):
                    ok = False
                new_items.append(("v", pv))
            if not ok:
                return links, "exact check rejected the A* path"
            if not args.dry_run:
                for item in new_items:
                    if item[0] == "t":
                        t = bd.add_track(item[1], item[2], item[3], net)
                        paint_new(occ, occ_via, t, (item[3],))
                    else:
                        v = bd.add_via(item[1], net)
                        paint_new(occ, occ_via, v, LAYERS)
            made += 1
            links += 1
            hit = path[-1]
            for k in range(len(comps) - 1):
                if hit in cs[k]:
                    comps[k] += comps.pop()
                    cs[k] |= cs.pop()
                    break
            else:
                comps[0] += comps.pop()
                cs[0] |= cs.pop()
        return links, None

    pending = sorted((n for n in isl if len(isl[n]) > 1
                      and names[n] not in EXCLUDE),
                     key=hop_len, reverse=True)
    occ = occ_via = hard = None
    for tier in TIERS:
        CLEAR, TRACK_W = tier["clear"], tier["track"]
        INFL_TRK = CLEAR + TRACK_W // 2
        INFL_VIA = CLEAR + VIA_D // 2
        print(f"\n-- tier {tier['name']}: rebuilding maps, "
              f"{len(pending)} nets pending --")
        occ, occ_via, hard = build_maps(bd)
        still = []
        for net in pending:
            nm = names[net]
            links, why = try_net(net, nm)
            if why:
                still.append(net)
                print(f"  {nm}: {links} link(s), stuck: {why}")
            else:
                print(f"  {nm}: complete")
        pending = still
        if not pending:
            break

    for net in pending:
        n_left = len(isl[net]) - 1
        failed += n_left
        fails.append((names[net], f"{n_left} link(s) unrouted at all tiers"))

    print(f"\nlinks made: {made}   failed: {failed}")
    for nm, why in fails:
        print(f"  FAIL {nm}: {why}")

    if not args.dry_run:
        # the fine tier is JLC-standard-capable; align the board's rules
        ds = bd.b.GetDesignSettings()
        ds.m_MinClearance = MM(0.127)
        ds.m_TrackMinWidth = MM(0.127)
        try:
            bd.b.GetAllNetClasses()["Default"].SetClearance(MM(0.127))
        except Exception as e:
            print("netclass update skipped:", e)
        print("refilling zones + saving ...")
        pcbnew.ZONE_FILLER(bd.b).Fill(bd.b.Zones())
        bd.b.BuildConnectivity()
        after = bd.b.GetConnectivity().GetUnconnectedCount(False)
        print(f"unconnected after: {after}  (was {before})")
        pcbnew.SaveBoard(BRD, bd.b)


if __name__ == "__main__":
    main()
