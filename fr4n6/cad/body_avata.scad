// Fr4n6-001 — Avata-2-inspired cinewhoop (viewer/styling model, v3)
//
// Design language studied from the DJI Avata 2 silhouette: a true cinewhoop
// UNIBODY — the four prop ducts are bores cut through ONE sculpted shell
// (webbed/filled between the ducts, gently waisted on the flanks), a low
// wide canopy running nose-to-tail, a rear "backpack" battery, and a tilted
// camera head on the nose. This is our OWN original OpenSCAD geometry — a
// stylistic homage, NOT a copy of any DJI mesh — scaled to the Fr4n6-001's
// 5" / 220 mm class.
//
//   for P in shell canopy battery camera motors prop; do
//     xvfb-run -a openscad -o stl/avata_$P.stl --export-format binstl \
//       -D "PART=\"$P\"" body_avata.scad; done
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 72;

PART = "assembly";     // shell|canopy|battery|camera|motors|prop|assembly

/* ------------- master geometry (matches frame.scad) ------------- */
wheelbase = 220;
prop_d    = 127;                    // 5"
posXY     = wheelbase/2/sqrt(2);    // 77.78
duct_bore = prop_d + 9;             // 136 — prop swept bore
wall      = 5;
duct_or   = duct_bore/2 + wall;     // 73 — outer radius of a duct
plate_h   = 24;                     // unibody thickness at the ducts
split     = 30;                     // canopy(top) / shell(bottom) divider
edge_y    = posXY + duct_or;        // 150.78 — flank extent before waisting

/* ---------------- rounded primitives ---------------- */
module rbox(sz, r){ minkowski(){ cube([sz[0]-2*r, sz[1]-2*r, sz[2]-2*r], center=true);
                                  sphere(r=r); } }
// rounded-edge cylinder, base at z=0, total height h, fillet rr
module rcyl(r, h, rr){ translate([0,0,rr]) minkowski(){
    cylinder(r=r-rr, h=h-2*rr); sphere(r=rr); } }

/* ---------------- unibody plate (the cinewhoop body) ------------ */
// hull of the four duct pucks → one continuous shell with filled webbing;
// flanks scooped inward for the Avata "waist".
module plate_raw(){
  hull() for (x=[-1,1], y=[-1,1])
    translate([x*posXY, y*posXY, 0]) rcyl(duct_or, plate_h, 6);
}
module plate(){
  Rs = 185; scoop = 15;
  difference(){
    plate_raw();
    for (s=[-1,1]) translate([0, s*(edge_y + Rs - scoop), plate_h/2])
      cylinder(r=Rs, h=plate_h+6, center=true);
  }
}

/* ---------------- central canopy crown (nose-to-tail hump) ------ */
// wide + low, biased to the front; the rear third is the battery.
module crown(){
  hull(){
    translate([-30,0,16]) rcyl(34, 24, 13);   // canopy rear (meets battery)
    translate([ 16,0,20]) rcyl(37, 26, 16);   // peak, widest
    translate([ 58,0,12]) rcyl(25, 18, 10);   // shoulder
    translate([ 84,0, 7]) rcyl(13, 12,  6);   // nose lead-in to camera
  }
}

/* ---------------- duct bores + raised lips ---------------------- */
module bores(){ for (x=[-1,1], y=[-1,1])
  translate([x*posXY, y*posXY, -1]) cylinder(d=duct_bore, h=plate_h+40); }
module lips(){ for (x=[-1,1], y=[-1,1])
  translate([x*posXY, y*posXY, plate_h-4]) difference(){
    cylinder(r=duct_or,      h=6);
    translate([0,0,-1]) cylinder(r=duct_bore/2, h=8);
    translate([0,0,4]) cylinder(r1=duct_bore/2, r2=duct_bore/2+3, h=3); // top chamfer
  } }

/* full outer body (plate + crown), bores punched through */
module body_full(){ difference(){ union(){ plate(); crown(); lips(); } bores(); } }

module top_of(z0){ translate([0,0, 200+z0]) cube([500,400,400], center=true); }
module bot_of(z0){ translate([0,0,-200+z0]) cube([500,400,400], center=true); }

/* ---------------- canopy (recolourable accent lid) ------------- */
module canopy(){
  difference(){
    intersection(){ crown(); top_of(split); }        // just the crown's top slice
    // front intake slot + two top vent lines for detail
    translate([70, 0, 30]) rotate([0,22,0]) cube([9, 26, 7], center=true);
    for (s=[-1,1]) translate([-4, s*11, 44]) rotate([0,3,0]) cube([54, 2.6, 7], center=true);
  }
}

/* ---------------- rear antennas -------------------------------- */
module antennas(){
  for (s=[-1,1]) translate([-92, s*15, plate_h]) rotate([0,26,0])
    { cylinder(d=3, h=24); translate([0,0,24]) sphere(d=5); }
}

/* ---------------- shell = body below split + lips + antennas ---- */
module shell(){
  intersection(){ body_full(); bot_of(split); }
  antennas();
}

/* ---------------- battery (integrated rear backpack) ----------- */
module battery(){
  translate([-72, 0, plate_h-2]) difference(){
    rbox([58, 54, 30], 10);
    for (i=[-10:4:10]) translate([-29, i, 3]) cube([4, 2, 20], center=true); // rear vents
    translate([0,0,-30]) cube([90,80,44], center=true);                      // flat base
    translate([34,0,6]) cube([16,60,40], center=true);                       // front face to canopy
  }
}

/* ---------------- camera head (nose, tilted up) ---------------- */
module camera(){
  translate([93, 0, 18]) rotate([0,-18,0]){
    rbox([24, 32, 27], 10);                                       // gimbal shroud
    translate([14,0,0]) rotate([0,90,0]) cylinder(d=20, h=12);    // lens barrel
    translate([24,0,0]) rotate([0,90,0]) cylinder(d=13, h=2.8);   // glass
  }
}

/* ---------------- motors / prop (per duct) --------------------- */
module motor_one(){
  for (a=[0:120:240]) rotate([0,0,a])
    translate([duct_bore/4, 0, plate_h/2]) cube([duct_bore/2, 9, 4], center=true); // stator arms
  translate([0,0,plate_h/2]) cylinder(d=30, h=16, center=true);   // bell
  translate([0,0,plate_h/2+9]) cylinder(d1=30, d2=24, h=5, center=true);
}
module motors(){ for (x=[-1,1], y=[-1,1])
  translate([x*posXY, y*posXY, 0]) motor_one(); }
module prop(){
  translate([0,0,plate_h/2+11]){
    cylinder(d=15, h=8, center=true);
    for (a=[0:120:240]) rotate([0,0,a]) rotate([0,0,14])
      translate([prop_d/4-4,0,0]) rotate([8,0,0])
        scale([1,0.22,0.06]) sphere(d=prop_d/2+4);
  }
}

/* ---------------- exports / preview ---------------- */
if      (PART=="shell")   shell();
else if (PART=="canopy")  canopy();
else if (PART=="battery") battery();
else if (PART=="camera")  camera();
else if (PART=="motors")  motors();
else if (PART=="prop")    prop();
else {
  color("#23272e") shell();
  color("#2f6fed") canopy();
  color("#33383f") battery();
  color("#14161b") camera();
  color("#474d57") motors();
  color("#20242c") for (x=[-1,1], y=[-1,1])
    translate([x*posXY, y*posXY, 0]) scale([1,(x*y>0)?1:-1,1]) prop();
}
