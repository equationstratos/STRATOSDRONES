#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OASIS 30 — modèle paramétrique du châssis Sub250 OasisFly30.

Construit avec le noyau **OpenCASCADE de gmsh** : chaque pièce est un vrai
solide B-rep, donc exportable en `.step` (conception, ré-usinage) *et*
maillable en `.stl` (impression, visualisateur).

    python3 export.py            # écrit step/ + stl/ + les contrôles de cotes

Toutes les cotes viennent de `tune.py`. Ce fichier ne contient que de la
construction géométrique — si un chiffre ne va pas, il se change dans tune.py.
"""
import math
import gmsh

import tune as T

occ = None          # rempli par start()


# ══════════════════════════════════════════════════ socle gmsh
def start(name="oasis30"):
    global occ
    if not gmsh.isInitialized():
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
    gmsh.clear()
    gmsh.model.add(name)
    occ = gmsh.model.occ
    return occ


# ══════════════════════════════════════════════════ primitives
def box(x, y, z, dx, dy, dz):
    return (3, occ.addBox(x, y, z, dx, dy, dz))


def cyl(x, y, z, dz, r):
    return (3, occ.addCylinder(x, y, z, 0, 0, dz, r))


def fuse(objs):
    """Union robuste d'une liste de solides."""
    objs = list(objs)
    if len(objs) == 1:
        return objs
    out, _ = occ.fuse([objs[0]], objs[1:])
    return out


def cut(objs, tools):
    objs, tools = list(objs), list(tools)
    if not tools:
        return objs
    out, _ = occ.cut(objs, tools)
    return out


def rpad(x, y, z, w, l, h, r):
    """Prisme à coins arrondis (w suivant X, l suivant Y), centré en (x, y)."""
    r = min(r, w / 2 - 1e-6, l / 2 - 1e-6)
    parts = [box(x - w / 2 + r, y - l / 2, z, w - 2 * r, l, h),
             box(x - w / 2, y - l / 2 + r, z, w, l - 2 * r, h)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(x + sx * (w / 2 - r), y + sy * (l / 2 - r), z, h, r))
    return fuse(parts)


def prism(pts, z, h):
    """Extrusion d'un polygone fermé (liste de (x, y)) de z à z+h."""
    ids = [occ.addPoint(px, py, z) for px, py in pts]
    lines = [occ.addLine(ids[i], ids[(i + 1) % len(ids)]) for i in range(len(ids))]
    surf = occ.addPlaneSurface([occ.addCurveLoop(lines)])
    return [e for e in occ.extrude([(2, surf)], 0, 0, h) if e[0] == 3]


def mirror_profile(prof):
    """(Y, demi-largeur) → contour fermé complet, sens trigonométrique."""
    right = [(w, y) for y, w in prof]
    left = [(-w, y) for y, w in reversed(prof)]
    return right + left


def drill(solid, xy, r, z0, h):
    """Perce des trous traversants verticaux."""
    return cut(solid, [cyl(x, y, z0, h, r) for x, y in xy])


def square_pattern(pitch, cx=0.0, cy=0.0):
    h = pitch / 2
    return [(cx + h, cy + h), (cx - h, cy + h), (cx - h, cy - h), (cx + h, cy - h)]


def place(objs, dx=0, dy=0, dz=0, rz=0.0):
    """Rotation autour de Z (degrés) puis translation."""
    if rz:
        occ.rotate(objs, 0, 0, 0, 0, 0, 1, math.radians(rz))
    if dx or dy or dz:
        occ.translate(objs, dx, dy, dz)
    return objs


def copy(objs):
    return occ.copy(list(objs))


def occ_ref():
    """Le module `occ` courant — les autres modules passent par ici, car `occ`
    n'est rempli qu'au premier `start()`."""
    return occ


# ══════════════════════════════════════════════════ positions partagées
ARM_ANGLE = math.degrees(math.atan2(T.MY, T.MX))        # 33,55°
ARM_R = math.hypot(T.MX, T.MY)                          # 75,0 mm


def arm_root_holes():
    """Les 2 trous M3 de chaque fourche de bras, dans le repère du châssis."""
    out = []
    for sx in (1, -1):
        for sy in (1, -1):
            a = math.radians(ARM_ANGLE) * (1 if sx * sy > 0 else -1)
            for r in (T.ARM_R_IN + 4.0, T.ARM_R_IN + 14.0):
                x, y = r * math.cos(a), r * math.sin(a)
                out.append((sx * abs(x), sy * abs(y)))
    return out


def stack_holes():
    return square_pattern(T.STACK, 0, T.STACK_Y)


