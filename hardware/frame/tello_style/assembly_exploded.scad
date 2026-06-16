// STRATOSDRONE Tello-style — EXPLODED assembly preview (visual only).
// Shows the clamshell stack: canopy on top, the 36x70 mainboard in the
// middle, the lower shell with motors + props below. For the project website.
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
wheelbase = 118;
motor_off = wheelbase/2/sqrt(2);
prop_d    = 76.2;
exp       = 42;   // explosion gap

use <body_bottom.scad>
use <body_top.scad>

// lower shell + motors + props
color("DimGray") body_bottom();
for (sx=[-1,1], sy=[-1,1]) {
    translate([sx*motor_off, sy*motor_off, 1.4]) {
        color("Silver") cylinder(d=8.5, h=18);
        cw = (sx*sy > 0);
        color(cw ? "DarkOrange" : "#303030", 0.45)
            translate([0,0,18.5]) cylinder(d=prop_d, h=1.2);
    }
}

// mainboard (stand-in: a thin rounded plate 36x70 with a camera bump)
translate([0,0,exp*0.55]) color("#0b6b3a") {
    linear_extrude(1.6) offset(4) square([36-8,70-8], center=true);
    translate([0,-31,1.6]) cylinder(d=7,h=2);          // camera at the nose
}

// canopy on top
translate([0,0,exp*1.15]) color("DarkOrange", 0.95) body_top();
