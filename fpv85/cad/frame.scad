// STRATOSDRONE Fr4n8-001 (fpv85) — outdoor micro-FPV frame, 85 mm class (v1, M0).
//
// Clean-room design. Visual references (owner's photos, measurement/style
// only, nothing copied): an ~84 x 83 x 32 mm "Eagle-class" micro FPV quad
// (whence the overall footprint and the 14000KV 2S motor class) and a
// white-side-plate toothpick canopy — v3 follows the owner's Walle FPV
// Eagle2 reference (wallefpv.com, photos: visual reference ONLY, clean-room)
// : TWO LONG PARALLEL RAILS the full body length (open flat tunnel, camera
// unit upright at the nose INSIDE the rails, XT30 + antennas out the tail),
// trussed arms, diamond plate cutouts. Our own parametric OpenSCAD.
//
// Architecture: one printed UNIBODY bottom plate (X arms to four 0802-class
// motor pods + whoop-standard 25.5x25.5 AIO mount + battery strap slots +
// landing feet) and a side-plate CANOPY holding the tilted analog nano cam,
// the VTX bay and the ELRS RX shelf. The shared STRATOS FPV AIO board
// (hardware/pcb_fpv, 32x32) drops on the four M2 posts.
//
//   for P in frame canopy; do
//     xvfb-run -a openscad -o stl/$P.stl --export-format binstl \
//       -D "PART=\"$P\"" frame.scad; done
//   (PART="assembly" renders the preview used in cad/preview/)
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;
eps = 0.01;

PART = "assembly";   // frame | canopy | assembly

/* ---------------- master parameters (fpv85; keep fpv2/cad in sync) -------- */
wheelbase = 85;        // motor-to-motor diagonal — overall ≈ 0.707*wb + prop ≈ 100.
                       // v3.2: 65 -> 85. The class NAME is the wheelbase (Meteor85
                       // convention); at 65 the Ø40 discs swept the rail ends
                       // (motor->rail-corner ≈ 12 mm < 20 mm radius = collision).
prop_d    = 40;        // 1.6" tri-blade                                  // TUNE
motor_bc  = 6.6;       // 0802-class mount: 3x M1.4 on a 6.6 mm circle    // TUNE
motor_hole = 1.5;      // M1.4 clearance
pod_d     = 12.6;      // motor pod outer Ø (0802 base ~9.4 + wall)
shaft_d   = 4.2;       // prop-shaft / wire pass-through
arm_w     = 6.4;       // arm width                                       // TUNE
plate_t   = 3.0;       // unibody plate thickness (PLA-CF / PETG)
aio       = 25.5;      // whoop AIO mount pitch (the shared FPV AIO board)
aio_r     = 25.5*sqrt(2)/2;  // 18.03 — the BOARD IS ROTATED 45 deg (Eagle2): holes land ON the axes
aio_post_d = 4.8;      // M2 posts under the board (soft-mount grommets)
aio_post_h = 3.2;
centre_w  = 34;        // centre pad square (32x32 board + margin)
batt_w    = 18;        // 2S 450 mAh pack width                            // TUNE
strap_w   = 7; strap_l = 2.2;   // battery strap slots
cam_w     = 14.4;      // nano cam side-screw width (14 mm cams + clr)     // TUNE
cam_tilt  = 15;        // uptilt (deg)                                     // TUNE
foot_h    = 7;         // pod feet (the pack under the plate lands first — toothpick way)
batt_t    = 8;         // 2S pack thickness (strapped UNDER the plate)      // TUNE
canopy_l  = 42;        // RAIL length — v3.2: ends pulled clear of the prop discs
canopy_w  = 22;        // outside width across the two side plates
canopy_h  = 12;        // rail height — low flat tunnel            // TUNE
pinch     = 0;         // Eagle2 rails are PARALLEL (kept as a param)
wall      = 2.0;       // side-plate / deck thickness

posXY = wheelbase/2/sqrt(2);          // 30.05 — motor centres (X layout)
echo(str("ASSERT wheelbase=", wheelbase,
         "  overall=", 0.707*wheelbase + prop_d, "  posXY=", posXY));

/* ---------------- helpers ---------------- */
module rrect(x, y, r, h) { linear_extrude(h) offset(r) square([x-2*r, y-2*r], center=true); }

