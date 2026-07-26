// ===========================================================================
//  STRATOS 3 (Fr4n30-001) — 3" FPV freestyle, printable frame kit
//  All dimensions in mm. Everything here is parametric: change TUNE, re-export.
//
//    openscad -o stl/PART.stl -D 'PART="canopy_a"' frame3.scad
//    ./export.sh          # exports every part
//
//  Print notes live in ../README.md. Carbon plates are DXF-cut (2 mm / 3 mm),
//  every "tpu_*" and "canopy_*" part is printed in TPU 95A.
// ===========================================================================

PART = "all";          // which part to render/export
$fn  = 64;

// ---- TUNE -----------------------------------------------------------------
WB          = 142;     // wheelbase, motor centre to motor centre (diagonal)
ARM_W       = 11;      // arm width at the motor
ARM_ROOT_W  = 15;      // arm width at the body
PLATE_B     = 3.0;     // bottom plate thickness (carbon)
PLATE_T     = 2.0;     // top plate thickness (carbon)
BODY_W      = 30;      // body width between the arms
BODY_L      = 96;      // body length
STACK       = 30.5;    // FC/ESC mounting pattern (M3), 30.5 for a 3"
MOTOR_PCD   = 12;      // motor mount hole circle (1404/1804 = 12 mm, M2)
MOTOR_D     = 22;      // motor bell diameter, for clearance checks
PROP_D      = 76;      // 3" = 76.2 mm
STANDOFF_H  = 22;      // body height between plates
CAM_W       = 19;      // nano/micro cam width (19 mm class)
CAM_TILT    = 30;      // camera tilt, degrees
XT30_W      = 8;       // XT30 body width  (slot in the top plate)
XT30_H      = 8;       // XT30 body height
WALL        = 1.6;     // TPU wall
CLR         = 0.25;    // print clearance on mating features

MOT_R = WB/2;                                  // motor centre radius
mot   = [for (a=[45,135,225,315]) [MOT_R*cos(a), MOT_R*sin(a)]];

// ---- helpers ---------------------------------------------------------------
module m3(h=20) { cylinder(d=3.2, h=h, center=true); }
module m2(h=20) { cylinder(d=2.2, h=h, center=true); }
module stack_holes(h=20) {                     // 30.5 x 30.5, M3
  for (x=[-1,1], y=[-1,1]) translate([x*STACK/2, y*STACK/2, 0]) m3(h);
}
module motor_holes(h=20) {                     // 4 x M2 on a 12 mm PCD
  for (a=[0,90,180,270]) rotate([0,0,a]) translate([MOTOR_PCD/2,0,0]) m2(h);
}
module rounded(w, l, r, h) {                   // rounded rectangle prism
  linear_extrude(h) offset(r=r) offset(r=-r) square([w,l], center=true);
}

