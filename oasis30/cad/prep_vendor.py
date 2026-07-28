#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prépare les STEP **du commerce** de `../ref/vendor_step/` pour la 3-D.

Ce sont les fichiers des constructeurs, jamais redessinés : ils remplacent les
primitives qui tenaient lieu de moteurs, d'air unit, de caméra et d'antennes
dans le visualisateur. On n'en garde que ce qui sert au montage :

  · **air unit** — boîtier haut et bas, USB-C, connecteur de nappe et les 4
    pattes de fixation : entraxe **25,5 × 25,5**, ce qui recoupe exactement le
    perçage VTX relevé sur le châssis ;
  · **caméra** — le bloc optique **et ses deux tourillons** (les ergots Ø 2,1
    en y = ±10, qui sont l'axe de bascule), mais **pas** les 148 mm de nappe
    droite du STEP : dans le drone elle est pliée, on la retrace en courbe dans
    le visualisateur ;
  · **antenne** — **un seul** des deux brins, coupé sous son fourreau et remis
    sur son axe, pour l'instancier deux fois dans les alésages du support de
    queue (relevés à Ø 3,0, entraxe 21,4). Le connecteur MMCX est retiré : il
    n'est pas au support, il est branché sur l'air unit, à l'autre bout d'un
    coaxial que le visualisateur trace en courbe ;
  · **moteur XING2 1404** — pour la 3-D, **l'enveloppe visible seulement** :
    cloche, arbre, embase et manchon de sortie de fils. Roulements, billes,
    aimants et bobinages sont enfermés dans la cloche ; les mailler coûtait
    48 000 triangles pour des pièces qu'on ne voit jamais. Les 25 mm de fils
    droits du STEP sont retirés aussi : le visualisateur les fait passer par le
    canal du protège-bras jusqu'aux pads de l'ESC. Le plan de pose est à
    z = −4,25 dans le fichier ; c'est lui qu'on vient plaquer sur la face haute
    du bras. Le maillage fin, lui, garde tout l'intérieur.

Attention aux cotes : `getBoundingBox` d'OpenCASCADE est **majorante** sur les
faces courbes — il annonce Ø 28,3 pour la cloche du 1404. Les cotes affichées
ci-dessous sont lues sur les **nœuds du maillage**, qui donnent Ø 19,9.

Seul le maillage **grossier** est écrit dans le dépôt, dans `stl/viz/` : la
page 3-D embarque ses STL en base64, un maillage de CAO complet la ferait
exploser. Il ne garde que les gros solides et passe dans un regroupement de
sommets. Le maillage fin sert à relever les cotes exactes affichées ci-dessous ;
il n'est pas versionné — le STEP en est la source, et `--ref` le régénère.

    python3 oasis30/cad/prep_vendor.py             # -> stl/viz/{dji,xing}_*.stl
    python3 oasis30/cad/prep_vendor.py --ref       # + le maillage fin dans stl/
    python3 oasis30/cad/prep_vendor.py xing2_1404  # une seule pièce (le STEP
                                                   # moteur seul prend ~10 min)
"""
import os
import struct
import sys
import tempfile

import gmsh

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "ref", "vendor_step")
OUT = os.path.join(HERE, "stl")
VIZ = os.path.join(OUT, "viz")

# Numéros de volume relevés dans le STEP lui-même (voir le docstring) ; ils sont
# stables tant que le fichier n'est pas remplacé.
#   nom STEP, nom de sortie, volumes gardés (None = tous), volumes gardés pour
#   la 3-D, taille de maille (fine, grossière), pas de regroupement, description
# Moteur : les 6 brins de fil droits (25 et 23,4 mm) sont retirés du maillage
# fin — le visualisateur les fait passer par le canal du protège-bras.
WIRES = list(range(128, 134))
MOTOR_FULL = [t for t in range(1, 138) if t not in WIRES]
# Pour la 3-D on ne garde que l'ENVELOPPE VISIBLE : cloche, arbre, embase,
# manchon de sortie de fils et les pattes de soudure. Roulements, billes,
# aimants et bobinages sont enfermés dans la cloche — les mailler coûtait
# 48 000 triangles pour des pièces qu'on ne voit jamais.
MOTOR_SHELL = [1, 15, 36, 127, 134, 135, 136, 137]

JOBS = [
    dict(src="DJI_O4_AIR_UNIT_PRO", name="dji_air_unit",
         keep=None, keep_viz=[1, 2, 3, 4, 5, 6, 15, 16, 17],
         size=(0.55, 2.6), cell=1.15,
         desc="Air unit O4 Pro — 33,5 carré, fixation 25,5"),
    dict(src="DJI_O4_PRO_CAM", name="dji_camera",
         keep=[1, 2, 3, 54, 55], keep_viz=[1, 2, 3, 54, 55],
         size=(0.55, 2.2), cell=0.85,
         desc="Caméra O4 Pro + tourillons — nappe retirée"),
    dict(src="DJI_O4_Pro_Antenna_v1", name="dji_antenna",
         keep=[2], keep_viz=[2], size=(0.5, 1.0), cell=0.35,
         trim_z=9.0,
         desc="Antenne O4 Pro — un brin, sans connecteur"),
    # les volumes 128 à 133 sont les 6 brins de fil droits (25 et 23,4 mm) ;
    # tout le reste du moteur est gardé, y compris la sortie de fils à l'embase
    dict(src="XING2_1404", name="xing2_1404",
         keep=MOTOR_FULL, keep_viz=MOTOR_SHELL, size=(0.5, 2.0), cell=None,
         desc="Moteur XING2 1404 — plan de pose à z = −4,25"),
]


def read_stl(path):
    with open(path, "rb") as f:
        d = f.read()
    n = struct.unpack("<I", d[80:84])[0]
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


def bounds(tris):
    return ([min(v[i] for t in tris for v in t) for i in range(3)],
            [max(v[i] for t in tris for v in t) for i in range(3)])


def shift(tris, d):
    return [tuple((v[0] + d[0], v[1] + d[1], v[2] + d[2]) for v in t) for t in tris]


def cluster(tris, cell):
    """Décimation par regroupement de sommets, représentant = **BARYCENTRE**.

    Même méthode que `prep_sub250.py` : les sommets sont rangés dans des
    cellules de `cell` mm et chaque cellule est remplacée par la **moyenne** des
    sommets qu'elle contient — pas par le point de grille. Coller sur la grille
    escaliérait les arêtes et arrondissait les perçages en polygones.
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
            & (idx[:, 0] != idx[:, 2]))
    idx = idx[keep]
    _, uniq = np.unique(np.sort(idx, axis=1), axis=0, return_index=True)
    idx = idx[np.sort(uniq)]
    return [tuple(map(tuple, cen[t])) for t in idx]


