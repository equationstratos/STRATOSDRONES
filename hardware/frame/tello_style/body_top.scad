// STRATOSDRONE — Tello-style closed-body shell, UPPER half (canopy).
//
// Snaps onto body_bottom.scad. Covers the pod and the four arm roots, holds
// the camera window at the nose, vents the electronics with a hex pattern,
// and carries two LED light pipes. Visually distinct from the Tello: faceted
// canopy crown + hex vents.
//
//   openscad -o stl/body_top.stl --export-format binstl body_top.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;
eps = 0.01;

/* ---------- shared geometry (keep in sync with body_bottom.scad) ---------- */
span_x      = 98;
span_y      = 92.5;
wheelbase   = 118;
motor_off   = wheelbase/2/sqrt(2);
nacelle_d   = 15;
pod_x       = 36;
pod_y       = 70;
wall        = 1.6;
top_h       = 11;     // canopy height
roof_t      = 1.4;
cam_w       = 9;
arm_w       = 9;
arm_h_top   = 3.0;
snap_n      = 8;

module rrect(x, y, r, h) {
    linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true);
}

/* faceted canopy crown: pod shell tapering inward toward the top */
module canopy() {
    difference() {
        hull() {
            rrect(pod_x, pod_y, 6, eps);                              // base
            translate([0,0,top_h]) rrect(pod_x-12, pod_y-14, 8, eps); // crown
        }
        // hollow
        difference() {
            hull() {
                translate([0,0,-eps]) rrect(pod_x-2*wall, pod_y-2*wall, 5, eps);
                translate([0,0,top_h-roof_t]) rrect(pod_x-12-2*wall, pod_y-14-2*wall, 7, eps);
            }
        }
        // camera window at the nose
        translate([0,-pod_y/2-eps,top_h*0.42])
            rotate([-90,0,0]) cylinder(d=cam_w+0.6, h=wall+3);
        // hex vent field on the crown
        for (ix=[-2:2], iy=[-2:2])
            if (abs(ix)+abs(iy) <= 3)
                translate([ix*7.5, iy*7.5, top_h-roof_t-eps])
                    cylinder(r=2.6/sqrt(3)*2, h=roof_t+2*eps, $fn=6);
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
            translate([sx*(pod_x/2-6), sy*(pod_y/2-6), 0]) cylinder(d=arm_w, h=arm_h_top);
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
