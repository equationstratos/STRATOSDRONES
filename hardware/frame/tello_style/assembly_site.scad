// STRATOSDRONE — frame + capot + real Tello prop guards, for site renders only.
// Mirrors the placement used in sim/viz/gen_viewer.py's guard block (clip
// recentred on its bore, +20% scale, z=3.5mm, on the motor axis).
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
use <body_bottom_v2.scad>
use <body_top_v2.scad>

wheelbase = 118;
motor_off = wheelbase/2/sqrt(2);
MOTORS = [for (sx=[-1,1], sy=[-1,1]) [sx,sy]];

color("#9298a3") body_bottom_v2();
color("#e6730d") translate([0,0,13]) capot();

for (m = MOTORS) {
    mx = m[0]*motor_off; my = m[1]*motor_off;
    a = atan2(my, mx);
    color("#2b2e33")
        translate([mx, my, 3.5])
            rotate([0,0,a])
                scale([1.2,1.2,0.69])
                    import("../../../sim/viz/guard.stl");
}
