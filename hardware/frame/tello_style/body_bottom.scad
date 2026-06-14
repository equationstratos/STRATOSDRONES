// STRATOSDRONE — Tello-style closed-body shell, LOWER half (structural).
//
// Same footprint class as a DJI Tello (≈98 × 92.5 mm, 118 mm wheelbase, 3"
// props) but visually distinct: hexagonal motor nacelles, a chamfered camera
// nose, a slide-in rear battery, and a bevelled pod. This is the bottom
// clamshell — it carries the PCB, the four arms, the motor pockets and the
// bottom sensor window. Pair with body_top.scad.
//
//   openscad -o stl/body_bottom.stl --export-format binstl body_bottom.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;
eps = 0.01;

/* ---------- shared geometry (keep in sync with body_top.scad) ---------- */
span_x      = 98;     // overall width  (left-right), incl. motors
span_y      = 92.5;   // overall length (front-back), incl. motors
wheelbase   = 118;    // motor-to-motor diagonal
motor_off   = wheelbase/2/sqrt(2);   // 41.72 mm in x and y
motor_d     = 8.5;    // 8520 motor diameter
motor_h     = 16;     // motor pocket depth
nacelle_d   = 15;     // outer hex nacelle across-flats
pod_x       = 36;     // central pod width  (narrow, Tello-like)
pod_y       = 70;     // central pod length (elongated)
wall        = 1.6;
half_h      = 13;     // height of the lower shell
floor_t     = 1.4;
arm_w       = 9;      // arm width (slimmer, Tello-like)
arm_h       = 6.0;    // arm thickness (structural)
pcb_x       = 32;     // Tello-style portrait mainboard (see design.py BOARD)
pcb_y       = 66;
pcb_hole    = 24;     // PCB mount hole pitch X (24 x 58)
pcb_hole_y  = 58;
boss_h      = 3.0;
batt_w      = 27;     // 1S pack
batt_l      = 53;
batt_h      = 13;
sensor_win  = 16;     // flow + ToF window
cam_w       = 9;      // camera barrel
snap_n      = 8;

module rrect(x, y, r, h) {            // rounded rect prism, centered
    linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true);
}

module hex(across_flats, h) {
    r = across_flats/sqrt(3);
    cylinder(r=r, h=h, $fn=6);
}

/* central pod outer wall + floor */
module pod_shell() {
    difference() {
        rrect(pod_x, pod_y, 6, half_h);
        // hollow interior
        translate([0,0,floor_t])
            rrect(pod_x-2*wall, pod_y-2*wall, 5, half_h);
        // bottom sensor window (flow + ToF look straight down; long enough to
        // clear both U8/U9 which are spaced along the board spine)
        translate([0,3,-eps]) rrect(sensor_win, sensor_win+10, 2, floor_t+2*eps);
        // camera aperture at the front nose (-y)
        translate([0,-pod_y/2-eps,half_h*0.5])
            rotate([-90,0,0]) cylinder(d=cam_w+0.6, h=wall+2);
        // USB-C slot on the LEFT side wall (like the Tello micro-USB), forward of centre
        translate([-pod_x/2-eps,-15,2.5]) cube([wall+2,12,5.5]);
    }
    // chamfered camera nose bump
    translate([0,-pod_y/2+1,half_h*0.5])
        rotate([-90,0,0])
            difference() {
                cylinder(d=cam_w+5, h=3.5);
                translate([0,0,-eps]) cylinder(d=cam_w+0.5, h=4);
                translate([-cam_w,-cam_w-2,-eps]) cube([2*cam_w,cam_w+2,5]);
            }
}

/* one arm + hex motor nacelle at signed corner (sx, sy) */
module arm(sx, sy) {
    ang = atan2(sy, sx);
    // arm bridge from pod edge to motor
    hull() {
        translate([sx*(pod_x/2-6), sy*(pod_y/2-6), 0]) cylinder(d=arm_w, h=arm_h);
        translate([sx*motor_off, sy*motor_off, 0]) cylinder(d=arm_w, h=arm_h);
    }
    // hex nacelle with press-fit motor pocket + wire channel
    translate([sx*motor_off, sy*motor_off, 0]) {
        difference() {
            hex(nacelle_d, motor_h);
            translate([0,0,floor_t]) cylinder(d=motor_d+0.15, h=motor_h);
            cylinder(d=motor_d-3, h=motor_h*3, center=true);            // vent
            // wire channel toward pod
            rotate([0,0,ang+180]) translate([0,-1.6,floor_t]) cube([nacelle_d, 3.2, motor_h]);
        }
    }
}

/* PCB mounting bosses (4) inside the pod, at the 24 x 58 mm hole pitch */
module pcb_bosses() {
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*pcb_hole/2, sy*pcb_hole_y/2, floor_t-eps])
            difference() {
                cylinder(d=6, h=boss_h);
                translate([0,0,0.8]) cylinder(d=1.7, h=boss_h);   // M2 self-tap
            }
}

/* rear battery cradle (slide-in from +y) */
module battery_bay() {
    for (s=[-1,1])
        translate([s*(batt_w/2+1.3), pod_y/2-batt_l-2, floor_t-eps])
            cube([2.6, batt_l, batt_h*0.6]);
    // floor stops
    translate([-batt_w/2, pod_y/2-batt_l-2, floor_t-eps]) cube([batt_w,2.5,3]);
}

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
    battery_bay();
    snap_posts();
}

body_bottom();

echo(str("ASSERT span=", span_x, "x", span_y));
echo(str("ASSERT wheelbase=", wheelbase));
echo(str("ASSERT motor_offset=", motor_off));
