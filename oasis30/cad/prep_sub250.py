#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prépare les STL **d'origine Sub250** pour le visualisateur.

Les fichiers de `../ref/sub250_stl/` ne sont jamais modifiés : ils restent la
référence de forme. Ce script en écrit des copies exploitables dans `stl/` :

  · `side_panel.stl` **est le flanc gauche** → on en écrit deux fichiers
    imprimables distincts : `flanc_gauche.stl` (la pièce telle quelle) et
    `flanc_droit.stl` (son **miroir sur Y**, avec l'enroulement des triangles
    inversé pour que les normales restent sortantes) ;
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

# fichier source → (nom de sortie, extraction, description, miroir ?)
# `side_panel.stl` est le flanc GAUCHE dans son entier ; le flanc droit en est
# le miroir, écrit dans son propre fichier pour pouvoir être imprimé tel quel.
JOBS = [
    ("side_panel.stl",         "flanc_gauche",        None,    "Flanc GAUCHE (pièce d'origine)"),
    ("side_panel.stl",         "flanc_droit",         None,    "Flanc DROIT (miroir du gauche)", True),
    ("foot_pad_x4.stl",        "sub250_foot_pad",     "comp0", "Patin de pied (×4)"),
    ("rx_antenna_plate.stl",   "sub250_rx_plate",     None,    "Platine d'antennes RX"),
    ("tail_antenna_mount.stl", "sub250_tail_mount",   None,    "Support d'antenne de queue"),
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


def mirror_y(tris):
    """Miroir par rapport au plan **Y = 0** du fichier.

    C'est bien Y et pas X : la face du flanc est dans le plan X-Z, donc son
    épaisseur (Y) est ce qui devient la gauche-droite du drone une fois la
    pièce tournée en place. Un miroir sur X retournerait la pièce d'avant en
    arrière — ce n'est pas la même pièce.

    On inverse aussi l'ordre de deux sommets de chaque triangle : sans ça
    l'enroulement change de sens et toutes les normales pointent vers
    l'intérieur — le trancheur voit alors une pièce « retournée ».
    """
    return [((c[0], -c[1], c[2]), (b[0], -b[1], b[2]), (a[0], -a[1], a[2]))
            for a, b, c in tris]


def cluster(tris, cell):
    """Décimation par **regroupement de sommets**, représentant = BARYCENTRE.

    Les sommets sont rangés dans des cellules de `cell` mm, puis chaque cellule
    est remplacée par la **moyenne** des sommets qu'elle contient — pas par le
    point de grille. C'est toute la différence : coller sur la grille escaliérait
    les arêtes et transformait les alésages Ø 3 de l'étrier de queue en blobs
    octogonaux. Le barycentre suit la surface, les cercles restent ronds.

    Aucune bibliothèque de décimation n'est disponible ici (fast_simplification
    et open3d sont absents) et la reconstruction de géométrie de gmsh échoue sur
    ces maillages. Les STL d'impression, eux, restent intacts.
    """
    import numpy as np

    V = np.asarray(tris, dtype=np.float64).reshape(-1, 3)
    key = np.floor(V / cell).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    n = int(inv.max()) + 1
    cen = np.zeros((n, 3))
    cnt = np.zeros(n)
    np.add.at(cen, inv, V)
    np.add.at(cnt, inv, 1)
    cen /= cnt[:, None]

    idx = inv.reshape(-1, 3)
    keep = ((idx[:, 0] != idx[:, 1]) & (idx[:, 1] != idx[:, 2])
            & (idx[:, 0] != idx[:, 2]))          # triangles écrasés
    idx = idx[keep]
    _, uniq = np.unique(np.sort(idx, axis=1), axis=0, return_index=True)
    idx = idx[np.sort(uniq)]                     # doublons exacts
    return [tuple(map(tuple, cen[t])) for t in idx]


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "viz"), exist_ok=True)
    for job in JOBS:
        src, name, pick, desc = job[:4]
        mirror = len(job) > 4 and job[4]
        tris = read_stl(os.path.join(SRC, src))
        if pick:
            comps = sorted(components(tris), key=len, reverse=True)
            idx = int(pick[-1])
            print("  %-22s %d composants → on extrait le n°%d" % (src, len(comps), idx))
            tris = comps[idx]
        if mirror:
            tris = mirror_y(tris)
        tris = recentre(tris)
        lo, hi = bounds(tris)
        write_stl(os.path.join(OUT, name + ".stl"), tris)
        light = cluster(tris, 0.35) if len(tris) > 8000 else tris
        write_stl(os.path.join(OUT, "viz", name + ".stl"), light)
        print("  %-22s %6d tris (viz %5d)  %5.1f × %5.1f × %5.1f mm   %s"
              % (name, len(tris), len(light),
                 hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], desc))


if __name__ == "__main__":
    print("OASIS 30 — préparation des STL Sub250 d'origine\n")
    main()
