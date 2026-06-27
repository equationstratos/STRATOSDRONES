// STRATOSDRONE Tello-style — both printed shells assembled, for the 3D viewer.
// (No motors/props — just the printable frame.) SPDX: CERN-OHL-P-2.0
use <body_bottom.scad>
use <body_top.scad>
body_bottom();
translate([0,0,13.2]) body_top();