// ===========================================================================
//  CARBON PLATES  (cut, not printed — export to DXF too)
// ===========================================================================
module arm2d(len, wr, wt) {                    // one arm, root -> tip
  hull() {
    translate([0,0]) circle(d=wr);
    translate([len,0]) circle(d=wt);
  }
}
module bottom_plate() {
  linear_extrude(PLATE_B) difference() {
    union() {
      offset(r=3) offset(r=-3) square([BODY_W, BODY_L], center=true);
      for (i=[0:3]) {                          // 4 arms, true X
        a = [45,135,225,315][i];
        rotate([0,0,a]) translate([BODY_W/2-2,0]) arm2d(MOT_R-BODY_W/2+6, ARM_ROOT_W, ARM_W);
      }
    }
    // motor mounts
    for (p=mot) translate(p) {
      circle(d=8);                             // bell clearance / wire pass
      for (a=[0,90,180,270]) rotate([0,0,a]) translate([MOTOR_PCD/2,0]) circle(d=2.2);
    }
    // stack + standoffs
    for (x=[-1,1], y=[-1,1]) translate([x*STACK/2, y*STACK/2]) circle(d=3.2);
    // lightening + zip-tie slots
    for (y=[-30,-18,18,30]) translate([0,y]) square([BODY_W-12, 3], center=true);
    translate([0, BODY_L/2-9]) circle(d=9);    // camera cable pass
  }
}
module top_plate() {
  linear_extrude(PLATE_T) difference() {
    offset(r=3) offset(r=-3) square([BODY_W, BODY_L-14], center=true);
    for (x=[-1,1], y=[-1,1]) translate([x*STACK/2, y*STACK/2]) circle(d=3.2);
    // ---- XT30 pass-through, the detail that matters: the battery lead drops
    // straight down to the ESC pads instead of chafing on a carbon edge.
    translate([0, -(BODY_L-14)/2 + 13])
      offset(r=1.5) offset(r=-1.5) square([XT30_W+2*CLR+2, XT30_H+2*CLR+2], center=true);
    // battery strap slots
    for (y=[-16, 16]) translate([0,y]) square([BODY_W-10, 4], center=true);
    translate([0, (BODY_L-14)/2-10]) circle(d=8);   // canopy screw / antenna pass
  }
}

// ===========================================================================
//  TPU PARTS
// ===========================================================================

// --- camera cage: two clamshell halves holding a 19 mm cam at CAM_TILT ------
module tpu_cam_mount_bottom() {
  difference() {
    union() {
      translate([0,3,3]) rounded(CAM_W+2*WALL+2*CLR, 20, 3, 6);         // cradle floor
      translate([0,-6,0]) rounded(CAM_W+2*WALL+2*CLR, 10, 2, 10);       // rear foot
    }
    rotate([CAM_TILT,0,0]) translate([0,6,7])                            // the camera itself
      cube([CAM_W+2*CLR, 26, 16], center=true);
    for (x=[-1,1]) translate([x*(CAM_W/2+WALL+CLR+1), -6, 5])            // side screws
      rotate([0,90,0]) cylinder(d=2.2, h=8, center=true);
  }
}
module tpu_cam_mount_top() {
  difference() {
    translate([0,2,9]) rounded(CAM_W+2*WALL+2*CLR, 22, 3, 7);
    rotate([CAM_TILT,0,0]) translate([0,6,7])
      cube([CAM_W+2*CLR, 26, 16], center=true);
    translate([0,2,9]) rounded(CAM_W-6, 30, 2, 12);                      // lens window
  }
}

// --- rear bay: VTX antenna post (up/back) + RX antenna sleeve --------------
BAY_ANG = 22;                                   // antenna rake, matches the canopy
module tpu_rear_bay() {
  difference() {
    union() {
      rounded(24, 14, 3, 6);                                            // base pad
      translate([0,-2,5]) rotate([-BAY_ANG,0,0]) cylinder(d=10, h=17);  // VTX post
      translate([0,4,3]) rotate([90,0,0]) cylinder(d=7, h=10);          // RX sleeve
    }
    translate([0,-2,4]) rotate([-BAY_ANG,0,0]) cylinder(d=6.6, h=22);   // Ø6.6 antenna bore
    translate([0,6,3]) rotate([90,0,0]) cylinder(d=3.2, h=14);          // RX coax bore
    translate([0,0,-1]) cube([9, 6, 4], center=true);                   // cable channel
    for (x=[-1,1]) translate([x*9,0,0]) m3(20);                         // screws
  }
}

// --- capacitor holder: the cap LIES DOWN so it never stands proud --------
module tpu_cap_holder() {
  difference() {
    union() {
      rounded(10, 22, 2, 5);
      translate([0,0,5]) rotate([90,0,0]) cylinder(d=10.5, h=20, center=true);
    }
    translate([0,0,5]) rotate([90,0,0]) cylinder(d=6.6, h=24, center=true); // Ø6.5 can
    translate([0,0,9]) cube([4, 24, 8], center=true);                       // snap opening
    translate([0,8,2]) m3(14);
  }
}

