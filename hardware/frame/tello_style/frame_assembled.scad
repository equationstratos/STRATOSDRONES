// STRATOSDRONE Tello-style — both printed shells assembled, for the 3D viewer.
// (No motors/props — just the printable frame.) Uses the current V2 shells:
// double lattice/twin arms, rear-loading battery (on top of the board), clean
// camera hole. SPDX: CERN-OHL-P-2.0
$fn = 20;                       // low-poly for the web viewer
use <body_bottom_v2.scad>
use <body_top_v2.scad>
body_bottom_v2();
translate([0,0,13]) capot();    // capot joins the pod rim at z=13
