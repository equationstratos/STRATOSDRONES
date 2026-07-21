#!/usr/bin/env python3
"""Convert the JeNo Pocket V2 STEP to a light binary STL for the 3-D viewer.

The viewer (../../viz/) embeds STL, not STEP, so this tessellates the real
CAD once with gmsh (OpenCASCADE) into ../stl/frame_real.stl. Re-run only if
you replace the STEP.

    pip install gmsh            # self-contained wheel (needs libXft on Linux)
    python3 step_to_stl.py     # -> ../stl/frame_real.stl

SPDX-License-Identifier: CC-BY-4.0  (see ATTRIBUTION.md — the geometry is
WE are FPV's JeNo Pocket V2; this script only meshes it).
"""
import os
import gmsh

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "JeNoPocket_V2.step")
OUT = os.path.join(HERE, "..", "stl", "frame_real.stl")

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.add("jeno")
gmsh.model.occ.importShapes(SRC)
gmsh.model.occ.synchronize()

bb = gmsh.model.getBoundingBox(-1, -1)
print("frame size: %.1f x %.1f x %.1f mm" % (bb[3]-bb[0], bb[4]-bb[1], bb[5]-bb[2]))

gmsh.option.setNumber("Mesh.Binary", 1)          # compact STL
gmsh.option.setNumber("Mesh.MeshSizeMax", 2.6)   # coarse enough for a viewer
gmsh.option.setNumber("Mesh.MeshSizeMin", 0.35)
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.model.mesh.generate(2)
gmsh.write(OUT)
gmsh.finalize()
print("wrote", os.path.relpath(OUT, HERE), os.path.getsize(OUT) // 1024, "KiB")
