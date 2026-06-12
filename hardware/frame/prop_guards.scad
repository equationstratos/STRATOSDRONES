// Clip-on prop guards (one per corner) — Tello-style, print 4x in PETG.
// Clips onto the 8520 motor pocket sleeve of frame.scad.
// SPDX-License-Identifier: CERN-OHL-P-2.0

prop_d      = 76.2;   // 3" prop
guard_gap   = 4.5;    // radial gap prop tip -> guard
ring_w      = 2.4;
ring_h      = 7;
clip_d      = 8.5 + 0.3 + 1.6 * 2;  // matches motor pocket OD
clip_h      = 8;
spoke_w     = 3.2;

$fn = 96;
eps = 0.01;
guard_r = prop_d / 2 + guard_gap;

module guard() {
    // 270-degree ring (open toward the hub side, like the Tello guard)
    rotate_extrude(angle = 270)
        translate([guard_r, 0]) square([ring_w, ring_h]);
    rotate([0, 0, 135]) {
        // clip collar
        difference() {
            cylinder(d = clip_d + 2.4, h = clip_h);
            translate([0, 0, -eps]) cylinder(d = clip_d + 0.25, h = clip_h + 2 * eps);
            // clip slot for elasticity
            translate([-1.25, 0, -eps]) cube([2.5, clip_d, clip_h + 2 * eps]);
        }
        // three spokes from collar to ring
        for (a = [-80, 0, 80]) rotate([0, 0, a])
            translate([clip_d / 2, -spoke_w / 2, 0])
                cube([guard_r - clip_d / 2 + ring_w / 2, spoke_w, 3]);
    }
}

rotate([0, 0, -135]) guard();
echo(str("ASSERT guard_outer_d=", 2 * (guard_r + ring_w)));
