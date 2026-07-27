#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OASIS 30 — exporte chaque pièce en **.step** (B-rep) et en **.stl** (impression).

    python3 oasis30/cad/export.py              # tout
    python3 oasis30/cad/export.py bottom_plate # une seule pièce

Écrit `step/*.step`, `stl/*.stl` et `step/oasisfly30_assembly.step`, puis
contrôle les cotes clefs contre `tune.py` — le script **échoue** si une cote
dérive, pour qu'une erreur de modélisation ne parte jamais à l'impression.
"""
import os
import sys

import gmsh

import tune as T
import oasisfly30 as F
import printed as P

HERE = os.path.dirname(os.path.abspath(__file__))
STEP = os.path.join(HERE, "step")
STL = os.path.join(HERE, "stl")
VIZ = os.path.join(STL, "viz")

MESH_MAX = 1.0        # maille d'impression : fine
MESH_MIN = 0.15
VIZ_MAX = 3.0         # maille du visualisateur : grossière, la page reste légère
VIZ_MIN = 0.5

# nom → (constructeur, quantité, matière, description)
PARTS = [
    ("bottom_plate",   F.bottom_plate,            1, "carbone 2,5", "Plaque basse — porte les 4 bras"),
    ("mid_plate",      F.mid_plate,               1, "carbone 2,5", "Plaque médiane — coiffe les bras"),
    ("deck_plate",     F.deck_plate,              1, "carbone 2,5", "Pont étroit posé sur la médiane"),
    ("top_plate",      F.top_plate,               1, "carbone 2,0", "Roof — sangle, passage XT30"),
    ("arm",            F.arm_single,              4, "carbone 3,0", "Bras — patin moteur + fourche"),
    ("cam_side_plate", lambda: F.cam_side_plate(1), 2, "carbone 2,5", "Flanc de cage caméra"),
    ("standoff",       lambda: F.standoff(0, 0, 0, T.STANDOFF_H), 4, "alu M3",
     "Entretoise lisse %g mm" % T.STANDOFF_H),
] + P.PRINTED


def mesh_bbox():
    """Emprise **exacte**, mesurée sur les nœuds du maillage.

    `getBoundingBox` d'OpenCASCADE est volontairement majorante sur les faces
    courbes (elle ajoute jusqu'à ~1 mm) : elle ne peut pas servir de contrôle
    de cote. Les nœuds, eux, sont sur la surface.
    """
    _, coords, _ = gmsh.model.mesh.getNodes()
    xs, ys, zs = coords[0::3], coords[1::3], coords[2::3]
    return (xs.max() - xs.min(), ys.max() - ys.min(), zs.max() - zs.min()), \
           (xs.min(), ys.min(), zs.min(), xs.max(), ys.max(), zs.max())


def write_part(name, builder):
    F.start(name)
    builder()
    F.occ.synchronize()
    gmsh.write(os.path.join(STEP, name + ".step"))
    gmsh.option.setNumber("Mesh.Binary", 1)
    gmsh.option.setNumber("Mesh.MeshSizeMax", MESH_MAX)
    gmsh.option.setNumber("Mesh.MeshSizeMin", MESH_MIN)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.model.mesh.generate(2)
    gmsh.write(os.path.join(STL, name + ".stl"))
    kb = os.path.getsize(os.path.join(STL, name + ".stl")) // 1024
    (dx, dy, dz), _ = mesh_bbox()

    # seconde passe, grossière : c'est cette version que le visualisateur embarque
    gmsh.model.mesh.clear()
    gmsh.option.setNumber("Mesh.MeshSizeMax", VIZ_MAX)
    gmsh.option.setNumber("Mesh.MeshSizeMin", VIZ_MIN)
    gmsh.model.mesh.generate(2)
    gmsh.write(os.path.join(VIZ, name + ".stl"))
    return (dx, dy, dz), kb


def check(label, got, want, tol):
    ok = abs(got - want) <= tol
    print("      %-26s %8.2f  (attendu %.2f ±%.2f)  %s"
          % (label, got, want, tol, "OK" if ok else "*** ÉCART ***"))
    return ok


def main(only=None):
    os.makedirs(STEP, exist_ok=True)
    os.makedirs(STL, exist_ok=True)
    os.makedirs(VIZ, exist_ok=True)
    sizes = {}
    print("OASIS 30 — export STEP + STL\n")
    for name, builder, qty, mat, desc in PARTS:
        if only and name != only:
            continue
        (dx, dy, dz), kb = write_part(name, builder)
        sizes[name] = (dx, dy, dz)
        print("  %-16s ×%d  %-12s %6.1f × %6.1f × %5.1f mm   stl %4d KiB   %s"
              % (name, qty, mat, dx, dy, dz, kb, desc))

    if only:
        return 0

    # ── assemblage complet
    F.start("assembly")
    F.assembly()
    F.occ.synchronize()
    gmsh.write(os.path.join(STEP, "oasisfly30_assembly.step"))
    gmsh.option.setNumber("Mesh.MeshSizeMax", 2.5)
    gmsh.model.mesh.generate(2)
    gmsh.write(os.path.join(STL, "assembly.stl"))       # pour l'aperçu / le contrôle
    (ax, ay, az), ab = mesh_bbox()
    print("\n  %-16s     %-12s %6.1f × %6.1f × %5.1f mm   (STEP d'assemblage)"
          % ("assembly", "châssis", ax, ay, az))
    print("      nez Y=%+.1f · queue Y=%+.1f · Z %.1f → %.1f"
          % (ab[4], ab[1], ab[2], ab[5]))

    # ── contrôles
    print("\n  Contrôles de cotes")
    ok = True
    ok &= check("hauteur hors-tout", az, T.H_TOTAL, 0.3)
    # recoupement indépendant : la hauteur du flanc Sub250 d'origine
    ok &= check("= hauteur flanc Sub250", az, T.SIDE_PANEL_H, 0.3)
    ok &= check("largeur du bras", sizes["arm"][1], T.MOTOR_PAD_D, 0.2)
    ok &= check("longueur du bras", sizes["arm"][0],
                F.ARM_R - T.ARM_R_IN + T.MOTOR_PAD_D / 2, 0.3)
    ok &= check("épaisseur plaque basse", sizes["bottom_plate"][2], T.PLATE_B, 0.02)
    ok &= check("épaisseur roof", sizes["top_plate"][2], T.PLATE_T, 0.02)
    ok &= check("épaisseur bras", sizes["arm"][2], T.ARM_T, 0.02)

    # L'entraxe se relit sur l'assemblage : le patin moteur est un carré arrondi
    # tourné de l'angle du bras, son débord est (a-r)(|cos|+|sin|)+r.
    import math
    a, r = T.MOTOR_PAD_D / 2, 5.0
    th = math.radians(F.ARM_ANGLE)
    over = (a - r) * (abs(math.cos(th)) + abs(math.sin(th))) + r
    ok &= check("emprise en X (patins)", ax, 2 * (T.MX + over), 0.4)
    ok &= check("longueur hors-tout", ay, T.LEN_TOTAL, 1.0)     # cote publiée : 132 mm

    # dégagement d'hélices : les disques ne doivent pas se croiser
    gap_y = T.TRACK_Y - T.PROP_D
    gap_x = T.TRACK_X - T.PROP_D
    # le berceau caméra doit entrer entre les flancs de cage
    ok &= check("berceau dans la cage", sizes["cam_cradle_bottom"][0], T.CAGE_GAP, 0.6)

    # ── un perçage trop près du bord = une vis qui ne tient pas, voire qui ne
    #    passe pas. On contrôle chaque trou contre la silhouette réelle de la
    #    plaque, interpolée entre les points du profil.
    def half_width(y):
        p = sorted(T.PROFILE_WIDE, key=lambda a: a[0])
        if y <= p[0][0] or y >= p[-1][0]:
            return 0.0
        for (y0, w0), (y1, w1) in zip(p, p[1:]):
            if y0 <= y <= y1:
                return w0 + (w1 - w0) * (y - y0) / (y1 - y0)
        return 0.0

    print("\n  Marges de perçage (plaques basse et médiane)")
    worst = None
    for name, holes in (("entretoise", T.STANDOFFS_TOP + T.STANDOFFS_CAM),
                        ("racine de bras", F.arm_root_holes()),
                        ("stack", F.stack_holes() + F.vtx_holes())):
        for x, y in holes:
            margin = half_width(y) - abs(x) - T.M3 / 2
            if worst is None or margin < worst[0]:
                worst = (margin, name, x, y)
    m, name, x, y = worst
    print("      %-26s %8.2f mm au plus juste  (%s en x=%.1f, y=%.1f)"
          % ("marge au bord", m, name, x, y))
    if m < T.EDGE_MIN - T.M3:
        print("      *** un perçage sort de la plaque ou n'a pas de matière ***")
        ok = False

    print("      %-26s %8.2f mm avant/arrière, %.2f mm latéral"
          % ("dégagement hélices", gap_y, gap_x))
    if gap_y <= 0.5:
        print("      *** les hélices se croisent ***")
        ok = False

    print("\n  %s" % ("tout est conforme." if ok else "*** DES COTES SONT HORS TOLÉRANCE ***"))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        rc = main(sys.argv[1] if len(sys.argv) > 1 else None)
    finally:
        if gmsh.isInitialized():
            gmsh.finalize()
    sys.exit(rc)
