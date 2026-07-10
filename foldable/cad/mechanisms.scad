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

/* ================= dispatch ================= */
if      (PART == "worm_crank")     worm_crank();
else if (PART == "worm_crank_kit") worm_crank_kit();
else if (PART == "scissor")        scissor();
else if (PART == "scissor_kit")    scissor_kit();
else if (PART == "iris_cam")       iris_cam();
else if (PART == "iris_cam_kit")   iris_cam_kit();
else                               worm_crank();