/* ---------------- unibody bottom plate ---------------- */
module motor_pod() {
    difference() {
        cylinder(d=pod_d, h=plate_t);
        translate([0,0,-eps]) cylinder(d=shaft_d, h=plate_t+2*eps);
        for (a=[0:120:240]) rotate([0,0,a+30])
            translate([motor_bc/2, 0, -eps]) cylinder(d=motor_hole, h=plate_t+2*eps);
    }
}
module foot() {   // paw pad + short bumper under each pod (pack lands first)
    translate([0,0,-1.8]) rrect(11, 11, 3.4, 1.8);          // rounded paw pad
    translate([0,0,-6.6]) cylinder(d1=4.2, d2=6.2, h=4.8);  // bumper
}
module arm(ang) {   // TRUSSED arm (Eagle2 style): tapered blade + lengthwise slot
    rotate([0,0,ang]) difference() {
        hull() {
            translate([10, -(arm_w+2.4)/2, 0]) cube([eps, arm_w+2.4, plate_t]);
            translate([sqrt(2)*posXY - pod_d/2 + 1.5, -(arm_w-1.8)/2, 0]) cube([eps, arm_w-1.8, plate_t]);
        }
        hull() for (r=[14, sqrt(2)*posXY - pod_d/2 - 3.5])
            translate([r, 0, -eps]) cylinder(d=2.6, h=plate_t+2*eps);
    }
}
module centre_pad() {
    difference() {
        linear_extrude(plate_t) offset(3) oct(centre_w-6, centre_w-2);  // diamond-cut waist
        // DIAMOND-LATTICE cutouts (Eagle2 bottom-plate look): centre diamond,
        // Y-axis lozenges, X diamonds + 4 small corner diamonds
        translate([0, 0, -eps]) rotate([0,0,45]) rrect(7.2, 7.2, 1.2, plate_t+2*eps);
        for (sy=[-1,1]) translate([0, sy*11.5, -eps]) linear_extrude(plate_t+2*eps)
            polygon([[0,-5.6],[3.2,0],[0,5.6],[-3.2,0]]);
        for (sx=[-1,1]) translate([sx*10.5, 0, -eps]) rotate([0,0,45])
            rrect(5.6, 5.6, 1.2, plate_t+2*eps);
        for (sx=[-1,1], sy=[-1,1]) translate([sx*7.5, sy*13.5, -eps]) rotate([0,0,45])
            rrect(3.0, 3.0, 0.9, plate_t+2*eps);
        // battery strap slots (pack lies along Y, strapped to the plate)
        for (sx=[-1,1], sy=[-1,1])
            translate([sx*(batt_w/2+2.6), sy*7.5, -eps])
                rrect(strap_l, strap_w, 1, plate_t+2*eps);
    }
    // AIO posts — board rotated 45 deg, holes ON the axes (front/rear/sides)
    for (p=[[1,0],[-1,0],[0,1],[0,-1]]) translate([p[0]*aio_r, p[1]*aio_r, 0]) {
        cylinder(d=9, h=plate_t);                                   // boss pad into the plate
        translate([0,0,plate_t-eps]) difference() {
            cylinder(d=aio_post_d, h=aio_post_h);
            translate([0,0,0.8]) cylinder(d=1.7, h=aio_post_h);
        }
    }
}
module frame() {
    for (sx=[-1,1], sy=[-1,1]) {
        translate([sx*posXY, sy*posXY, 0]) motor_pod();
        translate([sx*posXY, sy*posXY, 0]) foot();
        arm(atan2(sy, sx));
    }
    centre_pad();
}

