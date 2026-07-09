// STRATOSDRONE Fr4n7-F — FOLDABLE-arm Tello-class frame (v0, M0).
//
// Concept credit: inspired by Thingiverse thing:1604440 (foldable mini quad
// with corner-pivot arms) — https://www.thingiverse.com/thing:1604440 —
// CLEAN-ROOM: this file is our own original parametric geometry, nothing
// copied from that mesh. Key twist from the project owner's printed
// prototype: the FRONT arms are mounted INVERTED (pod flipped, prop below
// the belly) so the folded arms never cross — front folds rearward in a LOW
// prop plane, rear folds forward in a HIGH plane along the same flank.
//
// Both versions share torsion-spring pivots + a sliding latch that holds the
// arms FOLDED (arms deploy by spring the instant it releases):
//   V1 "manuelle":  umbrella-style mechanical push-button (zero electronics)
//   V2 "commande":  a nano-servo cam pushes the same latch — `deploy` SDK
//                   verb (spec in ../DESIGN.md — NOT yet in firmware)
// Folding back IN is manual in both versions: hold the button pressed while
// rotating the arms until the latch pins drop into their keyholes.
//
//   for P in body arm_front arm_rear arm_fr arm_fl arm_rr arm_rl latch button servo_cam; do
//     xvfb-run -a openscad -o stl/$P.stl --export-format binstl \
//       -D "PART=\"$P\"" frame_foldable.scad; done
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;
eps = 0.01;

PART = "assembly";   // body|arm_front|arm_rear|arm_fr|arm_fl|arm_rr|arm_rl|
                     // latch|button|servo_cam|assembly|assembly_folded|
                     // collision_folded|collision_arms

/* ---- shared geometry — keep in sync with tello_style/body_bottom_v2.scad ---- */
wheelbase   = 118;
motor_off   = wheelbase/2/sqrt(2);   // 41.72
motor_d     = 8.5;                   // 8520 brushed
nacelle_wall = 1.9;
nacelle_d    = motor_d + 2*nacelle_wall + 0.4;   // ~12.7
motor_grip   = 12;
floor_t      = 1.2;
nacelle_h    = motor_grip + floor_t;             // ~13.2
pcb_x = 38; pcb_y = 74; pcb_hole = 26; pcb_hole_y = 62; pcb_clear = 0.5; boss_h = 3.0;
pod_x = pcb_x + 2*pcb_clear + 2*1.5;   // ~42
pod_y = pcb_y + 2*pcb_clear + 2*1.5;   // ~78
pod_r = 9; wall = 1.5; half_h = 13;
tof_d = 7; flow_d = 7; tof_pos = [0,-3.9]; flow_pos = [0,8.3]; cam_w = 9; snap_n = 4;
batt_w = 22; batt_h = 9.5;
board_top = floor_t + boss_h + 1.6;    // ~5.8
arm_w = 7.4; arm_w_tip = 6.2; arm_h = 5.6; prop_d = 76.2;

/* ---------------- folding mechanism parameters ----------------
   (everything marked TUNE is a first-print estimate) */
pivot_x   = 19;    pivot_y = 37;    // M2 pivot axes in the corner dead zones
pivot_d   = 2.2;                    // M2 x 12 + nyloc (4x)
crank_out = 8.8;                    // folded beam centreline at x = pivot_x+crank_out = 27.8
                                    // (>= wall 21 + nacelle Ø/2 6.35 + 0.45 clr)   // TUNE
