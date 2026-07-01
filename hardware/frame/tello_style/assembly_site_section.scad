// STRATOSDRONE — side x-ray: battery riding ON TOP of the board, shown through
// a translucent shell (avoids OpenSCAD's cut-face colour loss on booleans).
// For site/README renders only — do not print.
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
use <body_bottom_v2.scad>
use <body_top_v2.scad>

board_top = 5.8;
batt_w = 22; batt_l = 53; batt_h = 9.5;

color("#9298a3", 0.35) body_bottom_v2();
color("#2f6fed", 0.30) translate([0,0,13]) capot();
// mainboard stand-in (green PCB plate)
color("#0f7a3d") translate([0,0,4.2]) linear_extrude(1.6) offset(2) square([38-4,74-4], center=true);
// 1S pack resting on the board
color("#2247c4") translate([0,10,board_top+batt_h/2]) cube([batt_w,batt_l,batt_h], center=true);