/* ---------------- canopy (side plates + spine, camera + VTX + RX) -------- */
module plate_profile() {   // RAIL silhouette (2D): long, low, flat top,
    L = canopy_l/2; H = canopy_h;  // chamfered ends, trussed cutouts
    difference() {
        polygon([[-L, 0], [L, 0], [L, H-3], [L-5, H], [-L+8, H], [-L, H-3.5]]);
        polygon([[-L+6, 2.5], [-L+16, 2.5], [-L+13, H-3]]);              // nose triangle
        polygon([[-2, 2.5], [8, 2.5], [9.5, H-3.6], [0, H-3.6]]);        // mid slot
        polygon([[L-10, 2.5], [L-5.5, 2.5], [L-4.5, H-3.6], [L-9, H-3.6]]); // tail slot
        // (v3.2: slots re-spaced — with the shorter rails the old tail slot
        //  collided with the mid slot into a zero-width cusp = broken mesh)
        translate([-L+3.2, H/2]) circle(d=2.2);                          // cam clamp screw
    }
}
module canopy() {
    L = canopy_l/2; H = canopy_h;
    // centreline COLUMNS down to the rotated board's front/rear holes
    // (the Eagle2's visible centre screws): brace -> column -> board -> post
    for (sy=[-1,1]) translate([0, sy*aio_r, 0]) difference() {
        cylinder(d=5.6, h=2.6+H-wall+eps);
        translate([0,0,-eps]) cylinder(d=2.2, h=2.6+H+1);
    }
    // TWO PARALLEL RAILS, full body length (the Eagle2 tunnel)
    for (sx=[-1,1]) translate([sx*(canopy_w/2-wall), 0, 2.6])
        rotate([0,0,-sx*pinch]) rotate([90,0,90])
            linear_extrude(wall, center=true) plate_profile();
    // open tunnel: braces over the two centreline columns
    translate([0, -aio_r, 2.6+H-wall]) rrect(canopy_w-2, 5, 1.4, wall);
    translate([0, aio_r, 2.6+H-wall]) rrect(canopy_w-2, 5, 1.4, wall);
    // exposed screw heads along the rails (photo look): a row of 5 domed
    // button heads + hex socket per side, WELDED 0.6 into the rail on the
    // always-solid lower band of the profile (v3.1 floated them 1.35 mm
    // off the outer face = unprintable islands)
    for (sx=[-1,1], yy=[-16,-8,0,8,16])
        translate([sx*(canopy_w/2-wall+0.4), yy, 2.6+1.6]) rotate([0,sx*90,0])
            difference() { $fn = 24;   // Ø3 heads: 64 facets would x4 the STL
                union() {
                    cylinder(d=3.0, h=1.2);
                    translate([0,0,1.2]) scale([1,1,0.5]) sphere(d=3.0);
                }
                translate([0,0,1.5]) cylinder(d=1.5, h=1.4, $fn=6);
            }
    // raked antenna seats at the tail (tubes exit between the rails)
    translate([0, L-3, 2.6+H/2-1]) difference() {
        rrect(canopy_w-5, 4.5, 1.4, 4);
        for (sx=[-1,1]) translate([sx*5, 0, -eps]) rotate([-40,0,0]) cylinder(d=2.1, h=10);
    }
}

/* ============ ELECTRONICS (viewer/preview meshes — buy, don't print) ====== */
module board() {           // the shared STRATOS FPV AIO, 32x32 green
    color("#0a5a30") rrect(32, 32, 2.5, 1.6);
    color("#caa14a") for (sx=[-1,1], sy=[-1,1])
        translate([sx*aio/2, sy*aio/2, -eps]) cylinder(d=4, h=1.8);
}
module airunit() {         // finned video/air-unit box (photo look)
    difference() {
        rrect(16, 19, 1.6, 13);
        for (i=[-3:3]) translate([i*2.1, -1.5, 4]) cube([1.1, 14, 12], center=false);
    }
    translate([0, 9.5, 4]) rotate([-90,0,0]) cylinder(d=3.2, h=2.4);   // rear plug
}
module fpvcam() {          // upright HD unit at the nose (Eagle2/O4 style)
    rrect(13.5, 11, 1.6, 15);                              // vertical body in the tunnel
    for (i=[0:4]) translate([-6.2, -2+i*2.0, 14.2]) cube([12.4, 1.1, 1.6]);  // top fins
    translate([0, -5.4, 9]) rotate([90-cam_tilt,0,0]) {
        cylinder(d=11.6, h=4.6);                           // lens barrel forward
        translate([0,0,4.6]) cylinder(d=9.2, h=1.6);       // ring
        color("#0b1e3a") translate([0,0,6.0]) sphere(d=7.4);   // glass
    }
}
module rxmod() {           // ELRS RX + wire antenna
    rrect(11, 14, 1.2, 2.4);
    translate([2.5, 6.5, 1.2]) rotate([-60,0,0]) cylinder(d=1.1, h=26);
}
module battery_pack() {    // 2S pack strapped UNDER the plate + XT30 pigtail
    rn=2.2;
    minkowski() { cube([batt_w-2*rn, 34-2*rn, batt_t-2*rn], center=true); sphere(r=rn, $fn=24); }
    translate([0, 16.5, batt_t/2+4]) cylinder(d=3.4, h=9);                        // leads up the tail
    color("#f5b301") translate([0, 19.5, batt_t/2+14]) cube([7, 11, 6.4], center=true);  // XT30 at the tunnel tail
}
module antennas() {        // two rear antennas, raked back (photo)
    for (sx=[-1,1]) translate([sx*5, 0.78*canopy_l/2, 0.43*canopy_h+1])
        rotate([-35,0,0]) {
            cylinder(d=1.7, h=34);                          // tube
            translate([0,0,34]) cylinder(d=2.6, h=8);       // sleeve tip
        }
}

