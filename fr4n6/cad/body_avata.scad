// Fr4n6-001 — Avata-2-inspired cinewhoop unibody (viewer/styling model, v0)
//
// Design language borrowed from the DJI Avata 2 silhouette: the four prop
// ducts are FUSED into one rounded unibody shell (squircle outline with
// pinched waists), a low flat-domed hump carries the electronics, the
// battery rides on top at the rear like a backpack, and the camera head
// sits in a protective U-frame on the nose. Scaled to the Fr4n6-001's
// 5" / 220 mm-wheelbase geometry (the Avata 2 itself is a 3" machine).
//
// This file feeds fr4n6/viz/gen_viewer.py (browser 3-D viewer): each PART
// below is exported as its own STL so the viewer can colour/toggle/spin
// groups independently.
//
//   for P in shell dome battery camera motors prop; do
//     xvfb-run -a openscad -o stl/avata_$P.stl --export-format binstl \
//       -D "PART=\"$P\"" body_avata.scad; done
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 72;

PART = "assembly";     // shell|dome|battery|camera|motors|prop|assembly

/* ------------- master geometry (matches frame.scad) ------------- */
wheelbase = 220;                 // motor diagonal
prop_d    = 127;                 // 5"
posXY     = wheelbase/2/sqrt(2); // duct centres at (±posXY, ±posXY)
duct_di   = prop_d + 8;          // bore
duct_t    = 6;                   // ring wall
duct_h    = 40;                  // deep Avata-style ducts
shell_do  = duct_di + 2*duct_t;

module ring_solid(){ cylinder(d=shell_do, h=duct_h, center=true); }
module bore(){ cylinder(d=duct_di, h=duct_h+40, center=true); }

/* ---------------- unibody shell (with ducts) ---------------- */
module shell(){
  difference(){
    union(){
      // squircle unibody: hull of the four outer rings…
      hull() for (x=[-1,1], y=[-1,1]) translate([x*posXY, y*posXY, 0]) ring_solid();
      // nose block for the camera bay
      translate([posXY+shell_do/2-24, 0, -4])
        minkowski(){ cube([34, 66, duct_h-14], center=true); sphere(r=6); }
    }
    // pinched waists on the four sides (Avata's sculpted flanks)
    for (a=[0:90:270]) rotate([0,0,a])
      translate([posXY+shell_do/2+92, 0, 0]) cylinder(r=118, h=duct_h+30, center=true);
    // the four duct bores
    for (x=[-1,1], y=[-1,1]) translate([x*posXY, y*posXY, 0]) bore();
    // duct inlet chamfers
    for (x=[-1,1], y=[-1,1]) translate([x*posXY, y*posXY, duct_h/2])
      cylinder(d1=duct_di, d2=duct_di+14, h=8, center=true);
    // belly relief under the centre (sensor window sits here)
    translate([0,0,-duct_h/2]) minkowski(){ cube([120, 90, 22], center=true); sphere(4); }
    // camera opening in the nose
    translate([posXY+shell_do/2-6, 0, 2]) rotate([0,90,0]) rotate([0,0,90])
      cube([34, 40, 40], center=true);
  }
  // landing pads under the outer corner of each duct ring
  pad_r = duct_di/2 + duct_t/2;
  for (x=[-1,1], y=[-1,1])
    translate([x*(posXY + pad_r/sqrt(2)), y*(posXY + pad_r/sqrt(2)), -duct_h/2-4])
      cylinder(d1=26, d2=20, h=8, center=true);
}

/* ---------------- electronics dome (recolourable "capot") -------- */
module dome(){
  translate([6, 0, duct_h/2])
    difference(){
      minkowski(){ cube([150, 96, 22], center=true); sphere(r=10); }
      translate([0,0,-22]) cube([220, 160, 30], center=true);   // flat underside
    }
}

/* ---------------- battery backpack ---------------- */
module battery(){
  translate([-posXY-6, 0, duct_h/2+16]){
    minkowski(){ cube([96, 46, 22], center=true); sphere(r=6); }
    // latch groove detail
    translate([50, 0, 0]) cube([4, 30, 14], center=true);
  }
}

/* ---------------- camera head ---------------- */
module camera(){
  translate([posXY+shell_do/2-8, 0, 2]) rotate([0, -25, 0]){
    sphere(d=30);                                     // gimbal-ish head
    rotate([0,90,0]) cylinder(d=17, h=17);            // lens barrel
    rotate([0,90,0]) translate([0,0,16]) cylinder(d=12, h=2.6);  // glass
  }
}

/* ---------------- motors (one per duct) ---------------- */
module motor_one(){
  // 3 flat spokes + can + bell, sitting low in the duct
  for (a=[0:120:240]) rotate([0,0,a])
    translate([duct_di/4, 0, -duct_h/2+5]) cube([duct_di/2, 9, 4], center=true);
  translate([0,0,-6]) cylinder(d=30, h=20, center=true);
  translate([0,0,6.5]) cylinder(d1=32, d2=27, h=6, center=true);
}
module motors(){
  for (x=[-1,1], y=[-1,1]) translate([x*posXY, y*posXY, 0]) motor_one();
}

/* ---------------- one 3-blade prop (viewer instances ×4) --------- */
module prop(){
  translate([0,0,12]){
    cylinder(d=16, h=9, center=true);                 // hub
    for (a=[0:120:240]) rotate([0,0,a])
      rotate([0,0,14]) translate([prop_d/4-4, 0, 0])
        rotate([8,0,0])                                // blade pitch
          scale([1, 0.22, 0.06])
            sphere(d=prop_d/2+6);                      // petal blade
  }
}

/* ---------------- exports / preview ---------------- */
if (PART=="shell") shell();
else if (PART=="dome") dome();
else if (PART=="battery") battery();
else if (PART=="camera") camera();
else if (PART=="motors") motors();
else if (PART=="prop") prop();
else {
  color("#2a2e35") shell();
  color("#2f6fed") dome();
  color("#3a4048") battery();
  color("#14161b") camera();
  color("#474d57") motors();
  color("#20242c") for (x=[-1,1], y=[-1,1])
    translate([x*posXY, y*posXY, 0]) scale([1, (x*y>0)?1:-1, 1]) prop();
}
