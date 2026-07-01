// STRATOSDRONE — frame + capot + real Tello prop guards, for site renders only.
// Mirrors the FINAL placement baked into sim/viz/gen_viewer.py's guard block:
// clip recentred on its bore, +20% scale, 4mm off the nacelle's foot, nudged
// 9mm out along the motor radius (clip lands on the arm, clear of the arm
// beam and the motor can — dialled in by hand via the viewer's live panel).
//
// SHOW_BODY / SHOW_CAPOT let this file render as two separate clean layers
// (`-D SHOW_CAPOT=false` / `-D SHOW_BODY=false`) that get composited in
// Python afterwards — OpenSCAD's preview ("thrown together") mode dithers
// between the body's and capot's colours where their surfaces are close/
// touching, and this OpenSCAD build (2021.01) drops per-object colour
// entirely under `--render`/`render()`, so two clean single-pass renders +
// a compositing step is the reliable fix. Default both true for normal use
// (e.g. opening this file directly in the GUI).
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
use <body_bottom_v2.scad>
use <body_top_v2.scad>

SHOW_BODY   = true;
SHOW_CAPOT  = true;
CAPOT_COLOR = "#2f6fed";   // configurator swatches override via -D CAPOT_COLOR='"#rrggbb"'

wheelbase = 118;
motor_off = wheelbase/2/sqrt(2);
MOTORS = [for (sx=[-1,1], sy=[-1,1]) [sx,sy]];

if (SHOW_BODY) color("#9298a3") body_bottom_v2();
if (SHOW_CAPOT) color(CAPOT_COLOR) translate([0,0,13]) capot();

if (SHOW_BODY) {
    // camera lens detail (semi-final look) — a dark barrel flush with the nose
    // hole's outer face (not protruding past the front wall, ~y=-39).
    translate([0,-36,6.5]) rotate([90,0,0]) {
        color("#101216") cylinder(d=8, h=3, $fn=32);
        color("#3a4a63") translate([0,0,2.4]) cylinder(d=4.6, h=0.6, $fn=32);
    }

    for (m = MOTORS) {
        mx = m[0]*motor_off; my = m[1]*motor_off;
        a = atan2(my, mx);
        color("#2b2e33")
            translate([mx + 9*cos(a), my + 9*sin(a), 4])
                rotate([0,0,a])
                    scale([1.2,1.2,0.69])
                        import("../../../sim/viz/guard.stl");

        // 8520 motor pressed into the pod — can + top bell, matching gen_viewer.py's
        // frame-mode motor (zcyl 8.5mm dia x 20mm can, 8.8/8.0mm x 5mm bell on top).
        color("#474d57") translate([mx,my,10]) cylinder(d=8.5, h=20, center=true, $fn=32);
        color("#2b303a") translate([mx,my,19.5]) cylinder(d1=8.8, d2=8.0, h=5, center=true, $fn=32);

        // real Tello prop (38.1mm radius, hub at origin) — front pair matches the
        // capot colour, rear pair dark, matching sim/viz/gen_viewer.py's buildProp().
        front = (m[1] < 0);                 // nose is -Y (camera hole side)
        cw    = (m[0] > 0) == (m[1] < 0);   // same rule as gen_viewer.py
        color(front ? CAPOT_COLOR : "#20242c")
            translate([mx, my, 20.5])
                scale([1, cw ? 1 : -1, 1])   // mirror Y for CCW props
                    import("../../../sim/viz/prop.stl");
    }
}
