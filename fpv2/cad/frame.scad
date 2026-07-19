// STRATOSDRONE Fr4n9-001 (fpv2) — outdoor 2" FPV frame (v0, M0).
//
// Clean-room design — the 2" big sibling of fpv85 (same design language,
// same file structure, params scaled; keep the two cad/ in sync). 98 mm
// wheelbase, 51 mm (2") tri-blades, 1102-class motors, SAME shared
// STRATOS FPV AIO board (hardware/pcb_fpv, whoop 25.5 mount).
//
// Architecture: one printed UNIBODY bottom plate (X arms to four 1102-class
// motor pods + whoop-standard 25.5x25.5 AIO mount + battery strap slots +
// landing feet) and the same octagonal stack CANOPY (tilted analog nano cam,
// VTX bay, ELRS RX shelf).
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
foot_h    = 8;         // landing feet under the pods
canopy_l  = 30;        // canopy footprint length (covers cam->RX shelf)
canopy_w  = 24;        // canopy width (inside the prop-free centre zone)
canopy_h  = 17;        // apex height (overall ≈ plate+canopy ≈ 20 -> H~32 w/ antenna)
wall      = 2.0;

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
    // legs: down to the AIO mount pattern (the same M2 screws hold
    // canopy + board + plate posts — the classic whoop stack)
    for (sx=[-1,1], sy=[-1,1]) translate([sx*aio/2, sy*aio/2, 0])
        difference() {
            hull() { cylinder(d=5.4, h=1.6);
                     translate([-sx*4.5, -sy*4.5, 3.4]) cylinder(d=4.6, h=1.2); }
            translate([0,0,-eps]) cylinder(d=2.2, h=6);
        }
    // shell: octagonal plan (45-deg corner cuts keep it inside the prop-free
    // centre zone), sides + top spine
    shell_z0 = 4.0;
    difference() {
        union() {
            hull() {
                translate([0,0,shell_z0]) linear_extrude(0.8) offset(2) oct(canopy_w-4, canopy_l-4);
                translate([0,-2,canopy_h-2]) linear_extrude(2) offset(2) oct(canopy_w-9, canopy_l-13);
            }
        }
        // hollow it
        hull() {
            translate([0,0,shell_z0-eps]) linear_extrude(0.8) offset(2-wall) oct(canopy_w-4, canopy_l-4);
            translate([0,-2,canopy_h-2-wall]) linear_extrude(2) offset(2-wall) oct(canopy_w-9, canopy_l-13);
        }
        // open the front face for the camera
        translate([0, -canopy_l/2+3, shell_z0+6]) cube([cam_w+2, 10, 12], center=true);
        // antenna exit (rear, angled up)
        translate([0, canopy_l/2-1, canopy_h-6]) rotate([65,0,0]) cylinder(d=4.6, h=16, center=true);
    }
    // camera cradle: two tilted ears inside the front opening
    for (sx=[-1,1]) difference() {
        translate([sx*(cam_w/2+1.2), -canopy_l/2+6, shell_z0+6.5])
            rotate([cam_tilt,0,0]) cube([2.4, 9, 10.5], center=true);
        translate([sx*(cam_w/2+1.2), -canopy_l/2+6, shell_z0+6.5])
            rotate([cam_tilt,0,0]) rotate([0,90,0]) cylinder(d=2.1, h=6, center=true);
    }
    // VTX shelf (mid) + RX shelf (rear)
    translate([0, 2.5, shell_z0+0.8]) rrect(canopy_w-8, 11, 2, 1.8);
    translate([0, canopy_l/2-5.5, shell_z0+0.8]) rrect(canopy_w-10, 6.5, 2, 1.8);
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
        %cylinder(d=13, h=10.4);
}
module ghost_board() { translate([0,0,plate_t+aio_post_h]) %rrect(32, 32, 2.5, 1.6); }
module ghost_batt()  { translate([0, 4, -0.1-9.5+0]) ; translate([0,4,plate_t+aio_post_h+3.5]) %rrect(batt_w, 34, 3, 9); }

module assembly() {
    color("#23272e") frame();
    color("#e8e8ea") translate([0, 0, plate_t+aio_post_h+1.6]) canopy();  // on the board top
    ghost_props(); ghost_motors(); ghost_board();
}

/* ---------------- dispatch ---------------- */
if      (PART == "frame")  frame();
else if (PART == "canopy") canopy();
else if (PART == "prop")   prop();
else if (PART == "motor")  motor();
else                       assembly();
