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

arm_root_z = 9.8;   // arm centre height — chosen so the beam TOP stays under the
                    // body rim (half_h=13): root_z + arm_h/2 ≈ 12.6 < 13
motor_lift = -1.0;  // motor cylinders dropped so they hang below the body and
                    // their TOP sits just under the pod top (body rides higher)

tof_d = 7; flow_d = 7; tof_pos = [0,-3.9]; flow_pos = [0,8.3]; cam_w = 9; snap_n = 4;

/* 1S pack (rear-insertable) — keep in sync with battery_dummy.scad */
batt_w = 22; batt_h = 9.5;
// the pack must sit ON TOP of the board so the downward sensors (under the board)
// stay clear. Board bottom rests on the bosses (floor_t+boss_h), board is 1.6 mm.
board_top = floor_t + boss_h + 1.6;   // ≈ 5.8 — the battery floor

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
        // REAR battery slot — opens the rear wall ONLY from the board top upward,
        // so the pack slides in ON TOP of the board. The wall stays SOLID below
        // board_top, blocking the pack from sliding underneath (which would cover
        // the downward sensors). Top portion of the pack passes under the capot.
        translate([0, pod_y/2-wall/2, board_top + 4.6])
            cube([batt_w+1.5, wall+3, 9.2], center=true);
    }
    // (camera nose bump removed — it left a little tab hanging below the body;
    //  the front camera is just a clean through-hole now)
}

/* ===== flat Tello-style lattice/truss arms — one tapered girder per motor ===== */
MOTORS = [for (sx=[-1,1], sy=[-1,1]) [sx,sy]];

arm_w     = 7.4;   // beam width at the body root
arm_w_tip = 6.2;   // beam width at the motor
arm_h     = 5.6;   // beam height (a flat slab, flat top/bottom like the Tello)
arm_lattice = false;  // false = SOLID flat beams (per the reference image);
                      // true  = open triangular truss/lattice

// flat tapered beam along +x, root at x=0, tip at x=L, centred in Z. When
// arm_lattice is on, alternating triangular windows are cut on the top/bottom
// AND the side faces (offset half a bay) for an open Tello-style truss; when off
// it is a clean solid flat girder. Either way it is a flat beam (not a tube).
module lattice_arm(L, w0, w1, h) {
    chord = 1.6;
    xs = 3.5; xe = L - 5; n = 4; seg = (xe - xs)/n;
    difference() {
        hull() {                                   // tapered flat beam, rounded plan ends
            cylinder(d=w0, h=h, center=true, $fn=36);
            translate([L,0,0]) cylinder(d=w1, h=h, center=true, $fn=36);
        }
        yi = w1/2 - chord;                         // top/bottom windows (through Z)
        if (arm_lattice && yi > 0.6)
            for (i=[0:n-1]) {
                x0 = xs + i*seg; x1 = x0 + seg; s = (i%2==0)?1:-1;
                translate([0,0,-h]) linear_extrude(2*h)
                    polygon([[x0,s*yi],[x1,s*yi],[(x0+x1)/2,-s*yi]]);
            }
        zi = h/2 - chord;                          // side windows (through Y), half-bay offset
        if (arm_lattice && zi > 0.6)
            for (i=[0:n-1]) {
                x0 = xs + seg/2 + i*seg; x1 = min(x0+seg, xe+seg/2); s = (i%2==0)?1:-1;
                translate([0, w0, 0]) rotate([90,0,0]) linear_extrude(2*w0)
                    polygon([[x0, s*zi],[x1, s*zi],[(x0+x1)/2, -s*zi]]);
            }
    }
}

// DOUBLE arm (like the Tello): TWO thin struts per motor, splayed from two body
// attach points to the motor pod — forming a clean triangle. Both roots sit near
// the body corner (clear of the camera face) and descend to the pod mid-height.
strut_w0 = 4.7;    // strut width at the body
strut_w1 = 3.7;    // strut width at the motor
function P_side(m) = [m[0]*20.5, m[1]*25,   arm_root_z];   // onto the side face
function P_end(m)  = [m[0]*13,   m[1]*36.5, arm_root_z];   // onto the end/corner face
module one_strut(R, M) {
    ang  = atan2(M[1]-R[1], M[0]-R[0]);
    Lh   = norm([M[0]-R[0], M[1]-R[1]]);
    rise = M[2]-R[2]; theta = atan2(rise, Lh); L3 = norm([Lh, rise]);
    translate(R) rotate([0,0,ang]) rotate([0,-theta,0])
        lattice_arm(L3, strut_w0, strut_w1, arm_h);
}
module truss_arm(m) {
    M = [m[0]*motor_off, m[1]*motor_off, motor_lift + nacelle_h/2];
    one_strut(P_side(m), M);
    one_strut(P_end(m),  M);
}
// motor pod — SOLID outer shell, rounded rims (minkowski). The pocket/vent are
// cut last (motor_bores) so the bore is always clear for the 8520.
module nacelle_outer(m) {
    rn = 0.6;
    translate([m[0]*motor_off, m[1]*motor_off, motor_lift])
        minkowski() {
            cylinder(d1=nacelle_d-2*rn, d2=nacelle_d-1-2*rn, h=nacelle_h-2*rn);
            sphere(r=rn, $fn=22);
        }
}
module motor_bores() {
    for (m = MOTORS)
        translate([m[0]*motor_off, m[1]*motor_off, motor_lift]) {
            translate([0,0,floor_t]) cylinder(d=motor_d+0.15, h=nacelle_h+1);  // motor pocket
            cylinder(d=motor_d-3, h=nacelle_h*3, center=true);                 // bottom wire/vent
        }
    // the motor wire drops through the bottom vent and runs under the struts —
    // no slot cut across the strut roots (that was breaking the arm up).
}
// clip collar: a Ø18.6 mm flange + retention ridge on each nacelle so the real
// Tello prop guard (its C-clip has an inner radius ≈ 9.5 mm) snaps on snugly and
// is held axially. The collar sits low (a stub below the pod, doubling as a foot).
clip_r = 9.3;
module clip_collar(m) {
    translate([m[0]*motor_off, m[1]*motor_off, 0])
    difference() {
        union() {
            translate([0,0,-3.5]) cylinder(r=clip_r, h=5.5, $fn=44);                  // collar body (z -3.5..2)
            translate([0,0,1.1]) cylinder(r1=clip_r, r2=clip_r+0.55, h=1.0, $fn=44);  // top retention ridge
            translate([0,0,-4.1]) cylinder(r1=clip_r-1.4, r2=clip_r, h=0.7, $fn=44);  // bottom lead-in
        }
        // hollow it (the clip only grips the outer wall) — keep a ~1.6 mm wall and
        // a solid top that ties into the nacelle; saves weight.
        translate([0,0,-3.5-eps]) cylinder(r=clip_r-1.6, h=4.6, $fn=40);              // remove core (z -3.5..1)
    }
}
module arms() {
    for (m = MOTORS) { truss_arm(m); nacelle_outer(m); clip_collar(m); }
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
        union() { pod_shell(); arms(); }
        inner_cavity();    // keep the interior clean (trims the arm roots inside)
        motor_bores();     // pockets + vents + wire slots LAST → bores always clear
    }
    pcb_bosses();
    snap_posts();
}

body_bottom_v2();
echo(str("V2 wheelbase=", wheelbase, " motor_off=", motor_off));
