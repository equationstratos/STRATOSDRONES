// STRATOSDRONE — frame + capot only (no guards), for site/README renders.
// Plain colored assembly for iso/top/front/side/underside product shots.
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
use <body_bottom_v2.scad>
use <body_top_v2.scad>

color("#9298a3") body_bottom_v2();
color("#2f6fed") translate([0,0,13]) capot();