claw_d    = 6.4;                    // arm pivot barrel
jaw_b     = 2.4;                    // bottom clevis jaw (nyloc pocket underneath)
slot_h    = 6.0;                    // clevis slot height (claw 5.6 + 0.4 clr)
jaw_t     = 2.6;                    // top clevis jaw (torsion-spring pocket inside)
knuckle_d = 9.6;                    // clevis tower Ø                       // TUNE
spring_od = 7.4; spring_pk = 2.2;   // torsion spring pocket Ø / depth (0.5 mm wire)
leg_d     = 1.4;                    // spring leg holes
det_d     = 1.8;                    // deployed detent bump/recess          // TUNE
arm_z0    = jaw_b + 0.2;            // beam/claw bottom (2.6)
arm_zc    = arm_z0 + arm_h/2;       // beam centre (5.4)
tooth_y   = 20;                     // latch pins world |y| when folded
latch_travel = 4.5;                 // slider stroke to release             // TUNE
foot_h    = 8;                      // landing feet below the belly
prop_z_lo = -3.5;                   // FRONT (inverted) prop plane — under the belly
prop_z_hi = 19.7;                   // REAR prop plane — above the capot (as v2)

/* ---------------- fold math (documented in ../DESIGN.md) ----------------
   FR canonical, arm local frame = pivot at origin, deployed pose, front = -Y. */
L_pm    = norm([motor_off-pivot_x, motor_off-pivot_y]);      // 23.21 pivot->motor
a_beam  = sqrt(L_pm*L_pm - crank_out*crank_out);             // 22.42 along-beam
th_dep  = atan2(-(motor_off-pivot_y), motor_off-pivot_x);    // -11.74° deployed dir
th_fold = atan2(a_beam, crank_out);                          //  75.02° folded dir
FOLD_A  = th_fold - th_dep;                                  //  86.76° fold sweep
M_loc   = [motor_off-pivot_x, -(motor_off-pivot_y)];         // motor  (22.72,-4.72)
D_loc   = crank_out*[cos(th_dep-90), sin(th_dep-90)];        // dogleg foot (deployed)
pin_wx  = 17.3;                     // latch pin world |x| when folded (inside the wall)
riser_lx = crank_out - 0.9;         // riser on the beam, FOLDED-local x
pin_lx   = pin_wx - pivot_x;        // pin FOLDED-local x (= -1.7)
echo(str("ASSERT wheelbase=", wheelbase, "  FOLD_A=", FOLD_A,
         "  folded_motor=(", pivot_x+crank_out, ",", pivot_y-a_beam, ")"));

/* landing feet — inside the "dead diamond" that no blade (folded, aligned or
   mid-swing fan) sweeps at prop_z_lo. Front props hang below the belly, so
   ground clearance comes from these feet, not nacelle skids. */
FEET = [[16,0],[-16,0],[0,17],[0,-17]];

module rrect(x, y, r, h) { linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true); }

/* ================= pod (v2 shell, no integral arms) ================= */
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
            && min([for(b=bosses) norm([x-b[0],y-b[1]])])>7
            && min([for(f=FEET)   norm([x-f[0],y-f[1]])])>5.5;
        if (keep) translate([x,y,-eps]) rotate([0,0,30]) cylinder(r=R, h=floor_t+2*eps, $fn=6);
    }
}
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
        translate([px, py, half_h-2.4]) cylinder(d=2.2, h=2.4);
        hull() {
            translate([px, py, half_h-2.4]) cylinder(d=2.0, h=2.4);
            translate([sx*(pod_x/2-wall*0.4), py, half_h-2.4]) cylinder(d=2.0, h=2.4);
        }
    }
}
module feet() {
    for (f = FEET) translate([f[0], f[1], -foot_h])
        cylinder(d1=4.6, d2=6.4, h=foot_h+floor_t);
}

/* ================= per-corner placement helper =================
   FR (sx=+1, sy=-1) is the canonical corner; the other three are mirrors. */
module at_corner(sx, sy) {
    translate([sx*pivot_x, sy*pivot_y, 0])
        mirror([sx<0 ? 1:0, 0, 0]) mirror([0, sy>0 ? 1:0, 0])
        children();
}

