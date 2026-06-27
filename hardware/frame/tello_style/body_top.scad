// STRATOSDRONE — Tello-style closed-body shell, UPPER half (canopy).
//
// Snaps onto body_bottom.scad. Covers the pod and the four arm roots, holds
// the camera window at the nose, vents the electronics with a hex pattern,
// and carries two LED light pipes.
//
// LIGHTWEIGHT revision: rounder pod corners, thinner walls/roof and a wider
// hex vent field to drop mass while keeping the faceted-canopy look.
//
//   openscad -o stl/body_top.stl --export-format binstl body_top.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 72;
eps = 0.01;

/* ---------- shared geometry (keep in sync with body_bottom.scad) ---------- */
span_x      = 98;
span_y      = 92.5;
wheelbase   = 118;
motor_off   = wheelbase/2/sqrt(2);
pod_x       = 42;     // match body_bottom (sized to the real 38x74 PCB)
pod_y       = 78;
pod_r       = 9;      // rounder corners — match body_bottom (was 6)
wall        = 1.5;    // was 1.6
top_h       = 11;     // canopy height
roof_t      = 1.2;    // was 1.4
cam_w       = 9;
snap_n      = 8;

/* 1S pack, carried on top of the board by a cradle under the canopy */
batt_w      = 27;     // pack width
batt_l      = 53;     // pack length
batt_clear  = 0.6;    // fit clearance per side
rail_t      = 1.5;    // cradle wall thickness

module rrect(x, y, r, h) {
    linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true);
}

/* faceted canopy crown: pod shell tapering inward toward the top */
module canopy() {
    difference() {
        hull() {
            rrect(pod_x, pod_y, pod_r, eps);                          // base
            translate([0,0,top_h]) rrect(pod_x-12, pod_y-14, 8, eps); // crown
        }
        // hollow
        hull() {
            translate([0,0,-eps]) rrect(pod_x-2*wall, pod_y-2*wall, max(pod_r-wall,1), eps);
            translate([0,0,top_h-roof_t]) rrect(pod_x-12-2*wall, pod_y-14-2*wall, 7, eps);
        }
        // (no camera window here — the camera exits through the lower shell's
        //  nose bump, so the canopy stays solid above the lens)
        // wider hex vent field on the crown (lighter + Tello-vented look)
        for (ix=[-2:2], iy=[-2:2])
            if (abs(ix)+abs(iy) <= 3)
                translate([ix*7.6, iy*7.6, top_h-roof_t-eps])
                    cylinder(r=3.1/sqrt(3)*2, h=roof_t+2*eps, $fn=6);
        // two LED light pipes (front corners)
        for (s=[-1,1])
            translate([s*(pod_x/2-9), -pod_y/2+8, top_h-roof_t-eps])
                cylinder(d=3.2, h=roof_t+2*eps);
    }
    // internal snap clips matching body_bottom posts
    for (i=[0:snap_n-1]) {
        a = i*360/snap_n;
        rx = pod_x/2-2.2; ry = pod_y/2-2.2;
        translate([rx*cos(a), ry*sin(a), 0])
            difference() {
                cylinder(d=4.2, h=3);
                translate([0,0,-eps]) cylinder(d=2.35, h=3.2);
            }
    }
}

/* Integrated battery cradle: brackets the 1S pack (sitting on top of the board)
   from inside the canopy — two side rails + a rear stop + a front retaining lip.
   It grips the pack laterally and fore-aft; the closed canopy holds it down.
   Lightening windows keep the rails from adding much mass. */
module battery_cradle() {
    iw   = batt_w/2 + batt_clear;        // inner half-width
    h    = top_h - roof_t;               // hang from the roof down to the pod rim
    // two side rails with lightening windows
    for (s = [-1,1])
        translate([s*(iw + rail_t/2), 0, 0])
            difference() {
                translate([-rail_t/2, -batt_l/2, 0]) cube([rail_t, batt_l, h]);
                for (k = [-1.5:1:1.5])
                    translate([-rail_t/2-eps, k*12, h*0.5])
                        cube([rail_t+2*eps, 7, h*0.55], center=true);
            }
    // rear stop wall
    translate([-iw-rail_t, batt_l/2, 0]) cube([2*(iw+rail_t), rail_t, h]);
    // front retaining lip (low, leaves room for the battery lead)
    translate([-iw*0.6, -batt_l/2 - rail_t, 0]) cube([iw*1.2, rail_t, h*0.55]);
}

module body_top() {
    canopy();           // pod cover — the arms live on the lower shell
    battery_cradle();   // holds the 1S pack on top of the board
}

body_top();

echo(str("ASSERT span=", span_x, "x", span_y));
echo(str("ASSERT wheelbase=", wheelbase));
