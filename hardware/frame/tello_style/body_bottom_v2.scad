// STRATOSDRONE — Tello-style LOWER shell, V2 (twin Tello-style arms).
//
// New version per the reference Tello: each motor is carried by TWO splayed
// struts (not one truss arm), the motor wires run HIDDEN inside a channel in
// one strut of each pair down to the PCB, and the 1S pack slides in from the
// REAR (a rear slot) so you don't have to pull the canopy. Pod, honeycomb
// floor, sensor apertures, rounded belly and PCB bosses are carried over.
// Pair with a rear-slot canopy (body_top_v2.scad) — or the existing body_top*.
//
//   openscad -o stl/body_bottom_v2.stl --export-format binstl body_bottom_v2.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;
eps = 0.01;

/* ---------- shared geometry (keep in sync with body_top.scad) ---------- */
wheelbase   = 118;
motor_off   = wheelbase/2/sqrt(2);   // 41.72
motor_d     = 8.5;

nacelle_wall = 1.9;
nacelle_d    = motor_d + 2*nacelle_wall + 0.4;   // ≈12.7
motor_grip   = 12;
floor_t      = 1.2;
nacelle_h    = motor_grip + floor_t;             // ≈13.2

pcb_x = 38; pcb_y = 74; pcb_hole = 26; pcb_hole_y = 62; pcb_clear = 0.5; boss_h = 3.0;
pod_x = pcb_x + 2*pcb_clear + 2*1.5;   // ≈42
pod_y = pcb_y + 2*pcb_clear + 2*1.5;   // ≈78
pod_r = 9; wall = 1.5; half_h = 13;

arm_root_z = 11.0;  // struts attach near the TOP of the pod (like the Tello)
motor_lift = -1.0;  // motor cylinders dropped so they hang below the body and
                    // their TOP sits just under the pod top (body rides higher)

tof_d = 7; flow_d = 7; tof_pos = [0,-3.9]; flow_pos = [0,8.3]; cam_w = 9; snap_n = 4;

/* 1S pack (rear-insertable) — keep in sync with battery_dummy.scad */
batt_w = 22; batt_h = 9.5;

module rrect(x, y, r, h) { linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true); }

// rounded box centred at the origin: size sz=[x,y,z], every edge filleted by r.
// Used to build the arm blades/gussets so they read smooth, not faceted.
module rbox(sz, r) {
    hull() for (i=[-1,1], j=[-1,1], k=[-1,1])
        translate([i*(sz[0]/2-r), j*(sz[1]/2-r), k*(sz[2]/2-r)]) sphere(r, $fn=20);
}

/* ===== pod (carried over from v1) ===== */
module pod_outer() {
    br = 3; isq = [pod_x-2*pod_r, pod_y-2*pod_r];
    hull() {
        translate([0,0,br]) linear_extrude(half_h-br) offset(pod_r) square(isq, center=true);
        for (i=[0:6]) translate([0,0, br*(1-cos(i/6*90))]) linear_extrude(0.02)
            offset(pod_r - br*(1-sin(i/6*90))) square(isq, center=true);
    }
}
module inner_cavity() {
    translate([0,0,floor_t]) rrect(pod_x-2*wall, pod_y-2*wall, max(pod_r-wall,1), half_h+1);
}
module floor_vents() {
    R=2.5; gap=1.1; pitch=R*sqrt(3)+gap; dy=pitch*sqrt(3)/2;
    sensors=[tof_pos, flow_pos];
    bosses=[for (sx=[-1,1],sy=[-1,1]) [sx*pcb_hole/2, sy*pcb_hole_y/2]];
    for (iy=[-7:7], ix=[-4:4]) {
        x=ix*pitch + (iy%2?pitch/2:0); y=iy*dy;
        keep = abs(x)<15 && abs(y)<33
            && !(abs(x)<9 && y<-15)                       // solid floor behind the camera
            && min([for(s=sensors) norm([x-s[0],y-s[1]])])>6
            && min([for(b=bosses) norm([x-b[0],y-b[1]])])>7;
        if (keep) translate([x,y,-eps]) rotate([0,0,30]) cylinder(r=R, h=floor_t+2*eps, $fn=6);
    }
}
cam_z = half_h*0.5;   // camera centre height
// clean recessed lens housing (Tello-style) instead of a raw through-hole: a
// smooth rounded bezel that protrudes from the nose, with a recessed lens cup
// and a small lens bore. The floor right behind it is solid (see floor_vents),
// so you no longer look through into the honeycomb.
module camera_bezel() {
    translate([0, -pod_y/2, cam_z]) rotate([90,0,0])
        minkowski() { cylinder(d=10.5, h=1.6, $fn=48); sphere(r=1.2, $fn=22); }
}
module camera_cuts() {
    translate([0, -pod_y/2 - 4, cam_z]) rotate([-90,0,0]) {
        cylinder(d=8.6, h=4.0, $fn=44);        // recessed lens cup (clean face)
        cylinder(d=5.2, h=wall+9, $fn=32);     // small lens bore through the wall
    }
}
module pod_shell() {
    difference() {
        union() { pod_outer(); camera_bezel(); }
        inner_cavity();
        translate([tof_pos[0], tof_pos[1], -eps]) cylinder(d=tof_d, h=floor_t+2*eps);
        translate([flow_pos[0], flow_pos[1], -eps]) cylinder(d=flow_d, h=floor_t+2*eps);
        floor_vents();
        camera_cuts();
        translate([-pod_x/2-eps,-15,2.5]) cube([wall+2,12,5.5]);            // USB-C
        // REAR battery slot — the pack slides in from the back, on the board
        translate([0, pod_y/2-wall/2, floor_t+boss_h+batt_h/2+0.3])
            cube([batt_w+1.5, wall+3, batt_h+1.2], center=true);
    }
}