/* ================= clevis knuckles (body side) ================= */
module knuckle_tower_local() {
    cylinder(d=knuckle_d, h=jaw_b + slot_h + jaw_t);
    for (z0=[0, jaw_b+slot_h])   // webs tying both jaws back to the pod corner
        hull() {
            translate([0,0,z0]) cylinder(d=knuckle_d-1, h=(z0==0 ? jaw_b : jaw_t));
            translate([-7,7,z0]*0.85) cylinder(d=knuckle_d-1, h=(z0==0 ? jaw_b : jaw_t));
        }
}
module knuckle_cuts_local() {
    translate([0,0,-eps]) cylinder(d=pivot_d, h=20);                  // M2 bore
    translate([0,0,-eps]) cylinder(d=4.4/cos(30), h=1.7, $fn=6);      // nyloc pocket
    // claw barrel bore (full circle — the hinge core)
    translate([0,0,jaw_b-0.2]) cylinder(d=claw_d+0.5, h=slot_h+0.4);
    // torsion-spring pocket up inside the TOP jaw + body-side leg hole
    translate([0,0,jaw_b+slot_h-eps]) cylinder(d=spring_od, h=spring_pk+eps);
    rotate([0,0,th_fold+30]) translate([spring_od/2-0.7, 0, jaw_b+slot_h-eps])
        cylinder(d=leg_d, h=jaw_t+2);
    // detent: shallow groove along the whole sweep + deeper click at deployed
    for (a=[th_dep : 8 : th_fold])
        rotate([0,0,a]) translate([claw_d/2-0.4, 0, jaw_b+slot_h+0.1]) sphere(d=det_d+0.1, $fn=24);
    rotate([0,0,th_dep]) translate([claw_d/2-0.4, 0, jaw_b+slot_h+0.05]) sphere(d=det_d+0.4, $fn=24);
    // clevis mouth: fan opening for claw + dogleg + beam over the full sweep.
    // The dogleg hull hugs the barrel halfway round, so open a0 a full 180°
    // behind the deployed direction — the clevis reads as a C-clamp; the two
    // jaws stay tied through the remaining ~90° sector where the web sits.
    a0 = th_dep - 180; a1 = th_fold + 10;
    translate([0,0,jaw_b-0.2]) linear_extrude(slot_h+0.4)
        polygon(concat([[0,0]], [for (a=[a0 : 6 : a1]) 15*[cos(a),sin(a)]],
                       [15*[cos(a1),sin(a1)]]));
}
module knuckles()      { for (sx=[-1,1], sy=[-1,1]) at_corner(sx,sy) knuckle_tower_local(); }
module knuckle_voids() { for (sx=[-1,1], sy=[-1,1]) at_corner(sx,sy) knuckle_cuts_local(); }

/* ================= latch (shared V1/V2) =================
   Arms carry a pin that enters the body through a wall slot when folded.
   A sliding plate ("blade") with KEYHOLE windows drops over the pins:
   slider FORWARD  -> pins captured in the round ends  -> arms locked folded
   slider REARWARD -> pins inside the open rectangles  -> springs deploy arms
   The button (V1) or the servo cam (V2) pushes the slider rearward. */
rail_x  = 18.1;                 // slider rails hug the side walls (inner face 19.5)
rail_z0 = 8.6; rail_z1 = 11.4;  // rails ride above the beams (top 8.2)
blade_z0 = 11.4; blade_z1 = 12.6;
pin_d   = 3.0;                  // latch pin Ø on the arm overhang

