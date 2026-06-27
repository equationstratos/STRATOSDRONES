// STRATOSDRONE — Tello-style canopy, FULLY-ROUNDED DOME variant.
//
// A third canopy option (alongside body_top.scad = vented, body_top_smooth.scad
// = smooth): a continuously-curved dome with NO flat crown. Same footprint,
// 4 corner snap clips and snap-retention battery cradle — but the cradle is
// CLIPPED to the dome envelope so it can never poke through / show on the
// surface. Print this instead of body_top.stl for the rounded look.
//
//   openscad -o stl/body_top_dome.stl --export-format binstl body_top_dome.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 72;
eps = 0.01;

/* ---------- shared geometry (keep in sync with body_bottom.scad) ---------- */
pod_x       = 42;
pod_y       = 78;
pod_r       = 9;
wall        = 1.5;
top_h       = 6.5;
roof_t      = 1.2;
snap_n      = 4;

/* 1S pack cradle — KEEP IN SYNC with body_top.scad / battery_dummy.scad */
batt_w      = 22;
batt_l      = 53;
batt_h      = 9.5;
batt_clear  = 0.6;
rail_t      = 1.6;

/* fully-rounded dome: hull of a thin rounded-rect base and a rounded ellipsoid
   cap — a continuous curve all the way up, no flat crown. `extra` insets it. */
module smooth_outer(extra) {
    hull() {
        linear_extrude(0.6)
            offset(pod_r - extra) square([pod_x-2*pod_r, pod_y-2*pod_r], center=true);
        translate([0,0, top_h - 4.5])
            resize([pod_x - 11 - 2*extra, pod_y - 13 - 2*extra, 9])
                sphere(r=10, $fn=80);
    }
}

module canopy_dome() {
    difference() {
        smooth_outer(0);                                // outer dome
        translate([0,0,-roof_t]) smooth_outer(wall);    // hollow + roof
        // fully rounded + smooth: no vents, no pipes, solid over the lens
    }
    // internal snap clips at the corners (match body_bottom posts)
    for (i = [0:snap_n-1]) {
        a = 45 + i*360/snap_n;
        rx = pod_x/2-2.2; ry = pod_y/2-2.2;
        translate([rx*cos(a), ry*sin(a), 0])
            difference() {
                cylinder(d=4.2, h=3);
                translate([0,0,-eps]) cylinder(d=2.35, h=3.2);
            }
    }
}

/* snap-retention battery cradle (identical to body_top.scad) */
module battery_cradle() {
    iw  = batt_w/2 + batt_clear;
    top =  top_h - roof_t;
    bot = -5;
    H   = top - bot;
    for (s = [-1,1]) {
        translate([s*(iw + rail_t/2), 0, bot])
            difference() {
                translate([-rail_t/2, -batt_l/2, 0]) cube([rail_t, batt_l, H]);
                for (k = [-1:1:1])
                    translate([0, k*15, H*0.55]) cube([rail_t+1, 9, H*0.5], center=true);
            }
        for (yy = [-batt_l/4, batt_l/4])
            translate([s*iw, yy, bot + 2.2]) sphere(r=0.9, $fn=18);
    }
    translate([0, -batt_l/2 - rail_t/2, bot + H/2]) cube([2*iw + 2*rail_t, rail_t, H], center=true);
}

module body_top_dome() {
    canopy_dome();
    // keep the cradle, but CLIP it to the dome envelope (just inside the outer
    // surface) above the rim, and keep it whole below the rim (in the pod) — so
    // it grips the pack yet never pokes through the smooth dome.
    intersection() {
        battery_cradle();
        union() {
            smooth_outer(0.5);                              // inside the outer skin
            translate([0,0,-12]) linear_extrude(12 + eps)   // keep everything below z=0
                offset(pod_r) square([pod_x-2*pod_r, pod_y-2*pod_r], center=true);
        }
    }
}

body_top_dome();
