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
pod_x       = 40;
pod_y       = 74;
pod_r       = 9;      // rounder corners — match body_bottom (was 6)
wall        = 1.5;    // was 1.6
top_h       = 11;     // canopy height
roof_t      = 1.2;    // was 1.4
cam_w       = 9;
arm_w       = 7.5;    // match the slimmer lower arms
arm_h_top   = 3.0;
snap_n      = 8;

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
        // camera window at the nose
        translate([0,-pod_y/2-eps,top_h*0.42])
            rotate([-90,0,0]) cylinder(d=cam_w+0.6, h=wall+3);
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

/* light covers over the four arm roots (cosmetic continuity with the body) */
module arm_caps() {
    for (sx=[-1,1], sy=[-1,1])
        hull() {
            translate([sx*(pod_x/2-5), sy*(pod_y/2-5), 0]) cylinder(d=arm_w, h=arm_h_top);
            translate([sx*motor_off*0.7, sy*motor_off*0.7, 0]) cylinder(d=arm_w-2, h=arm_h_top);
        }
}

module body_top() {
    canopy();
    arm_caps();
}

body_top();

echo(str("ASSERT span=", span_x, "x", span_y));
echo(str("ASSERT wheelbase=", wheelbase));
