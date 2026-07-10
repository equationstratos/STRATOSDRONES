// STRATOSDRONE Fr4n7-F — FOLDABLE-arm Tello-class frame (v1, M0).
//
// Concept credit: inspired by Thingiverse thing:1604440 (foldable mini quad:
// STRAIGHT flat arms pivoting on corner posts, folding alongside the body)
// — https://www.thingiverse.com/thing:1604440 — CLEAN-ROOM: this file is our
// own original parametric geometry, nothing copied from that mesh. Key twist
// from the project owner's printed prototype: the FRONT arms are mounted
// INVERTED (pod flipped, prop below the belly) so the folded arms never
// cross — front folds rearward in a LOW prop plane, rear folds forward in a
// HIGH plane along the same flank.
//
// v1 (per owner feedback): STRAIGHT Thingiverse-style arms on corner OUTRIGGER
// ears; the folded arm is moored TO THE BODY AT THE MOTOR RING — a flexing
// snap CRADLE grips a groove at the nacelle's mid-height ("l'encoche au
// milieu du cercle récepteur du moteur") — and the release button moved ON
// TOP (vertical pin, conical cam onto the slider).
//
// Both versions share torsion-spring pivots + the snap cradles + the sliding
// EJECTOR latch:
//   V1 "manuelle":  press the TOP button -> slider cams the nacelles out of
//                   their cradles -> springs deploy the arms. Zero electronics.
//   V2 "commande":  a nano-servo cam drives the same slider — `deploy` SDK
//                   verb (spec in ../DESIGN.md — NOT yet in firmware).
// Folding back needs NO button: push the arms in until the cradles click.
//
//   for P in body capot arm_front arm_rear arm_fr arm_fl arm_rr arm_rl latch button servo_cam; do
//     xvfb-run -a openscad -o stl/$P.stl --export-format binstl \
//       -D "PART=\"$P\"" frame_foldable.scad; done
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;
eps = 0.01;

PART = "assembly";   // body|capot|arm_front|arm_rear|arm_fr|arm_fl|arm_rr|arm_rl|
                     // latch|button|servo_cam|assembly|assembly_folded|
                     // collision_deployed|collision_folded|collision_arms

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
arm_h = 5.6; arm_w = 8.0; prop_d = 76.2;   // STRAIGHT flat bar, uniform width

/* ---------------- folding mechanism parameters ----------------
   (everything marked TUNE is a first-print estimate) */
pivot_x   = 24.5;   pivot_y = 36;   // pivots INSET into the body corner, like
                                    // the real thing:1604440 (theirs: 6 mm in
                                    // from the plate edge, M3)             // TUNE
crank_out = 3.3;                    // slight paddle crank so the folded beam
                                    // centreline lands at x = 27.8 (nacelle
                                    // clears the wall by 0.45)             // TUNE
pivot_d   = 3.2;                    // M3 x 14 + nyloc (4x) — as the original
claw_d    = 8.0;                    // arm pivot barrel (M3 core needs meat)
jaw_b     = 2.4;                    // bottom clevis jaw (nyloc pocket underneath)
slot_h    = 6.0;                    // clevis slot height (claw 5.6 + 0.4 clr)
jaw_t     = 2.6;                    // top clevis jaw (torsion-spring pocket inside)
knuckle_d = 9.6;                    // clevis tower Ø                       // TUNE
spring_od = 7.4; spring_pk = 2.2;   // torsion spring pocket Ø / depth (0.5 mm wire)
leg_d     = 1.4;                    // spring leg holes
det_d     = 1.8;                    // deployed detent bump/recess          // TUNE
arm_z0    = jaw_b + 0.2;            // beam/claw bottom (2.6)
arm_zc    = arm_z0 + arm_h/2;       // beam centre (5.4)
tab_z0 = 8.6; tab_z1 = 11.3;        // arm-side snap TAB band (above the beam)
tab_w  = 3.6; tab_t = 1.7;          // tab plan size
lip_h  = 1.0;                       // tab hook lip, catches the window edge // TUNE
latch_travel = 3.2;                 // slider stroke (1.5 engages, rest margin) // TUNE
foot_h    = 8;                      // landing feet below the belly
prop_z_lo = -3.5;                   // FRONT (inverted) prop plane — under the belly
prop_z_hi = 19.7;                   // REAR prop plane — above the capot (as v2)

/* ---------------- fold math (documented in ../DESIGN.md) ----------------
   FR canonical, arm local frame = pivot at origin, deployed pose, front = -Y.
   Slightly CRANKED paddle: folded beam axis parallel to the flank, offset
   crank_out outboard of the (inset) pivot. */
