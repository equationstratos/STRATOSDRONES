// STRATOSDRONE — frame + capot only (no guards), for site/README renders.
// Plain colored assembly for iso/top/front/side/underside product shots.
//
// SHOW_BODY / SHOW_CAPOT let this file render as two separate clean layers
// (`-D SHOW_CAPOT=false` / `-D SHOW_BODY=false`), composited afterwards in
// Python — see assembly_site.scad's header for why.
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
use <body_bottom_v2.scad>
use <body_top_v2.scad>

SHOW_BODY  = true;
SHOW_CAPOT = true;

if (SHOW_BODY) color("#9298a3") body_bottom_v2();
if (SHOW_CAPOT) color("#2f6fed") translate([0,0,13]) capot();

if (SHOW_BODY) {
    // camera lens detail (semi-final look) — a dark barrel flush with the nose
    // hole's outer face (not protruding past the front wall, ~y=-39; hole is
    // translate([0,-pod_y/2-eps,half_h*0.5]) in body_bottom_v2.scad; pod_y=78,
    // half_h=13) with a small glass glint.
    translate([0,-36,6.5]) rotate([90,0,0]) {
        color("#101216") cylinder(d=8, h=3, $fn=32);
        color("#3a4a63") translate([0,0,2.4]) cylinder(d=4.6, h=0.6, $fn=32);
    }
}
