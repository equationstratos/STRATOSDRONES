#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prépare les STEP **DJI O4 Pro** du dossier `../ref/vendor_step/` pour la 3-D.

Ce sont les fichiers du constructeur, jamais redessinés : ils remplacent les
boîtes approximatives qui tenaient lieu d'air unit, de caméra et d'antennes dans
le visualisateur. On n'en garde que ce qui sert au montage :

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
    coaxial que le visualisateur trace en courbe.

Seul le maillage **grossier** est écrit dans le dépôt, dans `stl/viz/` : la
page 3-D embarque ses STL en base64, un maillage de CAO complet la ferait
exploser. Il ne garde que les gros solides et passe dans un regroupement de
sommets. Le maillage fin sert à relever les cotes exactes affichées ci-dessous ;
il n'est pas versionné — le STEP en est la source, et `--ref` le régénère.

    python3 oasis30/cad/prep_dji_o4.py         # -> stl/viz/dji_*.stl
    python3 oasis30/cad/prep_dji_o4.py --ref   # + le maillage fin dans stl/
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
    """Décimation par regroupement de sommets — même méthode que
    `prep_sub250.py` : aucune bibliothèque de simplification n'est disponible
    ici. Grossier, mais les STL de référence de `stl/` restent intacts."""
    snap = lambda v: (round(v[0] / cell) * cell, round(v[1] / cell) * cell,
                      round(v[2] / cell) * cell)
    out, seen = [], set()
    for t in tris:
        a, b, c = snap(t[0]), snap(t[1]), snap(t[2])
        if a == b or b == c or a == c:
            continue
        k = tuple(sorted((a, b, c)))
        if k in seen:
            continue
        seen.add(k)
        out.append((a, b, c))
    return out


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
    if viz:
        tris = cluster(tris, job["cell"])
    if job.get("trim_z") is not None:
        # l'antenne doit sortir centrée sur son axe, fourreau démarrant à z = 0
        lo, hi = bounds(tris)
        tris = shift(tris, (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))
    write_stl(path, tris)
    return tris, path


KEEP_REF = "--ref" in sys.argv


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(VIZ, exist_ok=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("Mesh.Binary", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    for job in JOBS:
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
    print("OASIS 30 — conversion des STEP DJI O4 Pro\n")
    main()
