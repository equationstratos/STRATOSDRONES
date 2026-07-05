// Fr4n6-001 — Avata-2-inspired cinewhoop (viewer/styling model, v4)
//
// Design language studied from two references the project owner picked:
//   * DJI Avata 2 (top view) — a molded cinewhoop UNIBODY: four prop ducts
//     cut through one sculpted, gently-waisted shell, with a NARROW raised
//     spine/channel running nose-to-tail and a distinct central electronics
//     module.
//   * BetaFPV Pavo-style analog cinewhoop — the "technical" details: a finned
//     heat-sink stack over the flight controller, tall rear antennas, a
//     tilted nose camera, motors visible inside the ducts.
//
// Our fusion: the Avata molded unibody + a BetaFPV-style finned avionics
// module (which also matches the Fr4n6's real ESP32-P4 cooling story). This
// is our OWN original OpenSCAD geometry — a stylistic homage, NOT a copy of
// any DJI/BetaFPV mesh — scaled to the Fr4n6-001's 5" / 220 mm class.
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
plate_h   = 22;                     // unibody thickness at the ducts (flat top)
edge_y    = posXY + duct_or;        // 150.78 — flank extent before waisting

/* ---------------- rounded primitives ---------------- */
module rbox(sz, r){ minkowski(){ cube([sz[0]-2*r, sz[1]-2*r, sz[2]-2*r], center=true);
                                  sphere(r=r); } }
// rounded-edge cylinder, base at z=0, total height h, fillet rr  (needs h>2rr, r>rr)
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

/* ---------------- duct bores + flush lips ---------------------- */
module bores(){ for (x=[-1,1], y=[-1,1])
  translate([x*posXY, y*posXY, -1]) cylinder(d=duct_bore, h=plate_h+40); }
module lips(){ for (x=[-1,1], y=[-1,1])
  translate([x*posXY, y*posXY, plate_h-4]) difference(){
    cylinder(r=duct_or,      h=5);
    translate([0,0,-1]) cylinder(r=duct_bore/2, h=7);
    translate([0,0,3]) cylinder(r1=duct_bore/2, r2=duct_bore/2+3, h=3); // top chamfer
  } }

/* ---------------- narrow spine (the recolourable canopy) -------- */
// low, near-parallel channel nose-to-tail — NOT a wide teardrop.
module spine(){
  hull(){
    translate([-40,0,13]) rcyl(20, 14, 6);   // rear (meets battery)
    translate([  4,0,14]) rcyl(23, 16, 7);   // middle (under avionics)
    translate([ 50,0,12]) rcyl(17, 13, 6);   // shoulder
    translate([ 86,0, 9]) rcyl(10, 11, 4);   // nose lead-in to camera
  }
}
module canopy(){
  difference(){
    spine();
    translate([74,0,15]) rotate([0,26,0]) cube([8, 20, 6], center=true); // nose intake slot
  }
}

/* ---- avionics module: BetaFPV-style finned FC stack (dark) ----- */
module avionics(){
  translate([4,0,0]){
    translate([0,0,27]) rbox([44, 30, 9], 4);                 // FC/air-unit base
    for (i=[-5:1:5]) translate([i*3.4, 0, 34]) cube([1.6, 24, 8], center=true); // heat-sink fins
    for (s=[-1,1]) translate([22, s*6, 28]) rotate([0,90,0]) cylinder(d=4, h=3); // sensor lenses
  }
}

/* ---------------- rear antennas (BetaFPV whips) ---------------- */
module antennas(){
  for (s=[-1,1]) translate([-86, s*14, plate_h-3]) rotate([0,-26,0]) rotate([s*8,0,0]){
    cylinder(d=3.4, h=30);                    // coax whip
    translate([0,0,30]) rcyl(4, 13, 3.8);     // rubber cap
  }
}

/* ---------------- shell = body + module + antennas ------------- */
module shell(){
  difference(){ union(){ plate(); lips(); } bores(); }
  avionics();
  antennas();
}

/* ---------------- battery (integrated rear backpack) ----------- */
module battery(){
  translate([-72, 0, plate_h-2]) difference(){
    rbox([58, 54, 28], 10);
    for (i=[-10:4:10]) translate([-29, i, 3]) cube([4, 2, 20], center=true); // rear vents
    translate([0,0,-28]) cube([90,80,44], center=true);                      // flat base
    translate([34,0,6]) cube([16,60,40], center=true);                       // front face to spine
  }
}

/* ---------------- camera head (nose, tilted up) ---------------- */
module camera(){
  translate([92, 0, 15]) rotate([0,-24,0]){
    rbox([24, 32, 26], 10);                                       // gimbal shroud
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