// --- ELRS receiver tray ----------------------------------------------------
module tpu_rx_holder() {
  difference() {
    rounded(18, 22, 2, 7);
    translate([0,0,3]) rounded(14+2*CLR, 18+2*CLR, 1, 8);   // RX pocket
    translate([0,-8,4]) cube([5, 8, 6], center=true);       // wire exit
    translate([0,9,3]) rotate([90,0,0]) cylinder(d=3.2, h=8, center=true); // antenna out
  }
}

// --- GPS pad (front, on the top plate) ------------------------------------
module tpu_gps_mount() {
  difference() {
    rounded(20, 20, 3, 4);
    translate([0,0,2]) rounded(16+2*CLR, 16+2*CLR, 2, 4);
    for (x=[-1,1]) translate([x*7.5, -7.5, 0]) m3(10);
  }
}

// --- arm bumper + motor cable guard (one part per arm) --------------------
module tpu_arm_guard() {
  difference() {
    union() {
      rounded(ARM_W+2*WALL+2*CLR, 34, 3, 7);                 // clamp over the arm
      translate([0,-14,3]) rounded(ARM_W+6, 8, 3, 5);        // bumper lip
    }
    translate([0,0,4]) cube([ARM_W+2*CLR, 40, PLATE_B+2*CLR], center=true);  // arm slot
    translate([(ARM_W)/2+1, 6, 4]) rotate([90,0,0])          // 3-phase wire channel
      cylinder(d=4.2, h=26, center=true);
  }
}

// --- battery pads (grip, under the strap) ---------------------------------
module tpu_batt_pad() {
  difference() {
    rounded(26, 18, 3, 3);
    for (y=[-1,1]) translate([0, y*6, 1.5]) cube([20, 3, 3], center=true);   // grip ribs
  }
}

// ===========================================================================
//  CANOPIES — 5 styles, same footprint & fixings, pick your favourite.
//  All screw to the top plate on the STACK pattern + the front post.
//  Shared: camera window at the front, antenna exits at the back.
// ===========================================================================
CAN_L = BODY_L - 16;
CAN_W = BODY_W + 4;
module canopy_shell(h, taper=0.72, r=6) {       // common lofted body
  hull() {
    translate([0,0,0.01])   rounded(CAN_W, CAN_L, r, 0.02);
    translate([0,2,h])      rounded(CAN_W*taper, CAN_L*0.86, r, 0.02);
  }
}
module canopy_cuts() {                          // openings shared by all variants
  // camera window (front, raked)
  translate([0, CAN_L/2-6, 12]) rotate([CAM_TILT,0,0])
    cube([CAM_W+3, 20, 20], center=true);
  // antenna exits (rear)
  for (x=[-8,8]) translate([x, -CAN_L/2+6, 14]) rotate([-BAY_ANG,0,0])
    cylinder(d=7.5, h=30, center=true);
  // USB / bind access, right side
  translate([CAN_W/2, 4, 10]) rotate([0,90,0]) cylinder(d=11, h=8, center=true);
  // airflow in (front) and out (rear top)
  for (y=[10, 2, -6]) translate([0, y, 0]) rotate([0,0,0])
    for (x=[-1,1]) translate([x*(CAN_W/2-2), 0, 12]) rotate([0,90,0])
      cylinder(d=6, h=6, center=true);
  // fixings: stack pattern + front post
  for (x=[-1,1], y=[-1,1]) translate([x*STACK/2, y*STACK/2, 0]) m3(20);
  translate([0, CAN_L/2-4, 0]) m3(20);
}
// inner void: the same loft inset by WALL on every side, open at the bottom so
// the canopy drops over the stack. Height is h-WALL so the roof keeps its skin.
module canopy_void(h, taper, r) {
  translate([0,0,-1]) hull() {
    translate([0,0,0.01])
      rounded(CAN_W-2*WALL, CAN_L-2*WALL, max(r-WALL,1), 0.02);
    translate([0,2,h-WALL])
      rounded(CAN_W*taper-2*WALL, CAN_L*0.86-2*WALL, max(r-WALL,1), 0.02);
  }
}
module canopy_body(h, taper, r) {
  difference() {
    canopy_shell(h, taper, r);
    canopy_void(h, taper, r);
    canopy_cuts();
  }
}

