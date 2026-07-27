#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prépare les STL **d'origine Sub250** pour le visualisateur.

Les fichiers de `../ref/sub250_stl/` ne sont jamais modifiés : ils restent la
référence de forme. Ce script en écrit des copies exploitables dans `stl/` :

  · `foot_pad_x4.stl` contient **4 patins** posés à plat sur une planche
    d'impression → on en extrait **un seul**, ré-centré ;
  · chaque pièce est ramenée à une origine prévisible (centrée en X/Y, posée
    sur z = 0) pour que le placement dans la scène 3-D soit lisible.

    python3 oasis30/cad/prep_sub250.py       # -> stl/sub250_*.stl
"""
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "ref", "sub250_stl")
OUT = os.path.join(HERE, "stl")

# fichier source → (nom de sortie, n'garder qu'un composant ?, description)
JOBS = [
    ("side_panel.stl",         "sub250_side_panel",   False, "Flanc latéral (×2)"),
    ("foot_pad_x4.stl",        "sub250_foot_pad",     True,  "Patin de pied (×4)"),
    ("rx_antenna_plate.stl",   "sub250_rx_plate",     False, "Platine d'antennes RX"),
    ("tail_antenna_mount.stl", "sub250_tail_mount",   False, "Support d'antenne de queue"),
]


def read_stl(path):
    """Lit un STL binaire → liste de triangles [(v0, v1, v2), ...]."""
    with open(path, "rb") as f:
        d = f.read()
    n = struct.unpack("<I", d[80:84])[0]
    if 84 + 50 * n != len(d):
        raise ValueError("%s n'est pas un STL binaire" % path)
    tris = []
    for i in range(n):
        o = 84 + 50 * i + 12
        tris.append(tuple(struct.unpack("<3f", d[o + 12 * j:o + 12 * j + 12])
                          for j in range(3)))
    return tris


def write_stl(path, tris):
    out = bytearray(b"\0" * 80 + struct.pack("<I", len(tris)))
    for a, b, c in tris:
        ux, uy, uz = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        vx, vy, vz = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        out += struct.pack("<3f", nx / ln, ny / ln, nz / ln)
        for v in (a, b, c):
            out += struct.pack("<3f", *v)
        out += b"\0\0"
    with open(path, "wb") as f:
        f.write(bytes(out))


def components(tris):
    """Sépare les triangles en composants connexes (union-find sur les sommets)."""
    key = {}
    parent = []

    def vid(v):
        k = (round(v[0], 4), round(v[1], 4), round(v[2], 4))
        if k not in key:
            key[k] = len(parent)
            parent.append(len(parent))
        return key[k]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    ids = []
    for t in tris:
        r = [vid(v) for v in t]
        ids.append(r)
        r0 = find(r[0])
        for x in r[1:]:
            rx = find(x)
            if rx != r0:
                parent[rx] = r0

    groups = {}
    for t, r in zip(tris, ids):
        groups.setdefault(find(r[0]), []).append(t)
    return list(groups.values())


def bounds(tris):
    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    zs = [v[2] for t in tris for v in t]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def recentre(tris):
    """Centre en X/Y, pose sur z = 0."""
    lo, hi = bounds(tris)
    dx, dy, dz = -(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]
    return [tuple((v[0] + dx, v[1] + dy, v[2] + dz) for v in t) for t in tris]


def cluster(tris, cell):
    """Décimation par **regroupement de sommets** : on colle les sommets sur une
    grille de `cell` mm, puis on jette les triangles devenus dégénérés.

    Aucune bibliothèque de décimation n'est disponible ici (fast_simplification
    et open3d sont absents) ; cette méthode est grossière mais suffit largement
    pour l'affichage — les STL d'impression, eux, restent intacts.
    """
    snap = lambda v: (round(v[0] / cell) * cell,
                      round(v[1] / cell) * cell,
                      round(v[2] / cell) * cell)
    out, seen = [], set()
    for t in tris:
        a, b, c = snap(t[0]), snap(t[1]), snap(t[2])
        if a == b or b == c or a == c:
            continue                      # triangle écrasé par la grille
        k = tuple(sorted((a, b, c)))
        if k in seen:
            continue                      # doublon exact
        seen.add(k)
        out.append((a, b, c))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "viz"), exist_ok=True)
    for src, name, single, desc in JOBS:
        tris = read_stl(os.path.join(SRC, src))
        if single:
            comps = components(tris)
            comps.sort(key=len, reverse=True)
            print("  %-22s %d composants → on garde le plus gros" % (src, len(comps)))
            tris = comps[0]
        tris = recentre(tris)
        lo, hi = bounds(tris)
        write_stl(os.path.join(OUT, name + ".stl"), tris)
        light = cluster(tris, 0.45) if len(tris) > 8000 else tris
        write_stl(os.path.join(OUT, "viz", name + ".stl"), light)
        print("  %-22s %6d tris (viz %5d)  %5.1f × %5.1f × %5.1f mm   %s"
              % (name, len(tris), len(light),
                 hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], desc))


if __name__ == "__main__":
    print("OASIS 30 — préparation des STL Sub250 d'origine\n")
    main()
