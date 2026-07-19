#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inject the Stratos Drones logo (an "S" made of two swept propeller blades
around a hub) + the "STRATOS DRONES" wordmark onto the board silkscreen,
as native vector shapes (gr_poly / gr_circle / gr_text).

Text-level append (no pcbnew) so it CANNOT disturb the existing routing —
run it on the committed, partially-routed stratosdrone.kicad_pcb. It is
idempotent: any previous logo block (tagged with SENTINEL) is stripped first.

    python3 scripts/add_logo.py            # default: back silk, lower area
"""
import os, sys, math, uuid, re

PCB = os.path.join(os.path.dirname(__file__), "..", "stratos_fpv_aio.kicad_pcb")
SENTINEL = "stratos-logo"          # tstamp marker -> lets us re-run cleanly

# ---- logo geometry in SVG space (viewBox 240x240, centre 120,120) ----------
# Two blades (cubic-bezier outlines) + hub ring + centre dot. Mirrors the
# vector we designed; the lower blade is the 180-deg rotation of the upper.
UPPER = [(118,112), [((138,96),(150,70),(150,44)),
                     ((168,60),(172,92),(156,116)),
                     ((150,124),(140,128),(128,126)),
                     ((120,124),(116,120),(118,112))]]
LOWER = [(122,128), [((102,144),(90,170),(90,196)),
                     ((72,180),(68,148),(84,124)),
                     ((90,116),(100,112),(112,114)),
                     ((120,116),(124,120),(122,128))]]
HUB_R, HUB_W, DOT_R = 15.0, 10.0, 4.0   # ring mid-radius, ring width, dot radius (svg units)

def bezier(p0, p1, p2, p3, n=18):
    out = []
    for i in range(1, n + 1):
        t = i / n; u = 1 - t
        x = u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0]
        y = u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]
        out.append((x, y))
    return out

def flatten(path):
    start, segs = path
    pts = [start]; cur = start
    for c1, c2, end in segs:
        pts += bezier(cur, c1, c2, end); cur = end
    return pts

def inject(center=(19.0, 59.0), tall_mm=10.6, layer="B.SilkS", mirror=True,
           wordmark="STRATOS DRONES", text_dy=8.6, text_size=1.5):
    cx, cy = center
    s = tall_mm / 152.0                      # svg logo is ~152 units tall
    sx = -1 if mirror else 1                  # pre-mirror X for back-side reading
    def M(x, y):                              # svg -> board mm
        return (cx + sx*(x - 120.0)*s, cy + (y - 120.0)*s)

    tag = f"(tstamp {uuid.uuid4()})"          # (real uuids; SENTINEL added as suffix comment-free)
    items = []
    def poly(pts):
        xy = " ".join(f"(xy {x:.3f} {y:.3f})" for x, y in pts)
        items.append(f'  (gr_poly (pts {xy}) (stroke (width 0) (type solid)) '
                     f'(fill solid) (layer "{layer}") (tstamp {SENTINEL}-{uuid.uuid4()}))')
    def circle(cxy, r_mm, w_mm, fill):
        ccx, ccy = cxy
        items.append(f'  (gr_circle (center {ccx:.3f} {ccy:.3f}) (end {ccx+r_mm:.3f} {ccy:.3f}) '
                     f'(stroke (width {w_mm:.3f}) (type solid)) (fill {fill}) '
                     f'(layer "{layer}") (tstamp {SENTINEL}-{uuid.uuid4()}))')

    poly([M(x, y) for x, y in flatten(UPPER)])
    poly([M(x, y) for x, y in flatten(LOWER)])
    circle(M(120, 120), HUB_R*s, HUB_W*s, "none")     # hub ring
    circle(M(120, 120), DOT_R*s, 0,       "solid")    # centre dot
    just = " (justify mirror)" if mirror else ""   # centred horizontally by default
    # single line so the SENTINEL tag covers the whole item (idempotent strip)
    items.append(
        f'  (gr_text "{wordmark}" (at {cx:.3f} {cy+text_dy:.3f}) (layer "{layer}") '
        f'(effects (font (size {text_size} {text_size}) (thickness {text_size*0.16:.2f})){just}) '
        f'(tstamp {SENTINEL}-{uuid.uuid4()}))')

    txt = open(PCB).read()
    # strip any previous logo block (lines whose tstamp carries SENTINEL)
    txt = "\n".join(l for l in txt.splitlines() if SENTINEL not in l)
    idx = txt.rstrip().rfind(")")
    open(PCB, "w").write(txt[:idx] + "\n" + "\n".join(items) + "\n" + txt[idx:])
    print(f"injected logo + wordmark on {layer} at {center}, {tall_mm} mm tall "
          f"({'mirrored' if mirror else 'front'})")

if __name__ == "__main__":
    # mark in the clean upper-middle pour (above the sensor aperture at y>=29),
    # wordmark along the bottom edge; both centred so back-mirroring stays aligned.
    inject(center=(16.0, 13.5), tall_mm=6.5, text_dy=12.5, text_size=1.0)
