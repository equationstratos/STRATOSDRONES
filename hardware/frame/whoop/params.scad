// STRATOSDRONE — whoop airframe, shared parameters + helper modules.
// Functional envelope kept identical to the validated electronics: 118 mm
// wheelbase, 8520 brushed motors, 3" (76 mm) props, 36x70 mainboard, M2 bosses
// at 26x60. Aesthetic target: smooth, swept, aggressive, airflow-optimised.
// SPDX-License-Identifier: CERN-OHL-P-2.0

/* ---- selectable variants (override on the CLI with -D) ---- */
guard = "duct";   // "none" | "ring" | "duct"

/* ---- functional geometry (DO NOT change without the PCB/firmware) ---- */
wheelbase   = 118;                  // motor-to-motor diagonal
motor_off   = wheelbase/2/sqrt(2);  // 41.72 mm in x and y
motor_d     = 8.5;                  // 8520 motor body
motor_fit   = 0.15;                 // press-fit clearance
motor_h     = 15;                   // motor pocket depth
prop_d      = 76.2;                 // 3"
prop_r      = prop_d/2;
pcb_x       = 36;                   // mainboard (see hardware/pcb design.py BOARD)
pcb_y       = 70;
hole_x      = 26;                   // M2 boss pitch
hole_y      = 60;
sensor_win  = 16;                   // flow + ToF aperture (under-body)

/* ---- structure / style ---- */
deck_x      = 44;       // central deck width
deck_y      = 82;       // central deck length (PCB + rear battery)
deck_t      = 2.0;      // deck plate thickness
wall        = 1.6;
arm_w       = 9;        // arm root width (tapers to motor)
arm_tip_w   = 11;       // width at the motor boss
arm_h       = 5.5;      // arm thickness
boss_h      = 3.2;      // PCB standoff height
guard_gap   = 3.2;      // radial clearance prop tip -> guard inner wall
guard_ir    = prop_r + guard_gap;        // guard inner radius
ring_t      = 2.2;      // open-ring wall thickness
ring_h      = 7;        // open-ring height
duct_t      = 1.8;      // duct wall thickness
duct_h      = 16;       // duct height (>= prop plane + lip)
duct_lip_r  = 2.6;      // intake lip radius (rounded top rim)
ground_clear= 10;       // skid height (duct variant)

/* ---- battery (1S LiHV ~ 1100 mAh) ---- */
batt_w      = 27;
batt_l      = 52;
batt_h      = 13;

/* ---- canopy ---- */
can_x       = deck_x + 2.4;
can_y       = deck_y + 2.4;
can_h       = 17;       // canopy crown height
can_wall    = 1.5;
cam_w       = 9;        // camera barrel
clip_n      = 4;        // canopy clip posts

$fn = 64;
eps = 0.01;

/* ---------- helper modules ---------- */
module rrect(x, y, r, h) {                 // rounded-rect prism, centred
    linear_extrude(h) offset(r) square([max(x-2*r,0.1), max(y-2*r,0.1)], center=true);
}

// teardrop-ish swept arm from (x0,y0) to (x1,y1), w0->w1 wide, h tall
module swept_arm(x0, y0, x1, y1, w0, w1, h) {
    hull() {
        translate([x0, y0, 0]) cylinder(d=w0, h=h);
        translate([x1, y1, 0]) cylinder(d=w1, h=h);
    }
}

module motor_pocket() {                    // press-fit 8520 + bottom vent + wire slot
    difference() {
        cylinder(d=motor_d + 2*motor_fit + 2*wall, h=motor_h);
        translate([0,0,1.2]) cylinder(d=motor_d + 2*motor_fit, h=motor_h);
        cylinder(d=motor_d-3, h=motor_h*3, center=true);     // vent
    }
}

// guard around a motor at local origin; mode picks the style
module prop_guard(mode) {
    if (mode == "ring") {
        // thin open ring on 3 struts (Tello-like, light)
        rotate_extrude() translate([guard_ir, 0]) square([ring_t, ring_h]);
    } else if (mode == "duct") {
        // full cinewhoop duct: wall + rounded intake lip + skid foot
        difference() {
            union() {
                cylinder(r=guard_ir + duct_t, h=duct_h);
                translate([0,0,duct_h])           // rounded intake lip
                    rotate_extrude()
                        translate([guard_ir + duct_t/2, 0]) circle(r=duct_lip_r);
            }
            translate([0,0,-eps]) cylinder(r=guard_ir, h=duct_h+duct_lip_r+1);
        }
    }
    // "none" -> nothing
}
