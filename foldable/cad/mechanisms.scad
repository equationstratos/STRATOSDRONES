// STRATOSDRONE Fr4n7-F — ALTERNATIVE deploy mechanisms (printable demos).
//
// Per the owner's request (photo reference: a casement-window operator —
// crank + worm + toothed sector + scissor arms): three DIFFERENT mechanism
// families that can drive the foldable's release slider (stroke ~3.2 mm) or
// the arms directly. Everything is designed to be as 3-D-PRINTABLE as
// possible: coarse pitches, printed pins, generous clearances. These are
// M0 CONCEPT DEMOS — each prints as a small self-contained kit you can
// actuate by hand; integration into the airframe is the next step.
//
//   for P in worm_crank scissor iris_cam worm_crank_kit scissor_kit iris_cam_kit; do
//     xvfb-run -a openscad -o stl/mech_$P.stl --export-format binstl \
//       -D "PART=\"$P\"" mechanisms.scad; done
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;
eps = 0.01;

PART = "worm_crank";   // worm_crank | scissor | iris_cam  (+ _kit variants)

/* =====================================================================
   1) WORM + CRANK + TOOTHED SECTOR  (the window-operator, miniaturised)
   Crank spins a coarse single-start printed worm; the worm walks a
   toothed sector; the sector's pin drives a slotted slider. Huge
   reduction -> fingertip effort, self-locking like the real hardware. */
w_lead = 6;            // worm lead (coarse + printable)          // TUNE
w_len  = 16; w_d = 10;
s_r    = 16;           // sector pitch radius
module worm() {
    linear_extrude(w_len, twist = -360*w_len/w_lead, convexity = 10)
        translate([1.6, 0]) circle(d = w_d - 2.4);              // offset lobe = thread
    cylinder(d = 4, h = w_len + 8);                             // shaft core
    translate([0, 0, w_len + 6]) rotate([0, 90, 0]) cylinder(d = 3.4, h = 12); // crank pin
    translate([10.4, 0, w_len + 6]) rotate([0, 90, 0]) cylinder(d = 7, h = 2); // knob stop
}
module sector() {
    difference() {
        union() {
            cylinder(r = s_r - 2.2, h = 3.6);
            for (a = [-30 : 12 : 30]) rotate([0, 0, a])          // coarse teeth
                translate([s_r - 2.6, -1.7, 0]) cube([4.2, 3.4, 3.6]);
        }
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 4);        // pivot bore (M3/pin)
    }
    translate([s_r - 7, 0, 3.6 - eps]) cylinder(d = 3.2, h = 4.2);  // drive pin -> slider slot
}
module wc_base() {
    difference() {
        union() {
            translate([-14, -20, 0]) cube([44, 40, 3]);
            translate([22, -6.5, 0]) cube([14, 13, 8]);          // worm saddle
        }
        translate([26, 0, 8]) rotate([-90, 0, 0]) cylinder(d = 4.6, h = 30, center = true); // worm axle
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 4);        // sector pivot
        translate([-11, 8.4, -eps]) cube([18, 3.6, 3.2]);        // slider guide slot
    }
}
module wc_slider() {
    translate([0, 0, 0]) cube([20, 3.2, 2.8]);
    translate([3, -2.2, 2.8]) cube([8, 7.6, 2.6]);               // pin window
}
module worm_crank() {
    color("#cfd4da") wc_base();
    color("#b9bec6") translate([0, 0, 3.2]) rotate([0, 0, 14]) sector();
    color("#2f6fed") translate([26, -11, 8]) rotate([-90, 0, 0]) worm();
    color("#23272e") translate([-11, 8.6, 3.4]) wc_slider();
}
module worm_crank_kit() {   // laid out flat for the plate
    wc_base();
    translate([52, 0, 0]) sector();
    translate([80, 12, 0]) worm();
    translate([70, -16, 0]) wc_slider();
}

/* =====================================================================
   2) DUAL SCISSOR ARMS  (the operator's twin extending arms)
   A central slider drives two links; each link swings a long arm about a
   printed post — both arms sweep out symmetrically, exactly the window
   metaphor. Prints flat; pins are printed Ø3.  */