// A — CINEWHOOP WRAP : haute, enveloppante, façon coque blanche (photo 3)
module canopy_a() { canopy_body(26, 0.70, 7); }
// B — RACER LOW : basse et effilée, style racer orange (photo 2)
module canopy_b() { canopy_body(17, 0.62, 5); }
// C — SPLIT AERO : nervures latérales, look Split-X (photo 1)
module canopy_c() {
  union() {
    canopy_body(22, 0.66, 6);
    for (x=[-1,1]) translate([x*(CAN_W/2-1.2), 0, 11])           // side strakes
      rounded(2.4, CAN_L*0.7, 1, 8);
  }
}
// D — CAGE : ajourée, minimum de matière, refroidissement maxi
module canopy_d() {
  difference() {
    canopy_body(21, 0.68, 6);
    for (y=[-24:9:24]) translate([0, y, 13]) rotate([0,90,0])
      cylinder(d=9, h=CAN_W+10, center=true);                     // big side louvres
    for (x=[-8,0,8]) translate([x, 6, 20]) cylinder(d=7, h=20);   // top vents
  }
}
// E — DUCK BILL : bec avant plongeant, protège l'objectif en crash
module canopy_e() {
  union() {
    canopy_body(23, 0.67, 6);
    hull() {                                                       // the bill
      translate([0, CAN_L/2-6, 6])  rounded(CAN_W*0.8, 4, 3, 3);
      translate([0, CAN_L/2+7, 13]) rounded(CAN_W*0.5, 3, 2, 3);
    }
  }
}

// ===========================================================================
//  ASSEMBLY PREVIEW (PART="all")
// ===========================================================================
module assembly() {
  color("#1a1d21") bottom_plate();
  color("#1a1d21") translate([0,0,STANDOFF_H]) top_plate();
  for (p=mot) translate([p[0],p[1],PLATE_B]) color("#3a3d43") cylinder(d=MOTOR_D, h=14);
  for (p=mot) translate([p[0],p[1],PLATE_B+15]) color("#d8721e",0.45) cylinder(d=PROP_D, h=1.2);
  color("#2b2f36") translate([0,0,STANDOFF_H+PLATE_T]) canopy_a();
  color("#2b2f36") translate([0,-BODY_L/2+12, PLATE_B]) tpu_rear_bay();
  echo(str("WHEELBASE=", WB, " PROP=", PROP_D, " STACK=", STACK));
}

// ---- dispatch --------------------------------------------------------------
if      (PART=="bottom_plate")      bottom_plate();
else if (PART=="top_plate")         top_plate();
else if (PART=="tpu_cam_mount_top")    tpu_cam_mount_top();
else if (PART=="tpu_cam_mount_bottom") tpu_cam_mount_bottom();
else if (PART=="tpu_rear_bay")      tpu_rear_bay();
else if (PART=="tpu_cap_holder")    tpu_cap_holder();
else if (PART=="tpu_rx_holder")     tpu_rx_holder();
else if (PART=="tpu_gps_mount")     tpu_gps_mount();
else if (PART=="tpu_arm_guard")     tpu_arm_guard();
else if (PART=="tpu_batt_pad")      tpu_batt_pad();
else if (PART=="canopy_a")          canopy_a();
else if (PART=="canopy_b")          canopy_b();
else if (PART=="canopy_c")          canopy_c();
else if (PART=="canopy_d")          canopy_d();
else if (PART=="canopy_e")          canopy_e();
else                                assembly();