L_pm    = norm([motor_off-pivot_x, motor_off-pivot_y]);      // 18.15 pivot->motor
a_beam  = sqrt(L_pm*L_pm - crank_out*crank_out);             // 17.85 along-beam
th_dep  = atan2(-(motor_off-pivot_y), motor_off-pivot_x);    // -18.38° deployed dir
th_fold = atan2(a_beam, crank_out);                          //  79.5° folded dir
FOLD_A  = th_fold - th_dep;                                  //  97.9° fold sweep
M_loc   = [motor_off-pivot_x, -(motor_off-pivot_y)];         // motor (17.22,-5.72)
D_loc   = crank_out*[cos(th_dep-90), sin(th_dep-90)];        // dogleg foot (deployed)
dock_y  = pivot_y - a_beam;                                  // folded nacelle |y| = 18.15
echo(str("ASSERT wheelbase=", wheelbase, "  FOLD_A=", FOLD_A,
         "  folded_motor=(", pivot_x + crank_out, ",", dock_y, ")"));

/* landing feet — inside the "dead diamond" that no blade (folded, aligned or
   mid-swing fan) sweeps at prop_z_lo (re-checked for the ear pivots). */
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

/* ============ corner LOBES — sandwich hinges in the body line ============
   Thingiverse-style elegance: each pivot lives inside a rounded corner LOBE
   — two stacked plates (below and above the arm) that flow out of the pod
   corner, the arm paddle rotating in the gap between them. Reads as one
   sculpted silhouette instead of a bolted-on ear. */
lobe_d = 12.0;
module lobe_slab_local(z0, h) {
    hull() {   // compact corner plate: pivot boss INSET like the original —
               // blended into both pod faces, nothing reads as an add-on
        translate([0,0,z0])          cylinder(d=lobe_d, h=h);
        translate([-7.5, -1.5, z0])  cylinder(d=9, h=h);   // into the side wall
        translate([-3.5,  2.6, z0])  cylinder(d=9, h=h);   // into the end wall
    }
}
module knuckle_tower_local() {
    lobe_slab_local(0, jaw_b);                            // lower plate
    lobe_slab_local(jaw_b + slot_h, jaw_t);               // upper plate
    // C-pillar around the barrel keeps the sandwich tied at the slot band
    cylinder(d=knuckle_d, h=jaw_b + slot_h + jaw_t);
}
module knuckle_cuts_local() {
    translate([0,0,-eps]) cylinder(d=pivot_d, h=20);                  // M3 bore
    translate([0,0,-eps]) cylinder(d=5.6/cos(30), h=2.3, $fn=6);      // M3 nyloc pocket
    translate([0,0,jaw_b-0.2]) cylinder(d=claw_d+0.5, h=slot_h+0.4);  // barrel bore
    translate([0,0,jaw_b+slot_h-eps]) cylinder(d=spring_od, h=spring_pk+eps); // spring pocket
    rotate([0,0,th_fold+25]) translate([spring_od/2-0.7, 0, jaw_b+slot_h-eps])
        cylinder(d=leg_d, h=jaw_t+2);                                 // body-side spring leg
    // detent: shallow groove along the sweep + deeper click at deployed
    for (a=[th_dep : 8 : th_fold])
        rotate([0,0,a]) translate([claw_d/2-0.4, 0, jaw_b+slot_h+0.1]) sphere(d=det_d+0.1, $fn=24);
    rotate([0,0,th_dep]) translate([claw_d/2-0.4, 0, jaw_b+slot_h+0.05]) sphere(d=det_d+0.4, $fn=24);
    // clevis mouth: fan for the straight beam over the full sweep. The bar
    // root flares from the claw Ø to full width over 7 mm, so the opening
    // needs ±72°; the extrude stops AT the slot ceiling (detent lives there).
    a0 = th_dep - 110; a1 = th_fold + 88;  // cranked paddle root wraps the barrel:
                                           // dogleg side opens −110° (C-pillar ~64°,
                                           // the sandwich plates carry the load)
    translate([0,0,jaw_b-0.2]) linear_extrude(slot_h+0.2)
        polygon(concat([[0,0]], [for (a=[a0 : 6 : a1]) 12*[cos(a),sin(a)]],
                       [12*[cos(a1),sin(a1)]]));
}
module knuckles()      { for (sx=[-1,1], sy=[-1,1]) at_corner(sx,sy) knuckle_tower_local(); }
module knuckle_voids() { for (sx=[-1,1], sy=[-1,1]) at_corner(sx,sy) knuckle_cuts_local(); }

/* ============ mooring cradles — the arm docks AT THE MOTOR RING ============
   A flexing C-cradle on each flank grips the nacelle's mid-height GROOVE
   when folded (the owner's "encoche au milieu du cercle récepteur") — best
   grip: it holds the heavy end. The sliding latch EJECTS the nacelles. */