def build(job, viz):
    """Importe le STEP, ne garde que les volumes voulus, maille, écrit le STL."""
    gmsh.clear()
    gmsh.model.add(job["name"])
    gmsh.model.occ.importShapes(os.path.join(SRC, job["src"] + ".step"))
    gmsh.model.occ.synchronize()
    keep = job["keep_viz"] if viz else job["keep"]
    if keep is not None:
        drop = [(3, t) for _, t in gmsh.model.getEntities(3) if t not in keep]
        if drop:
            gmsh.model.occ.remove(drop, recursive=True)
            gmsh.model.occ.synchronize()
    if job.get("trim_z") is not None:
        # on coupe tout ce qui est sous le fourreau : le connecteur MMCX du
        # STEP n'a rien à faire dans l'alésage du support de queue
        z = job["trim_z"]
        bb = gmsh.model.getBoundingBox(-1, -1)
        pad = 5.0
        box = gmsh.model.occ.addBox(bb[0] - pad, bb[1] - pad, bb[2] - pad,
                                    bb[3] - bb[0] + 2 * pad,
                                    bb[4] - bb[1] + 2 * pad,
                                    z - bb[2] + pad)
        gmsh.model.occ.cut([(3, t) for _, t in gmsh.model.getEntities(3)],
                           [(3, box)])
        gmsh.model.occ.synchronize()
    size = job["size"][1 if viz else 0]
    gmsh.option.setNumber("Mesh.MeshSizeMax", size)
    gmsh.option.setNumber("Mesh.MeshSizeMin", size / 6)
    gmsh.model.mesh.generate(2)
    if viz:
        path = os.path.join(VIZ, job["name"] + ".stl")
    elif KEEP_REF:
        path = os.path.join(OUT, job["name"] + ".stl")
    else:
        # maillage fin jeté après lecture : il ne sert qu'aux cotes, et le STEP
        # de `ref/vendor_step/` en reste la source
        path = os.path.join(tempfile.gettempdir(), job["name"] + "_ref.stl")
    gmsh.write(path)

    tris = read_stl(path)
    if viz and job["cell"]:
        # `cell=None` : pas de regroupement. Sur le moteur, une grille de 0,9 mm
        # rabotait les rayons de cloche, larges de 1,5 — pour cette pièce c'est
        # la finesse de maillage seule qui règle le poids.
        tris = cluster(tris, job["cell"])
    if job.get("trim_z") is not None:
        # l'antenne doit sortir centrée sur son axe, fourreau démarrant à z = 0
        lo, hi = bounds(tris)
        tris = shift(tris, (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))
    write_stl(path, tris)
    return tris, path


KEEP_REF = "--ref" in sys.argv
ONLY = [a for a in sys.argv[1:] if not a.startswith("-")]      # filtre par nom


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(VIZ, exist_ok=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("Mesh.Binary", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    for job in JOBS:
        if ONLY and job["name"] not in ONLY:
            continue
        fine, fp = build(job, False)
        light, lp = build(job, True)
        if not KEEP_REF:
            os.remove(fp)
        lo, hi = bounds(fine)
        print("  %-13s %6d tris fins (3-D %5d, %4d Kio)  %5.1f × %5.1f × %5.1f mm"
              % (job["name"], len(fine), len(light), os.path.getsize(lp) // 1024,
                 hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
        print("     %-10s x[%7.2f %7.2f]  y[%7.2f %7.2f]  z[%7.2f %7.2f]   %s"
              % ("repère", lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], job["desc"]))
    gmsh.finalize()


if __name__ == "__main__":
    print("OASIS 30 — conversion des STEP du commerce\n")
    main()
