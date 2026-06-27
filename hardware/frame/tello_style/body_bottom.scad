// STRATOSDRONE — Tello-style closed-body shell, LOWER half (structural).
//
// Same footprint class as a DJI Tello (≈98 × 92.5 mm, 118 mm wheelbase, 3"
// props) but visually distinct. This is the bottom clamshell — it carries the
// PCB, the four arms, the motor mounts and the bottom sensor window. Pair with
// body_top.scad.
//
// LIGHTWEIGHT revision: round thin-wall motor mounts (was solid hex blocks),
// slimmer tapered arms, smoother rounder pod, thinner walls/floor — a lighter
// and more Tello-like shell. See README for the measured mass.
//
//   openscad -o stl/body_bottom.stl --export-format binstl body_bottom.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 72;
eps = 0.01;

/* ---------- shared geometry (keep in sync with body_top.scad) ---------- */
span_x      = 98;     // overall width  (left-right), incl. motors
span_y      = 92.5;   // overall length (front-back), incl. motors
wheelbase   = 118;    // motor-to-motor diagonal
motor_off   = wheelbase/2/sqrt(2);   // 41.72 mm in x and y
motor_d     = 8.5;    // 8520 motor diameter

/* ---- lightweight tuning (the levers that set the printed mass) ---- */
nacelle_wall = 1.9;                          // wall around the press-fit motor
nacelle_d    = motor_d + 2*nacelle_wall + 0.4;   // ≈12.7 round mount (was hex 15)
motor_grip   = 12;                           // pocket depth gripping the motor (was 16)
floor_t      = 1.2;                           // pod floor (was 1.4)
nacelle_h    = motor_grip + floor_t;          // ≈13.2 → flush with the pod, no tall blocks
// PCB envelope — AUTHORITATIVE values from hardware/pcb design.py BOARD
// (w=38, h=74, mount_pitch 28x64). The pod is sized to seat this board.
pcb_x       = 38;     // real mainboard width  (was a stale 36)
pcb_y       = 74;     // real mainboard length (was a stale 70)
pcb_hole    = 28;     // M2 mount pitch X (was a stale 26)
pcb_hole_y  = 64;     // M2 mount pitch Y (was a stale 60)
pcb_clear   = 0.5;    // wall-to-board clearance per side (drop-in fit)
boss_h      = 3.0;    // standoff: PCB sits at floor_t+boss_h, bottom sensors
                      // (U8 ToF + U9 flow, side B) clear the floor + window

pod_x        = pcb_x + 2*pcb_clear + 2*1.5;   // ≈42 — inner just clears the board
pod_y        = pcb_y + 2*pcb_clear + 2*1.5;   // ≈78
pod_r        = 9;     // corner radius — rounder, Tello-smooth (was 6)
wall         = 1.5;   // pod side wall (was 1.6); inner walls locate the board
half_h       = 13;    // height of the lower shell (keep: assembly offset)
arm_w        = 7.5;   // arm root width  (slimmer, was 9)
arm_w_tip    = 6.0;   // arm width at the motor (taper → sleeker + lighter)
arm_h        = 5.0;   // arm thickness (was 6)

sensor_win  = 16;     // flow + ToF window
cam_w       = 9;      // camera barrel
snap_n      = 8;

module rrect(x, y, r, h) {            // rounded rect prism, centered
    linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true);
}

/* central pod outer wall + floor */
module pod_shell() {
    difference() {
        rrect(pod_x, pod_y, pod_r, half_h);
        // hollow interior
        translate([0,0,floor_t])
            rrect(pod_x-2*wall, pod_y-2*wall, max(pod_r-wall,1), half_h);
        // bottom sensor window (flow + ToF look straight down; long enough to
        // clear both U8/U9 which are spaced along the board spine)
        translate([0,3,-eps]) rrect(sensor_win, sensor_win+10, 2, floor_t+2*eps);
        // camera aperture at the front nose (-y)
        translate([0,-pod_y/2-eps,half_h*0.5])
            rotate([-90,0,0]) cylinder(d=cam_w+0.6, h=wall+2);
        // USB-C slot on the LEFT side wall, forward of centre
        translate([-pod_x/2-eps,-15,2.5]) cube([wall+2,12,5.5]);
        // two slim under-floor vent slots at the rear (lighten + airflow)
        for (s=[-1,1])
            translate([s*9, pod_y/2-12, -eps]) rrect(4, 16, 2, floor_t+2*eps);
    }
    // smooth chamfered camera nose bump
    translate([0,-pod_y/2+1,half_h*0.5])
        rotate([-90,0,0])
            difference() {
                cylinder(d=cam_w+5, h=3.5);
                translate([0,0,-eps]) cylinder(d=cam_w+0.5, h=4);
                translate([-cam_w,-cam_w-2,-eps]) cube([2*cam_w,cam_w+2,5]);
            }
}

/* one slim tapered arm + ROUND thin-wall motor mount at corner (sx, sy) */
module arm(sx, sy) {
    ang = atan2(sy, sx);
    // tapered arm bridge from pod edge to motor (wide root → slim tip)
    hull() {
        translate([sx*(pod_x/2-5), sy*(pod_y/2-5), 0]) cylinder(d=arm_w, h=arm_h);
        translate([sx*motor_off, sy*motor_off, 0]) cylinder(d=arm_w_tip, h=arm_h);
    }
    // round nacelle: a light conical collar holding the press-fit motor
    translate([sx*motor_off, sy*motor_off, 0]) {
        difference() {
            cylinder(d1=nacelle_d, d2=nacelle_d-1, h=nacelle_h);   // slim taper
            translate([0,0,floor_t]) cylinder(d=motor_d+0.15, h=nacelle_h);  // motor pocket
            cylinder(d=motor_d-3, h=nacelle_h*3, center=true);     // bottom wire/vent hole
            // wire channel toward the pod
            rotate([0,0,ang+180]) translate([0,-1.5,floor_t]) cube([nacelle_d, 3, nacelle_h]);
        }
    }
}

/* PCB mounting bosses (4) inside the pod, at the 26 x 60 mm hole pitch */
module pcb_bosses() {
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*pcb_hole/2, sy*pcb_hole_y/2, floor_t-eps])
            difference() {
                cylinder(d=6, h=boss_h);
                translate([0,0,0.8]) cylinder(d=1.7, h=boss_h);   // M2 self-tap
            }
}

// NOTE: the 1S pack mounts on TOP of the board (under the canopy), not on the
// floor — the board fills the pod and its bottom-side sensors (U8 ToF, U9 flow)
// must see straight down through the floor window, so nothing sits beneath it.
// (The old floor battery rails were removed: they collided with the real-size
//  board.) A canopy-side battery cradle can be added to body_top if wanted.

/* snap posts around the pod rim to receive body_top */
module snap_posts() {
    for (i=[0:snap_n-1]) {
        a = i*360/snap_n;
        rx = pod_x/2-2.2; ry = pod_y/2-2.2;
        x = rx*cos(a); y = ry*sin(a);
        translate([x,y,half_h-2.4]) cylinder(d=2.2, h=2.4);
    }
}

module body_bottom() {
    pod_shell();
    for (sx=[-1,1], sy=[-1,1]) arm(sx, sy);
    pcb_bosses();
    snap_posts();
}

body_bottom();

echo(str("ASSERT span=", span_x, "x", span_y));
echo(str("ASSERT wheelbase=", wheelbase));
echo(str("ASSERT motor_offset=", motor_off));