module wall_pin_slots() {   // through-wall windows the arm pin/overhang swings through
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*(pod_x/2 - wall/2), sy*tooth_y, (7.6+12.9)/2])
            cube([wall+2.6, 6.4, 12.9-7.6], center=true);
}
module button_hole() {      // V1 front-face push button, beside the camera
    translate([10, -pod_y/2 - eps, 10.6]) rotate([90,0,0]) cylinder(d=5.0, h=wall+2.4, center=true);
}
module latch_guides() {     // ledges the rails ride on (part of the body)
    for (sx=[-1,1], gy=[-11, 11])
        translate([sx*rail_x - 0.8, gy-3, rail_z0-0.7]) cube([1.6, 6, 0.7]);
}
module keyhole() {          // one release window, pin-centred, opens rear+outboard
    translate([0,0,blade_z0-eps]) cylinder(d=pin_d+0.6, h=blade_z1-blade_z0+2*eps);
    translate([-((pin_d+0.6)/2), 0, blade_z0-eps])
        cube([pin_d+0.6, latch_travel+2.2, blade_z1-blade_z0+2*eps]);
    translate([-((pin_d+0.6)/2), latch_travel-0.4, blade_z0-eps])
        cube([6, 4.2, blade_z1-blade_z0+2*eps]);   // open outboard exit
}
module latch_u() {          // ONE printed part: rails + blades + nose + band hooks
    difference() {
        union() {
            for (sx=[-1,1]) {
                translate([sx*rail_x-1.0, -26, rail_z0]) cube([2.0, 52, rail_z1-rail_z0]);
                translate([sx*17.55-2.05, -24.5, blade_z0]) cube([4.1, 49, blade_z1-blade_z0]);
                translate([sx*rail_x-0.6, 25.4, rail_z0]) cube([1.2, 2.6, 5.2]);   // band hook
            }
            translate([-rail_x, -27.0, rail_z0+1.2])
                cube([2*rail_x, 1.6, rail_z1-rail_z0-1.2]);   // nose crossbar (button target)
        }
        for (sx=[-1,1], sy=[-1,1])   // keyholes: rear slot opens REARWARD = +y after mirror
            translate([sx*pin_wx, sy*tooth_y, 0]) mirror([0, sy>0 ? 0:1, 0])
                mirror([sx<0 ? 1:0, 0, 0]) keyhole();
    }
}
module body_band_hooks() {  // rubber-band return anchors on the floor    // TUNE
    for (sx=[-1,1]) translate([sx*rail_x-0.6, 30.5, floor_t-eps]) cube([1.2, 2.6, 5.2]);
}
module button() {           // V1 pin: through the front wall, pushes the crossbar
    cylinder(d=4.6, h=12);
    translate([0,0,12]) cylinder(d=7.6, h=2.4);
}
module servo_cam() {        // V2 cam disc for a 3.7 g nano-servo horn
    difference() {
        union() { cylinder(d=9, h=3); translate([2.6,0,0]) cylinder(d=6, h=3); }
        translate([0,0,-eps]) cylinder(d=4.7, h=3.4);
        for (a=[0:90:270]) rotate([0,0,a]) translate([3.4,0,-eps]) cylinder(d=1.2, h=3.4);
    }
}

/* ================= capot (foldable-specific lid) =================
   The tello_style body_top_v2 skirt (down to z 6.5 on the pod outline) would
   cut through the corner knuckle towers, so the foldable gets its own flat
   lid: base plate on the wall top + raised rear channel over the battery
   (pack top ≈ 15.3 > wall 13) + inner friction lip; corners notched around
   the towers. Snap sockets TUNE on first print. */
module capot() {
    difference() {
        union() {
            translate([0,0,half_h]) rrect(pod_x, pod_y, pod_r, 1.2);          // base plate
            hull() {                                                          // battery channel
                translate([0, 17, half_h]) rrect(batt_w+4, 40, 5, 3.9);
                translate([0, 17, half_h]) rrect(batt_w+9, 45, 7, 0.8);
            }
            translate([0,0,half_h-1.6])                                        // friction lip
                difference() { rrect(pod_x-2*wall-0.4, pod_y-2*wall-0.4, max(pod_r-wall,1), 1.6);
                               rrect(pod_x-2*wall-3.0, pod_y-2*wall-3.0, max(pod_r-wall-1.3,1), 2.0); }
        }
        translate([0, 17, half_h-0.1]) rrect(batt_w+1, 37, 4, 3.4);            // channel hollow
        translate([0, pod_y/2, half_h+2.6]) cube([batt_w+1, 6, 5.2], center=true); // rear opening
        for (sx=[-1,1], sy=[-1,1])                                             // tower notches
            translate([sx*pivot_x, sy*pivot_y, half_h-2]) cylinder(d=knuckle_d+0.8, h=6);
    }
}

