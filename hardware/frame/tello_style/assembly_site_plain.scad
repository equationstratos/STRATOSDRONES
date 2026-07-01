// STRATOSDRONE — frame + capot only (no guards), for site/README renders.
// Plain colored assembly for iso/top/front/side/underside product shots.
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
use <body_bottom_v2.scad>
use <body_top_v2.scad>

color("#9298a3") body_bottom_v2();
color("#2f6fed") translate([0,0,13]) capot();

// camera lens detail (semi-final look) — a dark barrel just inside the nose
// hole (translate([0,-pod_y/2-eps,half_h*0.5]) in body_bottom_v2.scad; pod_y=78,
// half_h=13) with a small glass glint.
translate([0,-38,6.5]) rotate([90,0,0]) {
    color("#101216") cylinder(d=8, h=3, $fn=32);
    color("#3a4a63") translate([0,0,2.4]) cylinder(d=4.6, h=0.6, $fn=32);
}
