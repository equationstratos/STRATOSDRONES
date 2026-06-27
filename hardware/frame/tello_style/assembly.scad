// STRATOSDRONE Tello-style — full assembly preview (visual only, not for print).
// Renders the bottom shell + top canopy + 4 motors + 3" prop disks so the
// proportions read at a glance. Print body_bottom.scad and body_top.scad.
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
wheelbase  = 118;
motor_off  = wheelbase/2/sqrt(2);
prop_d     = 76.2;
motor_lift = 1;          // keep in sync with body_bottom.scad (low motors)

use <body_bottom.scad>
use <body_top.scad>

color("DimGray") body_bottom();
color("DarkOrange", 0.92) translate([0,0,13.2]) body_top();

for (sx=[-1,1], sy=[-1,1]) {
    translate([sx*motor_off, sy*motor_off, motor_lift + 1.4]) {
        color("Silver") cylinder(d=8.5, h=18);                 // motor
        cw = (sx*sy > 0);
        color(cw ? "DarkOrange" : "DimGray", 0.35)
            translate([0,0,18.5]) cylinder(d=prop_d, h=1.2);   // prop disk
    }
}