def vtx_holes():
    return square_pattern(T.VTX_STACK, 0, T.STACK_Y)


# ══════════════════════════════════════════════════ pièces carbone
def bottom_plate():
    """Plaque basse 2,5 mm — porte les bras, fenêtre centrale pour le stack."""
    z, h = T.Z_BOTTOM, T.PLATE_B
    body = prism(mirror_profile(T.PROFILE_WIDE), z, h)
    tools = [
        rpad(0, T.STACK_Y, z - 1, T.BAY_W, 30, h + 2, 6)[0],           # fenêtre stack
        rpad(0, -52, z - 1, 12, 20, h + 2, 5)[0],                      # allègement queue
    ]
    for sx in (1, -1):                                                 # allègements latéraux
        tools.append(rpad(sx * 16, 22, z - 1, 6, 14, h + 2, 3)[0])
    body = cut(body, tools)
    body = drill(body, arm_root_holes(), T.M3 / 2, z - 1, h + 2)
    body = drill(body, T.STANDOFFS_TOP + T.STANDOFFS_CAM, T.M3 / 2, z - 1, h + 2)
    return body


def mid_plate():
    """Plaque médiane 2,5 mm — coiffe les bras, porte le stack et l'air unit."""
    z, h = T.Z_MID, T.PLATE_M
    prof = [(y, max(6.0, w - 1.0)) for y, w in T.PROFILE_WIDE]         # légèrement rentrée
    body = prism(mirror_profile(prof), z, h)
    tools = [rpad(0, T.STACK_Y, z - 1, 17, 17, h + 2, 2)[0]]           # passage câbles stack
    for sy in (1, -1):                                                 # ouïes
        tools.append(rpad(0, sy * 26, z - 1, 9, 16, h + 2, 4)[0])
        for sx in (1, -1):
            tools.append(rpad(sx * 14, sy * 14, z - 1, 6, 15, h + 2, 3)[0])
    body = cut(body, tools)
    body = drill(body, arm_root_holes(), T.M3 / 2, z - 1, h + 2)
    body = drill(body, stack_holes() + vtx_holes(), T.M3 / 2, z - 1, h + 2)
    body = drill(body, T.STANDOFFS_TOP + T.STANDOFFS_CAM, T.M3 / 2, z - 1, h + 2)
    return body


def _deck_outline(y0, y1, w):
    """Contour étroit à bouts pointus (le chevron Sub250)."""
    hw = w / 2
    return [(hw, y1 - 8), (hw - 5, y1), (-hw + 5, y1), (-hw, y1 - 8),
            (-hw, y0 + 10), (0, y0), (hw, y0 + 10)]


def deck_plate():
    """Pont étroit (« splint ») 2,5 mm, posé sur la médiane."""
    z, h = T.Z_DECK, T.PLATE_D
    body = prism(_deck_outline(-58, 34, T.DECK_W), z, h)
    tools = [rpad(0, y, z - 1, 8, 22, h + 2, 4)[0] for y in (16, -16, -40)]
    body = cut(body, tools)
    body = drill(body, T.STANDOFFS_TOP + T.STANDOFFS_CAM, T.M3 / 2, z - 1, h + 2)
    return body


def top_plate():
    """Roof 2,0 mm — fentes de sangle, découpe XT30, montage sur entretoises."""
    z, h = T.Z_TOP, T.PLATE_T
    body = prism(_deck_outline(T.DECK_Y0, T.DECK_Y1, T.DECK_W), z, h)
    tools = []
    for y in (22, 2, -18, -52):                                        # fentes de sangle
        for sx in (1, -1):
            tools.append(rpad(sx * 11, y, z - 1, 4.5, 13, h + 2, 2)[0])
    tools.append(rpad(0, 10, z - 1, 9, 22, h + 2, 4)[0])               # allègement central
    tools.append(rpad(0, T.XT30_Y, z - 1, T.XT30_W + 2 * T.CLR,        # passage XT30
                      13, h + 2, 2)[0])
    body = cut(body, tools)
    body = drill(body, T.STANDOFFS_TOP + T.STANDOFFS_CAM, T.M3 / 2, z - 1, h + 2)
    return body