module sc_arm(L = 34) {
    difference() {
        hull() { cylinder(d = 8, h = 3);
                 translate([L, 0, 0]) cylinder(d = 6, h = 3); }
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 3.4);      // pivot
        translate([12, 0, -eps]) cylinder(d = 3.4, h = 3.4);     // link pin
    }
}
module sc_link(L = 15) {
    difference() {
        hull() { cylinder(d = 6.4, h = 2.6);
                 translate([L, 0, 0]) cylinder(d = 6.4, h = 2.6); }
        for (x = [0, L]) translate([x, 0, -eps]) cylinder(d = 3.4, h = 3);
    }
}
module sc_slider() {
    cube([8, 14, 3]);
    translate([4, 7, 3 - eps]) cylinder(d = 3.2, h = 3.4);       // twin-link pin
    translate([4, 7, 3 - eps]) cylinder(d = 3.2, h = 3.4);
}
module sc_base() {
    difference() {
        translate([-30, -6, 0]) cube([60, 34, 3]);
        translate([-4.2, 6, -eps]) cube([8.4, 22, 3.2]);         // slider channel
    }
    for (s = [-1, 1]) translate([s*22, 0, 3 - eps]) cylinder(d = 3.2, h = 4); // arm posts
}
module scissor() {
    color("#cfd4da") sc_base();
    color("#23272e") translate([-4, 8, 3.2]) sc_slider();
    for (s = [-1, 1]) {
        color("#b9bec6") translate([s*22, 0, 6.6]) rotate([0, 0, s < 0 ? 35 : 145])
            mirror([s < 0 ? 0 : 0, 0, 0]) sc_arm();
        color("#8b929c") translate([0, 15, 4]) rotate([0, 0, s < 0 ? -145 : -35]) sc_link();
    }
}
module scissor_kit() {
    sc_base();
    translate([-28, 42, 0]) sc_arm();
    translate([16, 42, 0]) sc_arm();
    translate([-20, 56, 0]) sc_link();
    translate([4, 56, 0]) sc_link();
    translate([34, 52, 0]) sc_slider();
}

/* =====================================================================
   3) IRIS CAM DISC  (rotary quad-release — one twist frees all four)
   A disc with four Archimedean slots drives four radial pins at once —
   the drone version: the four pins would be the release fingers, the
   disc turned by the servo horn (V2) or a thumb wheel (V1). */
module iris_slot(r0 = 6, r1 = 14, sweep = 70) {
    pts = [for (a = [0 : 4 : sweep]) (r0 + (r1 - r0)*a/sweep) * [cos(a), sin(a)]];
    for (i = [0 : len(pts) - 2]) hull() {
        translate(pts[i])     circle(d = 3.6);
        translate(pts[i + 1]) circle(d = 3.6);
    }
}
module iris_disc() {
    difference() {
        cylinder(d = 34, h = 3);
        for (q = [0 : 90 : 270]) rotate([0, 0, q])
            translate([0, 0, -eps]) linear_extrude(3.2) iris_slot();
        translate([0, 0, -eps]) cylinder(d = 4.7, h = 3.4);      // servo-horn / axle bore
    }
    for (a = [0 : 60 : 300]) rotate([0, 0, a + 45])
        translate([15.4, 0, 0]) cylinder(d = 3, h = 5);          // grip studs (thumb wheel)
}
module iris_base() {
    difference() {
        cylinder(d = 42, h = 3);
        for (q = [0 : 90 : 270]) rotate([0, 0, q])
            translate([5, -2, -eps]) cube([13.5, 4, 3.2]);       // radial pin guides
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 3.4);      // centre axle
    }
}
module iris_pin() {
    cube([7, 3.6, 2.6], center = false);
    translate([1.8, 1.8, 2.6 - eps]) cylinder(d = 3.2, h = 4.4); // follower into the slot
}
module iris_cam() {
    color("#cfd4da") iris_base();
    for (q = [0 : 90 : 270]) rotate([0, 0, q])
        color("#23272e") translate([7, -1.8, 3.2]) iris_pin();
    color("#2f6fed") translate([0, 0, 7.4]) iris_disc();
}
module iris_cam_kit() {
    iris_base();
    translate([48, 0, 0]) iris_disc();
    for (i = [0 : 3]) translate([76, -14 + i*9, 0]) iris_pin();
}