/* ===== twin Tello-style arms with a hidden motor-wire channel ===== */
MOTORS = [for (sx=[-1,1], sy=[-1,1]) [sx,sy]];

// per motor: the motor junction (low) + two splayed pod attach points (high)
function Mtop(m) = [m[0]*motor_off, m[1]*motor_off, motor_lift + nacelle_h/2];  // arms meet the cylinder at MID-height
// both roots sit at the CORNER (clear of the camera face) so the flat front
// stays a clean uniform panel; the corner shoulder fairs them in smoothly.
function P_side(m) = [m[0]*21, m[1]*27, arm_root_z];   // side face, near the corner
function P_end(m)  = [m[0]*15, m[1]*37, arm_root_z];   // end face, onto the corner

// flat strut: a vertical BLADE between A and B (thin horizontally, taller
// vertically) — flat faces, but every edge filleted (rbox) so it reads smooth,
// not faceted. Still a flat blade, no round-tube look.
arm_r = 0.9;   // edge fillet radius on the arms (maximum-smooth)
module blade(A, B, thick, h) {
    ang = atan2(B[1]-A[1], B[0]-A[0]);
    r = min(arm_r, thick/2 - 0.05, h/2 - 0.05);
    hull() {
        translate(A) rotate([0,0,ang]) rbox([2*r, thick, h], r);
        translate(B) rotate([0,0,ang]) rbox([2*r, thick, h], r);
    }
}
// a strut = the slim blade PLUS a flared root fairing where it meets the body:
// the root grows wider and deepens DOWN toward the floor, and is pushed a few mm
// INTO the wall so it welds through the full wall thickness (inner_cavity then
// trims it flush inside). This makes the arm look moulded into the body — a
// gusset — instead of a thin tab grazing the surface.
module strut(A, B, thick, h) {
    ang = atan2(B[1]-A[1], B[0]-A[0]);
    dir = (B - A) / norm(B - A);            // unit, motor -> body
    L   = norm(B - A);
    blade(A, B, thick, h);                  // slim flat blade
    // gentle flare where the blade washes into the motor pod (softens the crease)
    Pn  = A + dir*5.5;
    hull() {
        translate(A)  rotate([0,0,ang]) rbox([2*arm_r, thick+1.8, h+0.6], arm_r);
        translate(Pn) rotate([0,0,ang]) rbox([2*arm_r, thick,     h     ], arm_r);
    }
    Po  = A + dir*(L - 8);                  // 8 mm outboard of the body — still slim
    Pi  = B + dir*2.2;                      // 2.2 mm INTO the wall (volumetric weld)
    z0  = 3.8;                              // stop ABOVE the rounded belly so the
                                            // bottom edge stays one smooth curve
    z1  = arm_root_z + h/2;                 // up to the blade top
    rg  = arm_r;
    hull() {
        translate(Po) rotate([0,0,ang]) rbox([2*rg, thick,       h     ], rg);
        translate([Pi[0], Pi[1], (z0+z1)/2])
            rotate([0,0,ang])           rbox([2*rg, thick + 2.6, z1-z0], rg);
    }
}
// motor pod — SOLID outer shell, rounded at both rims (minkowski) so there is no
// sharp lip where the blades wash into it. The motor pocket + wire vent are NOT
// cut here: they are subtracted at the very end (motor_bores), AFTER the blades
// are unioned, so a blade rooting at the pod axis can never block the bore.
module nacelle_outer(m) {
    rn = 0.6;
    translate([m[0]*motor_off, m[1]*motor_off, motor_lift])
        minkowski() {
            cylinder(d1=nacelle_d-2*rn, d2=nacelle_d-1-2*rn, h=nacelle_h-2*rn);
            sphere(r=rn, $fn=22);
        }
}
// the motor bores (pocket the 8520 presses into + a bottom wire/cooling vent),
// cut last so the pocket is guaranteed clear for the motor.
module motor_bores() {
    for (m = MOTORS)
        translate([m[0]*motor_off, m[1]*motor_off, motor_lift]) {
            translate([0,0,floor_t]) cylinder(d=motor_d+0.15, h=nacelle_h+1);  // motor pocket
            cylinder(d=motor_d-3, h=nacelle_h*3, center=true);                 // bottom vent
        }
}
blade_h = 4.5;    // blade height (vertical) — flat face, not a tube
// corner shoulder: a moulded fill that bridges the two strut roots to the body
// corner, so the arms emerge from a solid shoulder flush with the walls — no
// recessed step and no open slot between the arm and the body near the corner.
module corner_blend(m) {
    rb = 1.3;                                   // smoothing radius (minkowski)
    z0 = 3.8; z1 = arm_root_z + blade_h/2; zc = (z0+z1)/2; H = z1 - z0;
    c  = [m[0]*(pod_x/2 - 3), m[1]*(pod_y/2 - 3)];   // anchor on the body corner
    ps = P_side(m); pe = P_end(m);
    minkowski() {                               // round the whole shoulder smooth
        hull() {
            translate([c[0],  c[1],  zc]) cube([1.4, 1.4, H-2*rb], center=true);
            translate([ps[0], ps[1], zc]) cube([1.4, 1.4, H-2*rb], center=true);
            translate([pe[0], pe[1], zc]) cube([1.4, 1.4, H-2*rb], center=true);
        }
        sphere(r=rb, $fn=18);
    }
}
module twin_arms() {
    for (m = MOTORS) {
        corner_blend(m);                           // solid shoulder at the body corner
        strut(Mtop(m), P_side(m), 4.4, blade_h);   // wire strut (holds the channel)
        strut(Mtop(m), P_end(m),  2.8, blade_h);   // plain flat strut
        nacelle_outer(m);
    }
}
// the hidden wire channels (subtracted from the body so they pierce the strut
// and the pod wall, opening into the cavity at the PCB)
module wire_channels() {
    for (m = MOTORS) {
        A = Mtop(m); B = P_side(m);
        dir = (B - A) / norm(B - A);
        hull() {
            translate(A - dir*1) sphere(d=2.2, $fn=14);   // open at the motor
            translate(B + dir*9) sphere(d=2.2, $fn=14);   // open into the cavity
        }
    }
}

