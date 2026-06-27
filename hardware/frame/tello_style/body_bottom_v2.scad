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

arm_root_z = 7.0;   // struts attach HIGH on the pod (upper body)
motor_lift = 1.0;   // motors sit LOW → struts descend (the Tello stance)

tof_d = 7; flow_d = 7; tof_pos = [0,-3.9]; flow_pos = [0,8.3]; cam_w = 9; snap_n = 4;

/* 1S pack (rear-insertable) — keep in sync with battery_dummy.scad */
batt_w = 22; batt_h = 9.5;

module rrect(x, y, r, h) { linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true); }

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
            && min([for(s=sensors) norm([x-s[0],y-s[1]])])>6
            && min([for(b=bosses) norm([x-b[0],y-b[1]])])>7;
        if (keep) translate([x,y,-eps]) rotate([0,0,30]) cylinder(r=R, h=floor_t+2*eps, $fn=6);
    }
}
module pod_shell() {
    difference() {
        pod_outer();
        inner_cavity();
        translate([tof_pos[0], tof_pos[1], -eps]) cylinder(d=tof_d, h=floor_t+2*eps);
        translate([flow_pos[0], flow_pos[1], -eps]) cylinder(d=flow_d, h=floor_t+2*eps);
        floor_vents();
        translate([0,-pod_y/2-eps,half_h*0.5]) rotate([-90,0,0]) cylinder(d=cam_w+0.6, h=wall+2);
        translate([-pod_x/2-eps,-15,2.5]) cube([wall+2,12,5.5]);            // USB-C
        // REAR battery slot — the pack slides in from the back, on the board
        translate([0, pod_y/2-wall/2, floor_t+boss_h+batt_h/2+0.3])
            cube([batt_w+1.5, wall+3, batt_h+1.2], center=true);
    }
    // camera nose bump
    translate([0,-pod_y/2+1,half_h*0.5]) rotate([-90,0,0]) difference() {
        cylinder(d=cam_w+5, h=3.5);
        translate([0,0,-eps]) cylinder(d=cam_w+0.5, h=4);
        translate([-cam_w,-cam_w-2,-eps]) cube([2*cam_w,cam_w+2,5]);
    }
}

/* ===== twin Tello-style arms with a hidden motor-wire channel ===== */
MOTORS = [for (sx=[-1,1], sy=[-1,1]) [sx,sy]];

// per motor: the motor junction (low) + two splayed pod attach points (high)
function Mtop(m) = [m[0]*motor_off, m[1]*motor_off, motor_lift+2.5];
function P_side(m) = [m[0]*21, m[1]*20, arm_root_z];   // onto the long side wall
function P_end(m)  = [m[0]*14, m[1]*38, arm_root_z];   // onto the end corner

module strut(A, B, d) {
    hull() { translate(A) sphere(d=d, $fn=22); translate(B) sphere(d=d*1.05, $fn=22); }
}
module nacelle(m, ang) {
    translate([m[0]*motor_off, m[1]*motor_off, motor_lift]) difference() {
        cylinder(d1=nacelle_d, d2=nacelle_d-1, h=nacelle_h);
        translate([0,0,floor_t]) cylinder(d=motor_d+0.15, h=nacelle_h);    // motor pocket
        cylinder(d=motor_d-3, h=nacelle_h*3, center=true);                 // bottom wire/vent
    }
}
module twin_arms() {
    for (m = MOTORS) {
        strut(Mtop(m), P_side(m), 4.7);   // wire strut (channel cut later)
        strut(Mtop(m), P_end(m),  4.4);   // plain structural strut
        nacelle(m);
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
        translate([rx*cos(a), ry*sin(a), half_h-2.4]) cylinder(d=2.2, h=2.4);
    }
}

module body_bottom_v2() {
    difference() {
        union() { pod_shell(); twin_arms(); }
        wire_channels();   // hidden motor-wire passages
        inner_cavity();    // keep the interior clean (trims struts inside)
        // re-open the sensor/USB/rear-slot/camera cuts that inner_cavity might
        // have back-filled is unnecessary — pod_shell already cut them and
        // inner_cavity is the same volume.
    }
    pcb_bosses();
    snap_posts();
}

body_bottom_v2();
echo(str("V2 wheelbase=", wheelbase, " motor_off=", motor_off));