/* =====================================================================
   4) RACK + PINION  (direct drive of the release slider)
   A coarse 8-tooth pinion (thumb wheel on top, or the V2 servo horn)
   walks a straight rack — the simplest possible slider drive. */
rp_r = 8;   // pinion pitch radius
module rp_pinion() {
    difference() {
        union() {
            cylinder(r = rp_r - 1.6, h = 4);
            for (a = [0 : 45 : 315]) rotate([0, 0, a])
                translate([rp_r - 2.4, -1.9, 0]) cube([3.4, 3.8, 4]);
            translate([0, 0, 4 - eps]) cylinder(d = 9, h = 3);      // hub
            for (a = [0 : 60 : 300]) rotate([0, 0, a])              // thumb studs
                translate([0, 0, 7 - eps]) translate([5.5, 0, 0]) cylinder(d = 2.6, h = 2.6);
        }
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 12);          // axle bore
    }
}
module rp_rack() {
    cube([44, 5, 3.4]);
    for (x = [2 : 6.28 : 40])                                       // pitch ~ 2πr/8
        translate([x, 5 - eps, 0]) cube([3.4, 3.2, 3.4]);
    translate([0, -3, 0]) cube([44, 3.2, 3.4]);                     // guide rib
}
module rp_base() {
    difference() {
        translate([-4, -12, 0]) cube([56, 34, 3]);
        translate([1.6, -9.2, -eps]) cube([46, 3.8, 3.3]);          // rib channel
        translate([24, 12.4, -eps]) cylinder(d = 3.4, h = 3.4);     // pinion post bore
    }
    translate([24, 12.4, 0]) cylinder(d = 3.2, h = 8);              // pinion post
}
module rack_pinion() {
    color("#cfd4da") rp_base();
    color("#23272e") translate([2, -6, 3.2]) rp_rack();
    color("#2f6fed") translate([24, 12.4, 3.6]) rp_pinion();
}
module rack_pinion_kit() {
    rp_base();
    translate([0, 30, 0]) rp_rack();
    translate([64, 6, 0]) rp_pinion();
}

/* =====================================================================
   5) ECCENTRIC CAM + LEVER  (quarter-turn cam lock)
   A lever swings an ECCENTRIC disc; its rim pushes a flat follower in a
   straight channel — smooth force multiplication near the end of travel,
   self-holding at the over-centre. */
cl_e = 2.6;  cl_r = 8;   // eccentricity / cam radius
module cl_cam() {
    difference() {
        union() {
            translate([cl_e, 0, 0]) cylinder(r = cl_r, h = 4);      // eccentric disc
            hull() {                                                // lever handle
                cylinder(d = 6, h = 4);
                translate([-22, 0, 0]) cylinder(d = 5, h = 4);
            }
            translate([-22, 0, 4 - eps]) cylinder(d = 4.6, h = 4);  // thumb post
        }
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 4.4);         // pivot bore
    }
}
module cl_follower() {
    cube([5, 16, 4]);
    translate([5 - eps, 4, 0]) cube([8, 8, 4]);                     // push tongue
}
module cl_base() {
    difference() {
        translate([-30, -14, 0]) cube([56, 30, 3]);
        translate([12.6, -3.8, -eps]) cube([5.6, 17, 3.3]);         // follower channel
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 3.4);         // cam post bore
    }
    translate([0, 0, 0]) cylinder(d = 3.2, h = 8);                  // cam post
}
module cam_lever() {
    color("#cfd4da") cl_base();
    color("#2f6fed") translate([0, 0, 3.4]) rotate([0, 0, 25]) cl_cam();
    color("#23272e") translate([13, -3.5, 3.2]) cl_follower();
}
module cam_lever_kit() {
    cl_base();
    translate([-4, 26, 0]) cl_cam();
    translate([34, 24, 0]) cl_follower();
}

/* =====================================================================
   6) TOGGLE / OVER-CENTRE LINKAGE  (genouillère)
   Handle + link snap past the dead centre: holds the pad CLAMPED with
   zero holding force (like machinist toggle clamps) — a candidate for
   holding the arms folded with a positive lock. */
