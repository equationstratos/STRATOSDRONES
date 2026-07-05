// Fr4n6-001 — Avata-2-inspired cinewhoop (viewer/styling model, v1)
//
// Design language studied from the DJI Avata 2 silhouette (raised central
// spine + four distinct low ducts joined by sculpted struts, a figure-8
// flank on each side, protruding tilted camera head on the nose, battery
// integrated in the rear of the spine). This is our OWN original OpenSCAD
// geometry — a stylistic homage, NOT a copy of any DJI mesh — scaled to
// the Fr4n6-001's 5" / 220 mm geometry.
//
// Each PART exports as its own STL so fr4n6/viz/gen_viewer.py can colour,
// toggle and spin the groups independently.
//   for P in shell canopy battery camera motors prop; do
//     xvfb-run -a openscad -o stl/avata_$P.stl --export-format binstl \
//       -D "PART=\"$P\"" body_avata.scad; done
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 80;

PART = "assembly";     // shell|canopy|battery|camera|motors|prop|assembly

/* ------------- master geometry (matches frame.scad) ------------- */
wheelbase = 220;                    // motor diagonal
prop_d    = 127;                    // 5"
posXY     = wheelbase/2/sqrt(2);    // 77.78 — duct centres at (±posXY,±posXY)
duct_di   = prop_d + 9;             // bore
duct_t    = 5.0;                    // thin ring wall (Avata look)
duct_h    = 38;                     // deep ducts
duct_z    = 2;                      // ducts sit LOW
Rring     = duct_di/2 + duct_t/2;   // ring centreline radius

// central spine (raised body running front(+X)→rear(−X))
sp_x0 = -96; sp_x1 = 92;            // rear … nose
sp_w  = 42;                         // spine width (Y)
sp_z0 = 12; sp_z1 = 54;            // spine sits high, above the ducts

module rbox(sz, r){ minkowski(){ cube([sz[0]-2*r, sz[1]-2*r, sz[2]-2*r], center=true);
                                  sphere(r=r); } }

/* ---------------- one duct ring ---------------- */
module duct(){
  translate([0,0,duct_z]) difference(){
    cylinder(d=duct_di+2*duct_t, h=duct_h, center=true);
    cylinder(d=duct_di, h=duct_h+4, center=true);
    translate([0,0,duct_h/2])                                   // inlet chamfer
      cylinder(d1=duct_di, d2=duct_di+12, h=7, center=true);
    translate([0,0,-duct_h/2])                                  // exit chamfer
      cylinder(d1=duct_di+9, d2=duct_di, h=6, center=true);
  }
}
module ducts(){ for (x=[-1,1], y=[-1,1]) translate([x*posXY, y*posXY, 0]) duct(); }

/* ---------------- sculpted struts spine → each duct ------------- */
module strut(dcx, dcy){
  inx = dcx - dcx/abs(dcx)*Rring*0.72;      // point on the duct inner rim
  iny = dcy - dcy/abs(dcy)*Rring*0.72;
  sx  = dcx*0.42;                            // anchor on the spine flank
  sy  = (sp_w/2-2)*(dcy>0?1:-1);
  hull(){
    translate([sx, sy, sp_z0+9])  rbox([16,10,16], 3);
    translate([inx, iny, duct_z+8]) rbox([16,14,14], 3);
  }
  // a lower tie so the strut reads as a webbed sweep, not a stick
  hull(){
    translate([sx*1.1, sy*0.8, sp_z0+2]) rbox([12,8,8], 2);
    translate([(inx+dcx)/2, (iny+dcy)/2, duct_z+2]) rbox([12,12,8], 2);
  }
}
module struts(){ for (x=[-1,1], y=[-1,1]) strut(x*posXY, y*posXY); }

/* ---------------- spine lower body (structural) ---------------- */
module spine_base(){
  intersection(){
    translate([(sp_x0+sp_x1)/2, 0, (sp_z0+sp_z1)/2])
      rbox([sp_x1-sp_x0, sp_w, sp_z1-sp_z0], 12);
    translate([0,0,-40]) cube([400, sp_w+40, 96], center=true);   // keep lower half
  }
}

/* ---------------- canopy (recolourable accent top) ------------- */
module canopy(){
  intersection(){
    translate([(sp_x0+sp_x1)/2+4, 0, (sp_z0+sp_z1)/2])
      rbox([sp_x1-sp_x0-6, sp_w-2, sp_z1-sp_z0], 12);
    translate([0,0,60]) cube([400, sp_w+40, 96], center=true);    // keep upper half
  }
}

/* ---------------- battery (integrated rear of spine) ----------- */
module battery(){
  translate([sp_x0+22, 0, (sp_z0+sp_z1)/2])
    difference(){
      rbox([46, sp_w-3, sp_z1-sp_z0-4], 9);
      translate([-24,0,0]) for (i=[-6:3:6])                      // rear vents
        translate([0,i,-6]) cube([6,1.4,16], center=true);
    }
}

/* ---------------- camera head (nose, tilted up) ---------------- */
module camera(){
  translate([sp_x1-4, 0, sp_z0+10]) rotate([0,-22,0]){
    rbox([20,30,26], 8);                                          // gimbal shroud
    translate([12,0,0]) rotate([0,90,0]) cylinder(d=18, h=10);    // lens barrel
    translate([20,0,0]) rotate([0,90,0]) cylinder(d=12, h=2.6);   // glass
  }
}

/* ---------------- motors (one per duct) ---------------- */
module motor_one(){
  for (a=[0:120:240]) rotate([0,0,a])
    translate([duct_di/4, 0, duct_z-duct_h/2+6]) cube([duct_di/2, 9, 4], center=true);
  translate([0,0,duct_z-4]) cylinder(d=30, h=20, center=true);
  translate([0,0,duct_z+7]) cylinder(d1=32, d2=27, h=6, center=true);
}
module motors(){ for (x=[-1,1], y=[-1,1]) translate([x*posXY, y*posXY, 0]) motor_one(); }

/* ---------------- one 3-blade prop (viewer instances ×4) ------- */
module prop(){
  translate([0,0,duct_z+12]){
    cylinder(d=16, h=9, center=true);
    for (a=[0:120:240]) rotate([0,0,a]) rotate([0,0,14])
      translate([prop_d/4-4,0,0]) rotate([8,0,0])
        scale([1,0.22,0.06]) sphere(d=prop_d/2+6);
  }
}

/* ---------------- exports / preview ---------------- */
if      (PART=="shell")   { ducts(); struts(); spine_base(); }
else if (PART=="canopy")  canopy();
else if (PART=="battery") battery();
else if (PART=="camera")  camera();
else if (PART=="motors")  motors();
else if (PART=="prop")    prop();
else {
  color("#23272e"){ ducts(); struts(); spine_base(); }
  color("#2f6fed") canopy();
  color("#3a4048") battery();
  color("#14161b") camera();
  color("#474d57") motors();
  color("#20242c") for (x=[-1,1], y=[-1,1])
    translate([x*posXY, y*posXY, 0]) scale([1,(x*y>0)?1:-1,1]) prop();
}