/* ============ arm-side snap TABS (« les accroches sont sur les bras ») ====
   Nothing protrudes from the body: each arm carries a small flexible tab on
   its nacelle that enters a flush WINDOW in the side wall when folded; a
   sideways barb hooks the wall's inner face. The slider's release fingers
   deflect the tabs (+Y), the barbs clear the edge, the springs deploy. */
win_y0 = 3.2;  win_y1 = 2.4;        // window span rel. dock: [-win_y0, +win_y1]
                                    // (uniform WORLD layout on all four corners:
                                    //  barb pokes past the FRONT edge, shank
                                    //  deflects REARWARD, finger pushes +Y)

/* ================= ejector latch (shared V1/V2) =================
   Slider rails inside the walls; fingers pass through wall slots and end in
   45° wedges behind each docked nacelle. Slider pushed REARWARD 4.5 mm ->
   the wedges cam the nacelles OUTBOARD past the cradle lips -> torsion
   springs finish the deploy. Fold-in needs no button (cradles just click). */
rail_x  = 18.1;
rail_z0 = 8.6; rail_z1 = 11.4;     // rails ride ABOVE the PCB (top 5.8) and the beams
btn_y   = -19;                     // release button ON TOP, centred on the axis
                                   // (clear of the battery nose at y -16 and the
                                   //  ToF window at (0,-3.9) — the pin cannot cross
                                   //  the PCB, so it is guided by a bridge sleeve)
module tab_windows() {   // flush wall windows the arm tabs snap into
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*(pod_x/2 - wall/2), sy*dock_y - (win_y0-win_y1)/2, (8.4+11.6)/2])
            cube([wall+2.6, win_y0+win_y1, 11.6-8.4], center=true);
}
module latch_guides() {   // ledges the rails ride on — anchored into the walls
    for (sx=[-1,1], gy=[-11, 11])
        translate([sx*18.6 - 1.5, gy-3, rail_z0-0.7]) cube([3.0, 6, 0.7]);
}
module latch_u() {        // ONE printed part: rails + release fingers + bridge
    for (sx=[-1,1]) {
        translate([sx*rail_x-1.0, -26, rail_z0]) cube([2.0, 52, rail_z1-rail_z0]);
        for (sy=[-1,1])   // straight fingers inside the windows: slider +3.2
                          // rearward -> they deflect the tab shanks, barbs clear
            translate([sx*20.3-1.1, sy*dock_y - 2.0, rail_z0+0.2])
                cube([2.2, 1.4, rail_z1-rail_z0-0.4]);
        translate([sx*rail_x-0.6, 25.4, rail_z0]) cube([1.2, 2.6, 5.2]);   // band hook
    }
    difference() {   // centre-front bridge: button sleeve + cam notch
        union() {
            translate([-rail_x, btn_y-1.6, rail_z0]) cube([2*rail_x, 3.2, rail_z1-rail_z0]);
            translate([0, btn_y, rail_z0]) cylinder(d=8.2, h=3.8);          // guide sleeve
        }
        translate([0, btn_y+0.8, rail_z0-eps]) cylinder(d1=2.6, d2=5.2, h=4.0);  // cone seat
        translate([-2.6, btn_y-3.4, rail_z0-eps]) cube([5.2, 3.6, 4.0]);    // open frontward
        translate([0, btn_y, rail_z0+1.2]) cylinder(d=4.9, h=4);            // shank pass
    }
}
module body_band_hooks() {
    for (sx=[-1,1]) translate([sx*rail_x-0.6, 30.5, floor_t-eps]) cube([1.2, 2.6, 5.2]);
}
module button() {         // TOP pin (absolute z): cone -> shank -> head
    translate([0,0,6.4])  cylinder(d1=2.2, d2=4.6, h=2.4);   // cam cone (on the bridge seat)
    translate([0,0,8.8])  cylinder(d=4.6, h=10.0);           // shank (sleeve + capot bores)
    translate([0,0,18.8]) cylinder(d=8.4, h=2.0);            // head, proud of the capot
}
module servo_cam() {      // V2 cam disc for a 3.7 g nano-servo horn
    difference() {
        union() { cylinder(d=9, h=3); translate([2.6,0,0]) cylinder(d=6, h=3); }
        translate([0,0,-eps]) cylinder(d=4.7, h=3.4);
        for (a=[0:90:270]) rotate([0,0,a]) translate([3.4,0,-eps]) cylinder(d=1.2, h=3.4);
    }
}

/* ================= capot (foldable-specific lid) ================= */
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
        translate([0, btn_y, half_h-1]) cylinder(d=5.2, h=4);   // centred TOP-button bore
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
        tab_windows();
    }
    pcb_bosses();
    snap_posts();
}

