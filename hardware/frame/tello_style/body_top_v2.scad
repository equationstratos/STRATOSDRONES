// STRATOSDRONE — Tello-style canopy V2 (capot) for body_bottom_v2.
//
// A smooth low capot to match the v2 lower shell: rounded shell, solid over the
// lens, with a REAR opening + side guide rails so the 1S pack slides in from
// the back (no need to pull the capot), a front stop, and the 4 corner snap
// clips. Lowered motors -> props clear just above this capot.
//
//   openscad -o stl/body_top_v2.stl --export-format binstl body_top_v2.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 72;
eps = 0.01;

pod_x = 42; pod_y = 78; pod_r = 9; wall = 1.5;
top_h = 4.5;   // low capot (props clear just above)
roof_t = 1.2; snap_n = 4;

/* 1S pack — keep in sync with body_bottom_v2 / battery_dummy */
batt_w = 22; batt_l = 53; batt_h = 9.5; batt_clear = 0.6; rail_t = 1.6;
// the pack sits on the board (abs top 5.8..15.3); this capot's z=0 is the pod
// joint (abs 13), so the pack reaches batt-local +2.3 and down into the pod.

/* low smooth dome, ellipsoid cap — no flat crown. `extra` insets it. */
module capot_outer(extra) {
    hull() {
        linear_extrude(0.6)
            offset(pod_r - extra) square([pod_x-2*pod_r, pod_y-2*pod_r], center=true);
        translate([0,0, top_h - 3])
            resize([pod_x - 10 - 2*extra, pod_y - 12 - 2*extra, 7])
                sphere(r=10, $fn=72);
    }
}

/* rear battery passage — opens the rear-bottom so the pack slides in */
module rear_slot() {
    translate([0, pod_y/2, batt_h/2 - 4]) cube([batt_w+1.6, 36, batt_h+1], center=true);
}

/* side guide rails (descend into the pod) + a front stop — channel the pack.
   The capot joins the pod at abs z=13 (= capot-local 0). The rails grip the pack
   only DOWN TO the board top (abs ≈ 6.5, capot-local ≈ -6.5) so they clear the
   board — they no longer reach to abs 4 and drag the pack under the board. */
rail_bot = -6.5;   // capot-local; abs 6.5 — just above the board top
rail_top =  2.5;   // capot-local; abs 15.5 — grips up near the pack top
module battery_guides() {
    iw = batt_w/2 + batt_clear; rh = rail_top - rail_bot; rz = (rail_top+rail_bot)/2;
    for (s = [-1,1])
        translate([s*(iw + rail_t/2), 0, rz])
            cube([rail_t, batt_l+4, rh], center=true);
    // front stop (nose side); rear stays open for sliding in + the lead
    translate([0, -batt_l/2 - rail_t/2, rz]) cube([2*iw + 2*rail_t, rail_t, rh], center=true);
    // a small retention nub each side near the rear, so the pack clicks in
    for (s = [-1,1])
        translate([s*iw, batt_l/2 - 5, rail_bot + 1.5]) sphere(r=0.9, $fn=18);
}

module capot() {
    difference() {
        capot_outer(0);
        translate([0,0,-roof_t]) capot_outer(wall);    // hollow + roof
        rear_slot();                                    // rear battery opening
    }
    // battery guides (clipped to stay inside the capot envelope)
    intersection() {
        battery_guides();
        union() {
            capot_outer(0.5);
            translate([0,0,-14]) linear_extrude(14+eps)
                offset(pod_r) square([pod_x-2*pod_r, pod_y-2*pod_r], center=true);
        }
    }
    // corner snap clips (match body_bottom_v2 posts)
    for (i = [0:snap_n-1]) {
        a = 45 + i*360/snap_n; rx = pod_x/2-2.2; ry = pod_y/2-2.2;
        translate([rx*cos(a), ry*sin(a), 0]) difference() {
            cylinder(d=4.2, h=3);
            translate([0,0,-eps]) cylinder(d=2.35, h=3.2);
        }
    }
}

capot();
