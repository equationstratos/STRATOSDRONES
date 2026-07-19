// STRATOSDRONE Fr4n9-001 (fpv2) — outdoor 2" FPV frame (v1, M0).
//
// Clean-room design — the 2" twin of fpv85 v1 (same toothpick language from
// the owner's photos: SIDE PLATES + top deck, big-lens cam, finned air unit,
// two rear antennas, pack strapped UNDER). Params scaled to 2"; keep the two
// cad/ files in sync. All geometry is our own parametric OpenSCAD.
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

/* ---------------- master parameters (fpv2; keep fpv85/cad in sync) -------- */
wheelbase = 98;        // motor-to-motor diagonal — overall ≈ 0.707*wb + prop ≈ 120
prop_d    = 51;        // 2" tri-blade                                    // TUNE
motor_bc  = 9.0;       // 1102-class mount: 3x M2 on a 9 mm circle        // TUNE
motor_hole = 2.2;      // M2 clearance
pod_d     = 16.0;      // motor pod outer Ø (1102 base ~13 + wall)
shaft_d   = 4.2;       // prop-shaft / wire pass-through
arm_w     = 7.6;       // arm width                                       // TUNE
plate_t   = 3.4;       // unibody plate thickness (PLA-CF / PETG)
aio       = 25.5;      // whoop AIO mount pitch (the shared FPV AIO board)
aio_post_d = 4.8;      // M2 posts under the board (soft-mount grommets)
aio_post_h = 3.2;
centre_w  = 34;        // centre pad square (32x32 board + margin)
batt_w    = 22;        // 2S 650 mAh pack width                            // TUNE
strap_w   = 7; strap_l = 2.2;   // battery strap slots
cam_w     = 14.4;      // nano cam side-screw width (14 mm cams + clr)     // TUNE
cam_tilt  = 15;        // uptilt (deg)                                     // TUNE
foot_h    = 7;         // pod feet (the pack under the plate lands first — toothpick way)
batt_t    = 9;         // 2S 650 pack thickness (strapped UNDER)            // TUNE
canopy_l  = 34;        // side-plate length
canopy_w  = 22;        // outside width across the two side plates
canopy_h  = 16;        // side-plate height above its base
wall      = 2.0;       // side-plate / deck thickness

posXY = wheelbase/2/sqrt(2);          // 22.98 — motor centres (X layout)
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
module foot() {   // small printed foot under each pod
    cylinder(d1=6.5, d2=4.5, h=foot_h);
}
module arm(ang) {
    rotate([0,0,ang]) hull() {
        translate([10,0,0]) cube([eps, arm_w+3, plate_t]/1, center=false);
        translate([sqrt(2)*posXY - pod_d/2 + 1.5, -arm_w/2, 0]) cube([eps, arm_w, plate_t]);
    }
}
module centre_pad() {
    difference() {
        rrect(centre_w, centre_w, 5, plate_t);
        // lightening windows around the AIO mount
        for (sx=[-1,1]) translate([sx*10.6, 0, -eps]) rrect(6.5, 15, 2.4, plate_t+2*eps);
        // battery strap slots (pack lies along Y, strapped to the plate)
        for (sx=[-1,1], sy=[-1,1])
            translate([sx*(batt_w/2+2.6), sy*7.5, -eps])
                rrect(strap_l, strap_w, 1, plate_t+2*eps);
    }
    // AIO posts (board soft-mounts on top)
    for (sx=[-1,1], sy=[-1,1]) translate([sx*aio/2, sy*aio/2, plate_t-eps])
        difference() {
            cylinder(d=aio_post_d, h=aio_post_h);
            translate([0,0,0.8]) cylinder(d=1.7, h=aio_post_h);
        }
}
module frame() {
    for (sx=[-1,1], sy=[-1,1]) {
        translate([sx*posXY, sy*posXY, 0]) motor_pod();
        translate([sx*posXY, sy*posXY, -foot_h]) foot();
        arm(atan2(sy, sx));
    }
    centre_pad();
}

