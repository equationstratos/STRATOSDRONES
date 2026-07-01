// STRATOSDRONE — exploded preview: capot lifted off, 1S battery floating over
// the honeycomb floor. For site/README renders only — do not print.
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
use <body_bottom_v2.scad>
use <body_top_v2.scad>

board_top = 5.8;      // battery floor (see body_bottom_v2.scad)
batt_w = 22; batt_l = 53; batt_h = 9.5;

color("#9298a3") body_bottom_v2();

// 1S pack, floating just above its resting height on the honeycomb floor
color("#2247c4")
    translate([0, 10, board_top + 14])
        minkowski() {
            cube([batt_w-3.2, batt_l-3.2, batt_h-3.2], center=true);
            sphere(r=1.6, $fn=24);
        }

// capot, lifted well clear
color("#2f6fed") translate([0,0,13+38]) capot();