/* ================= the body ================= */
module body() {
    difference() {
        union() {
            difference() {
                pod_outer();
                inner_cavity();
                translate([tof_pos[0], tof_pos[1], -eps]) cylinder(d=tof_d, h=floor_t+2*eps);
                translate([flow_pos[0], flow_pos[1], -eps]) cylinder(d=flow_d, h=floor_t+2*eps);
                floor_vents();
                translate([0,-pod_y/2-eps,half_h*0.5]) rotate([-90,0,0]) cylinder(d=cam_w+0.6, h=wall+2);
                translate([-pod_x/2-eps,-15,2.5]) cube([wall+2,12,5.5]);      // USB-C
                translate([0, pod_y/2-wall/2, board_top + 4.6])
                    cube([batt_w+1.5, wall+3, 9.2], center=true);             // rear battery slot
            }
            knuckles();
            latch_guides();
            body_band_hooks();
            feet();
        }
        knuckle_voids();
        wall_pin_slots();
        button_hole();
    }
    pcb_bosses();
    snap_posts();
}

/* ================= arms (FR canonical, pivot-local, deployed pose) ========= */
module nacelle_arm(inv) {
    rn = 0.6;
    zb = inv ? -0.5 : -1.0;                     // nacelle bottom
    translate([M_loc[0], M_loc[1], zb]) difference() {
        translate([0,0,rn]) minkowski() {
            cylinder(d1=nacelle_d-2*rn, d2=nacelle_d-1-2*rn, h=nacelle_h-2*rn);
            sphere(r=rn, $fn=22);
        }
        if (inv) {   // FRONT: pocket opens DOWN, floor on top, shaft exits below
            translate([0,0,-eps]) cylinder(d=motor_d+0.15, h=nacelle_h-floor_t);
            cylinder(d=motor_d-3, h=nacelle_h*3, center=true);
        } else {     // REAR (v2): pocket opens UP, floor at the bottom
            translate([0,0,floor_t]) cylinder(d=motor_d+0.15, h=nacelle_h+1);
            cylinder(d=motor_d-3, h=nacelle_h*3, center=true);
        }
    }
}
module claw() {
    difference() {
        union() {
            translate([0,0,arm_z0]) cylinder(d=claw_d, h=arm_h);
            rotate([0,0,th_dep]) translate([claw_d/2-0.4, 0, arm_z0+arm_h-0.15])
                sphere(d=det_d-0.2);                                   // deployed detent bump
        }
        translate([0,0,arm_z0-eps]) cylinder(d=pivot_d+0.25, h=arm_h+2);
        rotate([0,0,th_fold+30]) translate([spring_od/2-0.7, 0, arm_z0+arm_h-1.4])
            cylinder(d=leg_d, h=2);                                    // arm-side spring leg
    }
}
module beam_arm() {
    hull() {
        translate([D_loc[0], D_loc[1], arm_zc]) cylinder(d=arm_w, h=arm_h, center=true, $fn=36);
        translate([M_loc[0], M_loc[1], arm_zc]) cylinder(d=arm_w_tip, h=arm_h, center=true, $fn=36);
    }
    hull() {
        translate([0,0,arm_zc]) cylinder(d=claw_d, h=arm_h, center=true);
        translate([D_loc[0], D_loc[1], arm_zc]) cylinder(d=arm_w, h=arm_h, center=true, $fn=36);
    }
}
module latch_pin_arm() {   // riser on the beam + inboard overhang + pin — FOLDED-local
    rotate([0,0,-FOLD_A]) translate([0, 17.0, 0]) {
        translate([riser_lx-1.6, -2.4, arm_z0+arm_h-0.4])
            cube([3.2, 4.8, 11.0-(arm_z0+arm_h)+0.4]);                       // riser
        translate([pin_lx-1.4, -2.4, 9.6]) cube([riser_lx-pin_lx+3.0, 4.8, 1.4]); // overhang
        translate([pin_lx, 0, 9.6]) cylinder(d=pin_d, h=12.8-9.6);           // latch pin
    }
}
module arm_canonical(inv=true) {
    claw();
    beam_arm();
    nacelle_arm(inv);
    latch_pin_arm();
}
module arm_fr() { arm_canonical(true); }
module arm_rr() { mirror([0,1,0]) arm_canonical(false); }
module arm_fl() { mirror([1,0,0]) arm_fr(); }
module arm_rl() { mirror([1,0,0]) arm_rr(); }

