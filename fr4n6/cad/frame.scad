// Fr4n6-001 — parametric 5" printable frame (v0, M0 scaffold)
//
// One-piece bottom frame for a 220 mm-wheelbase X quad: integrated tapered
// arms, 2207 motor pods (16×16 M3), 30.5×30.5 FC stack, forward camera ears
// (20×20 bay), rear battery shelf with strap slots, downward sensor window
// (PMW3901 + VL53L1X), and optional DEXI-style printed prop ducts that bolt
// onto each pod. Print PETG/PA-CF, 40 % gyroid, 4 walls.
//
//   openscad -o stl/frame_bottom.stl -D 'PART="frame"' frame.scad
//   openscad -o stl/duct.stl         -D 'PART="duct"'  frame.scad   (print ×4)
//   openscad -o stl/top_plate.stl    -D 'PART="top"'   frame.scad
//   (PART="assembly" renders the full preview used in cad/preview/)
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;

PART = "assembly";              // frame | duct | top | assembly

/* ---------------- master parameters ---------------- */
wheelbase   = 220;              // motor-to-motor diagonal, mm (5" class)
prop_d      = 127;              // 5.0" propeller
arm_w_root  = 15;  arm_w_tip = 11;
arm_t       = 8;                // arm thickness (z)
plate_t     = 4;                // centre plate thickness
plate_w     = 92;               // centre plate square-ish envelope
stack       = 30.5;             // FC stack hole pitch (M3)
motor_pitch = 16;               // 2207 mount holes (M3, 16×16)
pod_d       = 27;               // motor pod outer Ø
batt_w      = 42; batt_l = 78;  // battery shelf footprint (4S1500…6S li-ion)
cam_gap     = 21;               // 20×20 FPV cam ear spacing
duct_h      = 22;  duct_t = 2.2;
duct_clr    = 4;                // blade tip clearance inside the duct

arm_r  = wheelbase/2;           // pod centre radius
posXY  = arm_r/sqrt(2);         // pod centre on ±45°

module m3(h=20) cylinder(d=3.2, h=h, center=true);

/* ---------------- bottom frame ---------------- */
module pod(){
  difference(){
    cylinder(d=pod_d, h=arm_t, center=true);
    cylinder(d=9, h=arm_t+2, center=true);                       // wire/cooling
    for (a=[0:90:270]) rotate([0,0,a+45])
      translate([motor_pitch/2*sqrt(2)/2*0+motor_pitch/2*cos(45)*0+0,0,0]) ;
    for (x=[-1,1], y=[-1,1])
      translate([x*motor_pitch/2, y*motor_pitch/2, 0]) m3(arm_t+2);
    for (a=[30:120:270]) rotate([0,0,a])                          // duct legs
      translate([pod_d/2-3, 0, 0]) m3(arm_t+2);
  }
}
module arm(){
  hull(){
    translate([plate_w*0.28, 0, 0]) cube([1, arm_w_root, arm_t], center=true);
    translate([arm_r-6, 0, 0])      cube([1, arm_w_tip,  arm_t], center=true);
  }
}
module centre_plate(){
  difference(){
    minkowski(){
      cube([plate_w-16, plate_w-16, plate_t], center=true);
      cylinder(r=8, h=0.01);
    }
    for (x=[-1,1], y=[-1,1])                                     // 30.5 stack
      translate([x*stack/2, y*stack/2, 0]) m3(plate_t+8);
    translate([12, 0, 0]) cube([26, 20, plate_t+2], center=true); // sensor window
    for (s=[-1,1]) translate([-plate_w/2+18, s*(batt_w/2+3), 0]) // strap slots
      cube([18, 3.2, plate_t+2], center=true);
    translate([-6,0,0]) for (y=[-9,9])                            // wire pass
      translate([0,y,0]) cylinder(d=6, h=plate_t+2, center=true);
  }
}
module battery_shelf(){
  // rear extension carrying the pack; strap slots at both ends
  difference(){
    translate([-(plate_w/2+batt_l/2-14), 0, 0])
      minkowski(){ cube([batt_l-10, batt_w-10, plate_t], center=true);
                   cylinder(r=5, h=0.01); }
    for (dx=[-batt_l+26, -14]) for (s=[-1,1])
      translate([-(plate_w/2)+dx+7, s*(batt_w/2-6), 0])
        cube([3.2, 14, plate_t+2], center=true);
  }
}
module camera_ears(){
  // two vertical ears in front, 20×20-bay spacing, M2 pivot on top
  for (s=[-1,1]) translate([plate_w/2+6, s*cam_gap/2, 11])
    difference(){
      hull(){
        cube([16, 3, 2], center=true);
        translate([0,0,10]) rotate([90,0,0]) cylinder(d=12, h=3, center=true);
      }
      translate([0,0,10]) rotate([90,0,0]) cylinder(d=2.2, h=5, center=true);
    }
}
module frame_bottom(){
  union(){
    centre_plate();
    battery_shelf();
    for (a=[45,135,225,315]) rotate([0,0,a]){ arm(); translate([arm_r,0,0]) pod(); }
    translate([0,0,plate_t/2]) camera_ears();
  }
}

/* ---------------- optional prop duct (print ×4) ---------------- */
module duct(){
  di = prop_d + 2*duct_clr;
  difference(){
    union(){
      // ring
      difference(){
        cylinder(d=di+2*duct_t, h=duct_h, center=true);
        cylinder(d=di, h=duct_h+2, center=true);
        // inlet lip round-over
        translate([0,0,duct_h/2]) rotate_extrude()
          translate([di/2+duct_t, 0]) circle(r=duct_t);
      }
      // three legs down to the pod bolt circle
      for (a=[30:120:270]) rotate([0,0,a])
        translate([ (di/2+pod_d/2-6)/2, 0, -duct_h/2+arm_t/2 ])
          cube([di/2-pod_d/2+12, 8, arm_t], center=true);
    }
    for (a=[30:120:270]) rotate([0,0,a])
      translate([pod_d/2-3, 0, -duct_h/2+arm_t/2]) m3(arm_t+2);
    cylinder(d=di, h=duct_h+2, center=true);   // re-clear bore through legs
  }
}

/* ---------------- optional top plate ---------------- */
module top_plate(){
  difference(){
    minkowski(){ cube([stack+18, stack+18, 2.5], center=true); cylinder(r=6, h=0.01); }
    for (x=[-1,1], y=[-1,1]) translate([x*stack/2, y*stack/2, 0]) m3(6);
    cube([16, 24, 4], center=true);            // strap/wires
  }
}

/* ---------------- exports / preview ---------------- */
if (PART == "frame") frame_bottom();
else if (PART == "duct") duct();
else if (PART == "top")  top_plate();
else {
  color("#2b303a") frame_bottom();
  color("#2f6fed", 0.85) for (a=[45,135,225,315]) rotate([0,0,a])
    translate([arm_r, 0, arm_t/2 + duct_h/2 - arm_t/2]) duct();
  color("#9298a3") translate([0,0,plate_t/2+31]) top_plate();
  // ghosts: motors + props for scale
  color("#474d57") for (a=[45,135,225,315]) rotate([0,0,a])
    translate([arm_r,0,arm_t/2+9]) cylinder(d=27.6, h=19.5, center=true);
  color("#20242c", 0.5) for (a=[45,135,225,315]) rotate([0,0,a])
    translate([arm_r,0,arm_t/2+21]) cylinder(d=prop_d, h=1.5, center=true);
}