/* ===== PCB bosses + snap posts (carried over) ===== */
module pcb_bosses() {
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*pcb_hole/2, sy*pcb_hole_y/2, floor_t-eps]) difference() {
            union() { cylinder(d=6, h=boss_h); cylinder(d1=8, d2=6, h=1.2); }
            translate([0,0,0.8]) cylinder(d=1.7, h=boss_h);
            translate([0,0,boss_h-0.55]) cylinder(d1=1.7, d2=3, h=0.6);
        }
}
module snap_posts() {
    for (i=[0:snap_n-1]) {
        a = 45 + i*360/snap_n; rx = pod_x/2-2.2; ry = pod_y/2-2.2;
        px = rx*cos(a); py = ry*sin(a); sx = sign(px);
        // the clip post itself (the canopy socket drops over it)
        translate([px, py, half_h-2.4]) cylinder(d=2.2, h=2.4);
        // anchor rib to the inner side wall so the post isn't a floating pillar
        // (it sits in the corner gap, outboard of the battery, hidden inside)
        hull() {
            translate([px, py, half_h-2.4]) cylinder(d=2.0, h=2.4);
            translate([sx*(pod_x/2-wall*0.4), py, half_h-2.4]) cylinder(d=2.0, h=2.4);
        }
    }
}

module body_bottom_v2() {
    difference() {
        union() { pod_shell(); twin_arms(); }
        wire_channels();   // hidden motor-wire passages
        inner_cavity();    // keep the interior clean (trims struts inside)
        motor_bores();     // pockets + vents LAST → bores always clear for the motors
    }
    pcb_bosses();
    snap_posts();
}

body_bottom_v2();
echo(str("V2 wheelbase=", wheelbase, " motor_off=", motor_off));