/* ================= assemblies / gates ================= */
module arm_at(name, fold) {
    if (name=="fr") translate([ pivot_x,-pivot_y,0]) rotate([0,0, fold*FOLD_A]) arm_fr();
    if (name=="fl") translate([-pivot_x,-pivot_y,0]) rotate([0,0,-fold*FOLD_A]) arm_fl();
    if (name=="rr") translate([ pivot_x, pivot_y,0]) rotate([0,0,-fold*FOLD_A]) arm_rr();
    if (name=="rl") translate([-pivot_x, pivot_y,0]) rotate([0,0, fold*FOLD_A]) arm_rl();
}
module ghost_props(fold) {   // preview only — NEVER in part exports
    for (n=[[1,-1,true],[-1,-1,true],[1,1,false],[-1,1,false]]) {
        sx=n[0]; sy=n[1]; inv=n[2];
        mx = (fold==0) ? sx*motor_off : sx*(pivot_x+crank_out);
        my = (fold==0) ? sy*motor_off : sy*(pivot_y-a_beam);
        translate([mx, my, inv ? prop_z_lo : prop_z_hi])
            %cylinder(d=prop_d, h=0.8, center=true);
    }
}
module assembly(fold=0) {
    color("#cfd4da") body();
    color("#b9bec6") for (n=["fr","fl","rr","rl"]) arm_at(n, fold);
    color("#23272e") latch_u();
    color("#2f6fed") translate([10, -29.6, 10.6]) rotate([90,0,0]) button();  // head outside
    ghost_props(fold);
}
module marker() { translate([60,60,0]) cube(1); }   // keeps empty exports valid
module collision_folded() { marker();
    intersection() { body(); union() { for (n=["fr","fl","rr","rl"]) arm_at(n, 1); } } }
module collision_arms() { marker();
    for (p=[["fr","rr"],["fl","rl"],["fr","rl"],["fl","rr"],["fr","fl"],["rr","rl"]])
        intersection() { arm_at(p[0],1); arm_at(p[1],1); } }
module collision_deployed() { marker();
    intersection() { body(); union() { for (n=["fr","fl","rr","rl"]) arm_at(n, 0); } } }

/* ================= dispatch ================= */
if      (PART=="body")       body();
else if (PART=="arm_front")  arm_fr();
else if (PART=="arm_rear")   arm_rr();
else if (PART=="arm_fr")     arm_fr();
else if (PART=="arm_fl")     arm_fl();
else if (PART=="arm_rr")     arm_rr();
else if (PART=="arm_rl")     arm_rl();
else if (PART=="capot")      capot();
else if (PART=="latch")      latch_u();
else if (PART=="button")     button();
else if (PART=="servo_cam")  servo_cam();
else if (PART=="assembly_folded")   assembly(1);
else if (PART=="collision_folded")  collision_folded();
else if (PART=="collision_arms")    collision_arms();
else if (PART=="collision_deployed") collision_deployed();
else                          assembly(0);