module oct(w, l) {   // octagon: square with 45-deg corner cuts (prop clearance)
    intersection() { square([w, l], center=true); rotate(45) square([(w+l)*0.62, (w+l)*0.62], center=true); }
}

/* ------- viewer parts: one prop + one motor bell, centred at origin ------- */
module blade2d() {   // curved scimitar plan-form (Gemfan look): lens of two
    // offset discs. The lens TIP sits at 1.172*R from the blade origin, and
    // prop() roots the blade 2.2 mm out -> swept radius = 2.2 + 1.172*R.
    // R is sized so that equals prop_d/2 - 0.4: the disc never exceeds the
    // rated Ø (v3.1 used R = prop_d/2-2.2 and overshot by ~3 mm -> the
    // spinning blades clipped the rails and the neighbouring discs).
    R = (prop_d/2 - 2.6) / 1.172;
    difference() {
        intersection() {
            translate([R*0.52, -R*0.34]) circle(r=R*0.78, $fn=48);
            translate([R*0.46,  R*0.42]) circle(r=R*0.78, $fn=48);
        }
        // concave trailing-edge scallop (Gemfan crescent): bites ~0.17R at
        // mid-root, fades before the tip — subtraction only, so the v3.2
        // swept-radius bound still holds
        translate([R*0.34, -R*0.72]) circle(r=R*0.55, $fn=48);
    }
}
module prop() {   // 40 mm CURVED tri-blade (viewer/playground mesh)
    cylinder(d=7.5, h=3.2);                       // hub
    translate([0,0,3.2]) cylinder(d=3.6, h=1.4);  // shaft cap
    for (a=[0:120:240]) rotate([0,0,a]) translate([2.2,0,2.4])
        rotate([16,0,0]) linear_extrude(1.25) blade2d();
}
module motor() {  // 0802-class bell
    cylinder(d=9.4, h=2.2);                        // base
    translate([0,0,2.2]) difference() {
        cylinder(d=11.2, h=5.6);
        translate([0,0,-eps]) cylinder(d=9.6, h=5.2);
    }
    translate([0,0,2.2]) cylinder(d=9.8, h=5.0);   // stator mass
    translate([0,0,7.8]) cylinder(d=11.2, h=1.2);  // top plate
    translate([0,0,9.0]) cylinder(d=1.5, h=3.4);   // shaft
}

/* ---------------- ghosts (previews only, never exported as parts) -------- */
module ghost_props() {
    for (sx=[-1,1], sy=[-1,1]) translate([sx*posXY, sy*posXY, 13])
        %cylinder(d=prop_d, h=0.8, center=true);
}
module ghost_motors() {
    for (sx=[-1,1], sy=[-1,1]) translate([sx*posXY, sy*posXY, plate_t])
        %cylinder(d=9.4, h=8);
}
module ghost_board() { translate([0,0,plate_t+aio_post_h]) %rrect(32, 32, 2.5, 1.6); }
module ghost_batt()  { translate([0, 4, -0.1-9.5+0]) ; translate([0,4,plate_t+aio_post_h+3.5]) %rrect(batt_w, 34, 3, 9); }

module assembly() {
    color("#23272e") frame();
    color("#e8e8ea") translate([0, 0, plate_t+aio_post_h+1.6]) canopy();  // on the board top
    translate([0, 0, plate_t+aio_post_h]) rotate([0,0,45]) board();
    color("#1a1c20") translate([0, 3, plate_t+aio_post_h+1.6+3.4]) airunit();
    color("#141416") translate([0, -canopy_l/2+8, plate_t+aio_post_h-1.4]) fpvcam();
    color("#1c2430") translate([0, 5, plate_t+aio_post_h+1.6+8.8]) rxmod();
    color("#101012") translate([0, 0, plate_t+aio_post_h+1.6+2.6]) antennas();
    color("#2b2f36") translate([0, 2, -batt_t/2]) battery_pack();
    color("#3f8f7a") for (sx=[-1,1], sy=[-1,1])
        translate([sx*posXY, sy*posXY, plate_t]) motor();
    ghost_props();
}

/* ---------------- dispatch ---------------- */
if      (PART == "frame")  frame();
else if (PART == "canopy") canopy();
else if (PART == "prop")   prop();
else if (PART == "motor")  motor();
else if (PART == "board")    board();
else if (PART == "airunit")  airunit();
else if (PART == "fpvcam")   fpvcam();
else if (PART == "rxmod")    rxmod();
else if (PART == "battery")  battery_pack();
else if (PART == "antennas") antennas();
else                       assembly();