def _arm_blank(z):
    """La forme brute d'un bras, dirigée vers +X, racine à x = ARM_R_IN."""
    h = T.ARM_T
    wr, wm = T.ARM_W_ROOT / 2, T.ARM_W_MID / 2
    beam = prism([(T.ARM_R_IN, wr), (T.ARM_R_IN + 12, wm), (ARM_R - 6, wm),
                  (ARM_R - 6, -wm), (T.ARM_R_IN + 12, -wm), (T.ARM_R_IN, -wr)], z, h)
    pad = rpad(ARM_R, 0, z, T.MOTOR_PAD_D, T.MOTOR_PAD_D, h, 5.0)
    body = fuse(beam + pad)
    body = cut(body, [box(T.ARM_R_IN - 1, -3.0, z - 1, 11.0, 6.0, h + 2)])  # fourche
    body = drill(body, square_pattern(T.MOTOR_PCD, ARM_R, 0), T.M2 / 2, z - 1, h + 2)
    return drill(body, [(ARM_R, 0)], T.MOTOR_BORE / 2, z - 1, h + 2)


def arms():
    """Les 4 bras à leur place (miroirs X et Y du bras avant-droit)."""
    out = []
    for sx in (1, -1):
        for sy in (1, -1):
            body = _arm_blank(T.Z_ARM)
            place(body, rz=sy * ARM_ANGLE)
            if sx < 0:
                occ.mirror(body, 1, 0, 0, 0)
            out += body
    return out


def cam_side_plate(side=1):
    """Flanc de cage caméra 2,5 mm, vertical, à ±(CAM_W/2 + jeu)."""
    x = side * (T.CAGE_GAP / 2 + T.CAGE_T / 2)
    y0, y1 = T.CAM_Y - 12, T.CAM_Y + 10
    zb, zt = T.Z_MID, T.CAM_Z + 13
    pts = [(y0, zb), (y0 + 4, zt - 6), (y0 + 13, zt), (y1 - 4, zt - 2),
           (y1, zb + 10), (y1 - 6, zb)]
    ids = [occ.addPoint(x - T.CAGE_T / 2, py, pz) for py, pz in pts]
    lines = [occ.addLine(ids[i], ids[(i + 1) % len(ids)]) for i in range(len(ids))]
    surf = occ.addPlaneSurface([occ.addCurveLoop(lines)])
    body = [e for e in occ.extrude([(2, surf)], T.CAGE_T, 0, 0) if e[0] == 3]
    # ajours en amande + perçages caméra
    tools = []
    for dy, dz, r in ((-4, 4, 3.6), (5, 6, 3.0)):
        c = occ.addCylinder(x - T.CAGE_T, T.CAM_Y + dy, T.CAM_Z + dz,
                            2 * T.CAGE_T, 0, 0, r)
        tools.append((3, c))
    axle = occ.addCylinder(x - T.CAGE_T, T.CAM_Y, T.CAM_Z, 2 * T.CAGE_T, 0, 0, T.M2 / 2)
    tools.append((3, axle))
    return cut(body, tools)


def standoff(x, y, z, h, r_out=None):
    """Entretoise alu M3 tournée lisse."""
    r_out = r_out or T.STANDOFF_D / 2
    tube = [cyl(x, y, z, h, r_out)]
    return cut(tube, [cyl(x, y, z - 1, h + 2, T.M3 / 2)])


def standoffs():
    out = []
    for x, y in T.STANDOFFS_TOP + T.STANDOFFS_CAM:
        out += standoff(x, y, T.Z_DECK + T.PLATE_D, T.STANDOFF_H)
    return out


# ══════════════════════════════════════════════════ registre des pièces
CARBON = {
    "bottom_plate": (bottom_plate, "Plaque basse 2,5 mm — porte les bras"),
    "mid_plate":    (mid_plate,    "Plaque médiane 2,5 mm — coiffe les bras"),
    "deck_plate":   (deck_plate,   "Pont étroit 2,5 mm posé sur la médiane"),
    "top_plate":    (top_plate,    "Roof 2,0 mm — sangle, XT30, entretoises"),
    "arm":          (lambda: arm_single(), "Bras 3 mm (×4) — patin moteur + fourche"),
    "cam_side_plate": (lambda: cam_side_plate(1), "Flanc de cage caméra 2,5 mm (×2)"),
    "standoff":     (lambda: standoff(0, 0, 0, T.STANDOFF_H), "Entretoise M3 %g mm" % T.STANDOFF_H),
}


def arm_single():
    """Le bras seul, à plat à l'origine — c'est ce qu'on imprime / usine."""
    body = _arm_blank(0.0)
    occ.translate(body, -T.ARM_R_IN, 0, 0)
    return body


def assembly():
    """Le châssis complet, chaque pièce à sa place."""
    out = []
    out += bottom_plate()
    out += arms()
    out += mid_plate()
    out += deck_plate()
    out += top_plate()
    out += standoffs()
    for s in (1, -1):
        out += cam_side_plate(s)
    return out