tg_a = 12;   // handle crank length
tg_b = 16;   // link length
module tg_handle() {
    difference() {
        union() {
            hull() { cylinder(d = 8, h = 3.6);
                     translate([tg_a, 0, 0]) cylinder(d = 6.4, h = 3.6); }
            hull() { cylinder(d = 8, h = 3.6);
                     translate([-20, 6, 0]) cylinder(d = 5, h = 3.6); }   // handle grip
        }
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 4);           // pivot
        translate([tg_a, 0, -eps]) cylinder(d = 3.4, h = 4);        // link pin bore
    }
    translate([-20, 6, 3.6 - eps]) cylinder(d = 4.4, h = 4);        // thumb post
}
module tg_link() {
    difference() {
        hull() { cylinder(d = 6.4, h = 3);
                 translate([tg_b, 0, 0]) cylinder(d = 6.4, h = 3); }
        for (x = [0, tg_b]) translate([x, 0, -eps]) cylinder(d = 3.4, h = 3.4);
    }
}
module tg_pad() {
    cube([10, 8, 4]);
    translate([5, 4, 4 - eps]) cylinder(d = 3.2, h = 4.2);          // link pin
}
module tg_base() {
    difference() {
        translate([-16, -10, 0]) cube([52, 26, 3]);
        translate([13.6, -4.2, -eps]) cube([20, 8.6, 3.3]);         // pad channel
        translate([0, 0, -eps]) cylinder(d = 3.4, h = 3.4);
    }
    translate([0, 0, 0]) cylinder(d = 3.2, h = 8);                  // handle post
}
module toggle_clamp() {
    color("#cfd4da") tg_base();
    color("#2f6fed") translate([0, 0, 3.4]) rotate([0, 0, 40]) tg_handle();
    color("#8b929c") translate([tg_a*cos(40), tg_a*sin(40), 7.2]) rotate([0, 0, -22]) tg_link();
    color("#23272e") translate([14, -4, 3.2]) tg_pad();
}
module toggle_clamp_kit() {
    tg_base();
    translate([-10, 24, 0]) tg_handle();
    translate([26, 22, 0]) tg_link();
    translate([44, 20, 0]) tg_pad();
}

/* ================= dispatch ================= */
if      (PART == "worm_crank")       worm_crank();
else if (PART == "worm_crank_kit")   worm_crank_kit();
else if (PART == "scissor")          scissor();
else if (PART == "scissor_kit")      scissor_kit();
else if (PART == "iris_cam")         iris_cam();
else if (PART == "iris_cam_kit")     iris_cam_kit();
else if (PART == "rack_pinion")      rack_pinion();
else if (PART == "rack_pinion_kit")  rack_pinion_kit();
else if (PART == "cam_lever")        cam_lever();
else if (PART == "cam_lever_kit")    cam_lever_kit();
else if (PART == "toggle_clamp")     toggle_clamp();
else if (PART == "toggle_clamp_kit") toggle_clamp_kit();
// ---- per-part exports for the mechanisms VIEWER (animated) ----
else if (PART == "p_wc_base")   wc_base();
else if (PART == "p_wc_worm")   worm();
else if (PART == "p_wc_sector") sector();
else if (PART == "p_wc_slider") wc_slider();
else if (PART == "p_sc_base")   sc_base();
else if (PART == "p_sc_arm")    sc_arm();
else if (PART == "p_sc_link")   sc_link();
else if (PART == "p_sc_slider") sc_slider();
else if (PART == "p_ir_base")   iris_base();
else if (PART == "p_ir_disc")   iris_disc();
else if (PART == "p_ir_pin")    iris_pin();
else if (PART == "p_rp_base")   rp_base();
else if (PART == "p_rp_pinion") rp_pinion();
else if (PART == "p_rp_rack")   rp_rack();
else if (PART == "p_cl_base")   cl_base();
else if (PART == "p_cl_cam")    cl_cam();
else if (PART == "p_cl_follower") cl_follower();
else if (PART == "p_tg_base")   tg_base();
else if (PART == "p_tg_handle") tg_handle();
else if (PART == "p_tg_link")   tg_link();
else if (PART == "p_tg_pad")    tg_pad();
else                             worm_crank();
