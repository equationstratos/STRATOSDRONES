// STRATOSDRONE — Tello-style canopy, SMOOTH variant (alternative to body_top).
//
// Same footprint, snaps + battery cradle as body_top.scad, but the crown is a
// clean curved dome with NO hex vents and NO LED pipes — a smooth, closed shell.
// (Ventilation is handled by the honeycomb floor in body_bottom.scad, so the
// top can stay solid.) Print this instead of body_top.stl if you prefer the
// smooth look.
//
//   openscad -o stl/body_top_smooth.stl --export-format binstl body_top_smooth.scad
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
snap_n      = 4;      // 4 corner clips (no edge-mid "ears")

/* 1S pack cradle — KEEP IN SYNC with body_top.scad / battery_dummy.scad */
batt_w      = 22;
batt_l      = 53;
batt_h      = 9.5;
batt_clear  = 0.6;
rail_t      = 1.6;

module rrect(x, y, r, h) {
    linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true);
}

/* a smooth domed shell layer-stack following a cosine profile (no facets read
   at this resolution). `extra` insets the section (for the hollow). */
module smooth_shell(h, extra) {
    isq = [pod_x-2*pod_r, pod_y-2*pod_r];
    n = 7; shrink = 11;
    hull() for (i = [0:n]) {
        t = i/n;
        translate([0,0,h*t]) linear_extrude(eps)
            offset(pod_r - shrink*(1 - cos(t*90)) - extra) square(isq, center=true);
    }
}

/* smooth canopy: domed solid shell + the 4 corner snap clips */
module canopy_smooth() {
    difference() {
        smooth_shell(top_h, 0);                         // outer dome
        translate([0,0,-1]) smooth_shell(top_h - roof_t + 1, wall);  // hollow
        // smooth: no hex vents, no LED pipes, solid over the camera lens
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

/* Integrated battery cradle (identical to body_top.scad): snap retention so
   the pack clips in and won't fall when the canopy is flipped. */
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

module body_top_smooth() {
    canopy_smooth();
    battery_cradle();
}

body_top_smooth();