/* ---------------- canopy (side plates + spine, camera + VTX + RX) -------- */
module canopy() {
    // legs down to the AIO stack (same M2 screws: canopy -> board -> posts)
    for (sx=[-1,1], sy=[-1,1]) translate([sx*aio/2, sy*aio/2, 0])
        difference() {
            hull() { cylinder(d=5.4, h=1.6);
                     translate([-sx*(aio/2 - (canopy_w/2-wall/2)), -sy*3.5, 2.6]) cylinder(d=4.6, h=1.4); }
            translate([0,0,-eps]) cylinder(d=2.2, h=6);
        }
    // two SIDE PLATES (the photo's aluminium look, printed): raked front,
    // lightening holes, joined by a flat TOP DECK
    for (sx=[-1,1]) translate([sx*(canopy_w/2-wall), 0, 2.6])
        rotate([90,0,90]) linear_extrude(wall, center=true) difference() {
            polygon([[-canopy_l/2+3,0],[canopy_l/2,0],[canopy_l/2,canopy_h-4],
                     [canopy_l/2-6,canopy_h],[-canopy_l/2+9,canopy_h],[-canopy_l/2+3,6]]);
            translate([canopy_l/2-11, canopy_h-7]) circle(d=5);       // lightening
            translate([canopy_l/2-18, canopy_h-8]) circle(d=4);
            translate([-2, 5]) square([10, 4], center=true);          // strap/wire slot
        }
    translate([0, 2, 2.6+canopy_h-wall]) rrect(canopy_w, canopy_l-9, 1.6, wall);  // top deck
    // camera RING at the raked front (big-lens nano cam, 15 deg uptilt)
    translate([0, -canopy_l/2+4.5, 2.6+7.5]) rotate([90-cam_tilt,0,0]) difference() {
        cylinder(d=cam_w+3.4, h=3.4, center=true);
        cylinder(d=cam_w-1.5, h=4.0, center=true);
    }
    // rear antenna clamp bar: two angled tubes' seats
    translate([0, canopy_l/2-3.5, 2.6+canopy_h-wall-2]) difference() {
        rrect(canopy_w-4, 5, 1.6, 4);
        for (sx=[-1,1]) translate([sx*5.5, 0, -eps]) rotate([-28,0,0]) cylinder(d=2.1, h=9);
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
module fpvcam() {          // big-lens nano cam
    rrect(cam_w, 10, 1.8, cam_w);                          // body cube
    translate([0, -6.4, cam_w/2]) rotate([90,0,0]) {
        cylinder(d=11.4, h=5.2);                           // barrel
        translate([0,0,5.2]) cylinder(d=9.0, h=1.6);       // lens ring
        color("#0b1e3a") translate([0,0,6.6]) sphere(d=7.2);   // glass
    }
}
module rxmod() {           // ELRS RX + wire antenna
    rrect(11, 14, 1.2, 2.4);
    translate([2.5, 6.5, 1.2]) rotate([-60,0,0]) cylinder(d=1.1, h=26);
}
module battery_pack() {    // 2S pack strapped UNDER the plate + XT30 pigtail
    rn=2.2;
    minkowski() { cube([batt_w-2*rn, 34-2*rn, batt_t-2*rn], center=true); sphere(r=rn, $fn=24); }
    translate([batt_w/2-2, 19.5, 0]) rotate([90,0,0]) cylinder(d=3.4, h=6);      // leads
    color("#f5b301") translate([batt_w/2-2, 24.5, 0]) cube([7, 10, 6], center=true);  // XT30
}
module antennas() {        // two rear antennas, angled up-back (photo)
    for (sx=[-1,1]) translate([sx*5.5, canopy_l/2-3.5, canopy_h-2])
        rotate([-28,0,0]) {
            cylinder(d=1.7, h=34);                          // tube
            translate([0,0,34]) cylinder(d=2.6, h=8);       // sleeve tip
        }
}

module oct(w, l) {   // octagon: square with 45-deg corner cuts (prop clearance)
    intersection() { square([w, l], center=true); rotate(45) square([(w+l)*0.62, (w+l)*0.62], center=true); }
}

/* ------- viewer parts: one prop + one motor bell, centred at origin ------- */
module prop() {   // 2" (51 mm) tri-blade (viewer/playground mesh)
    cylinder(d=7.5, h=3.2);                       // hub
    translate([0,0,3.2]) cylinder(d=3.6, h=1.4);  // shaft cap
    for (a=[0:120:240]) rotate([0,0,a])
        translate([prop_d/4+1.6, 0, 1.6])
            rotate([18,0,0]) scale([1, 0.26, 0.075])
                sphere(d=prop_d/2+3, $fn=40);
}
module motor() {  // 0802-class bell
    cylinder(d=13.0, h=2.6);                       // base
    translate([0,0,2.6]) difference() {
        cylinder(d=14.6, h=7.0);
        translate([0,0,-eps]) cylinder(d=12.6, h=6.6);
    }
    translate([0,0,2.6]) cylinder(d=12.9, h=6.4);  // stator mass
    translate([0,0,9.0]) cylinder(d=14.6, h=1.4);  // top plate
    translate([0,0,10.4]) cylinder(d=2.0, h=3.8);  // shaft
}

/* ---------------- ghosts (previews only, never exported as parts) -------- */
module ghost_props() {
    for (sx=[-1,1], sy=[-1,1]) translate([sx*posXY, sy*posXY, 16])
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
    translate([0, 0, plate_t+aio_post_h]) board();
    color("#1a1c20") translate([0, 3, plate_t+aio_post_h+1.6+3.4]) airunit();
    color("#141416") translate([0, -canopy_l/2+7.5, plate_t+aio_post_h+1.6+2.6]) fpvcam();
    color("#1c2430") translate([0, 10, plate_t+aio_post_h+1.6+canopy_h-4]) rxmod();
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