/* ============ arms — STRAIGHT Thingiverse-style flat bars ============
   FR canonical, pivot-local, deployed pose. The bar runs pivot -> motor;
   the nacelle carries the mid-height mooring GROOVE the cradles grip. */
module nacelle_arm(inv) {
    rn = 0.6;
    zb = inv ? -0.5 : -1.0;
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
/* the snap TAB — built in FOLDED-local coords so its shank/barb land exactly
   in the wall window; s flips the layout so all four barbs point FORWARD in
   world coords (one slider direction releases everything). */
module snap_tab(s) {
    rotate([0,0,-FOLD_A]) translate([crank_out, a_beam, 0]) {
        translate([-nacelle_d/2-2.45, (s>0 ? -0.4 : -1.0), tab_z0])
            cube([2.95, 1.4, tab_z1-tab_z0]);                  // flexible shank
        translate([-nacelle_d/2-2.85, (s>0 ? -4.0 : -1.0), tab_z0])
            cube([0.8, 5.0, 1.6]);                             // barb — fully BEHIND the
                                                               // wall inner face (hooks it
                                                               // under load) // TUNE ramp
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
        rotate([0,0,th_fold+25]) translate([spring_od/2-0.7, 0, arm_z0+arm_h-1.4])
            cylinder(d=leg_d, h=2);                                    // arm-side spring leg
    }
}
module beam_arm() {   // sculpted flat PADDLE (thing:1604440 style) with the
    ub = (M_loc - D_loc) / norm(M_loc - D_loc);   // slight crank built in
    vb = [-ub[1], ub[0]];
    S  = D_loc + 5.5*ub;              // shoulder centre
    W  = D_loc + 10.5*ub;             // waist centre
    difference() {
        hull() {
            translate([0,0,arm_zc])                 cylinder(d=claw_d, h=arm_h, center=true, $fn=36);
            translate([S[0], S[1], arm_zc])         cylinder(d=11.0,   h=arm_h, center=true, $fn=48);
            translate([M_loc[0], M_loc[1], arm_zc]) cylinder(d=12.4,   h=arm_h, center=true, $fn=48);
        }
        // concave flank scoops -> the elegant waist
        for (s=[-1,1])
            translate([W[0] + s*14.4*vb[0], W[1] + s*14.4*vb[1], arm_zc])
                cylinder(r=9.6, h=arm_h+2, center=true, $fn=64);
    }
}
module arm_canonical(inv=true) {
    claw();
    beam_arm();
    nacelle_arm(inv);
    snap_tab(inv ? 1 : -1);   // mirrored corners -> uniform world layout
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
        mx = (fold==0) ? sx*motor_off : sx*pivot_x;
        my = (fold==0) ? sy*motor_off : sy*dock_y;
        translate([mx, my, inv ? prop_z_lo : prop_z_hi])
            %cylinder(d=prop_d, h=0.8, center=true);
    }
}
module assembly(fold=0) {
    color("#cfd4da") body();
    color("#b9bec6") for (n=["fr","fl","rr","rl"]) arm_at(n, fold);
    color("#23272e") latch_u();
    color("#2f6fed") translate([0, btn_y, 0]) button();
    ghost_props(fold);
}
module marker() { translate([70,70,0]) cube(1); }   // keeps empty exports valid
module collision_folded() { marker();
    intersection() { body(); union() { for (n=["fr","fl","rr","rl"]) arm_at(n, 1); } } }
module collision_arms() { marker();
    for (p=[["fr","rr"],["fl","rl"],["fr","rl"],["fl","rr"],["fr","fl"],["rr","rl"]])
        intersection() { arm_at(p[0],1); arm_at(p[1],1); } }
module collision_deployed() { marker();
    intersection() { body(); union() { for (n=["fr","fl","rr","rl"]) arm_at(n, 0); } } }

/* ================= dispatch ================= */
if      (PART=="body")       body();
else if (PART=="capot")      capot();
else if (PART=="arm_front")  arm_fr();
else if (PART=="arm_rear")   arm_rr();
else if (PART=="arm_fr")     arm_fr();
else if (PART=="arm_fl")     arm_fl();
else if (PART=="arm_rr")     arm_rr();
else if (PART=="arm_rl")     arm_rl();
else if (PART=="latch")      latch_u();
else if (PART=="button")     button();
else if (PART=="servo_cam")  servo_cam();
else if (PART=="assembly_folded")   assembly(1);
else if (PART=="collision_folded")  collision_folded();
else if (PART=="collision_arms")    collision_arms();
else if (PART=="collision_deployed") collision_deployed();
else                          assembly(0);
