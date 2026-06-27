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
top_h       = 6.5;    // lower canopy — props (on the LOW motors) clear above it
roof_t      = 1.2;    // was 1.4
cam_w       = 9;
snap_n      = 4;      // 4 corner clips only (the 4 edge-mid "ears" are gone)

/* 1S pack, carried on top of the board by a cradle under the canopy.
   Default ≈ a Tello-class 1S 1100 mAh LiHV pack — KEEP IN SYNC with
   battery_dummy.scad and ADJUST to your real pack before the final print. */
batt_w      = 22;     // pack width
batt_l      = 53;     // pack length
batt_h      = 9.5;    // pack thickness
batt_clear  = 0.6;    // fit clearance per side
rail_t      = 1.6;    // cradle wall thickness

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
    // internal snap clips matching body_bottom posts (corners only)
    for (i=[0:snap_n-1]) {
        a = 45 + i*360/snap_n;
        rx = pod_x/2-2.2; ry = pod_y/2-2.2;
        translate([rx*cos(a), ry*sin(a), 0])
            difference() {
                cylinder(d=4.2, h=3);
                translate([0,0,-eps]) cylinder(d=2.35, h=3.2);
            }
    }
}

/* Integrated battery cradle with a SNAP retention so the pack can't fall out.
   Two side rails reach down from the roof into the pod to bracket the pack
   sitting on the board; small detent bumps near the open end snap over the
   pack so you can clip it into the canopy, flip it, and the pack stays put.
   Front stop locates it; the rear is open for the lead to J1. */
module battery_cradle() {
    iw  = batt_w/2 + batt_clear;     // inner half-width
    top =  top_h - roof_t;           // roof (canopy-local z)
    bot = -5;                         // reach down into the pod to grip the pack
    H   = top - bot;
    for (s = [-1,1]) {
        // side rail (lightening windows keep it from adding mass)
        translate([s*(iw + rail_t/2), 0, bot])
            difference() {
                translate([-rail_t/2, -batt_l/2, 0]) cube([rail_t, batt_l, H]);
                for (k = [-1:1:1])
                    translate([0, k*15, H*0.55]) cube([rail_t+1, 9, H*0.5], center=true);
            }
        // two snap detents per rail near the open end → retain the pack
        for (yy = [-batt_l/4, batt_l/4])
            translate([s*iw, yy, bot + 2.2]) sphere(r=0.9, $fn=18);
    }
    // front stop wall (nose side); rear left open for the battery lead
    translate([0, -batt_l/2 - rail_t/2, bot + H/2]) cube([2*iw + 2*rail_t, rail_t, H], center=true);
}

module body_top() {
    canopy();           // pod cover — the arms live on the lower shell
    battery_cradle();   // holds the 1S pack on top of the board
}

body_top();

echo(str("ASSERT span=", span_x, "x", span_y));
echo(str("ASSERT wheelbase=", wheelbase));
