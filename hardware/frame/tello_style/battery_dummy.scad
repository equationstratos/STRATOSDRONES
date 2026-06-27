// STRATOSDRONE — 1S LiPo DUMMY at real size, for print-fit testing only.
//
// A solid stand-in for the flight pack so you can check it drops into the
// canopy cradle and clips in without falling. Default ≈ a Tello-class
// 1S 1100 mAh LiHV pack. **Measure YOUR pack and edit batt_* to match**
// (and keep body_top.scad's batt_* in sync). Print at low infill — this is a
// size gauge, not a structural part.
//
//   openscad -o stl/battery_dummy.stl --export-format binstl battery_dummy.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
eps = 0.01;

/* ---- pack envelope (KEEP IN SYNC with body_top.scad) ---- */
batt_w   = 22;     // width  (X)
batt_l   = 53;     // length (Y)
batt_h   = 9.5;    // thickness (Z)
edge_r   = 1.6;    // rounded pack edges

/* ---- lead / connector stub at the rear (+Y, toward J1 on the board) ---- */
lead_w   = 7;      // connector width
lead_h   = 4;      // connector height
lead_l   = 6;      // how far it sticks out past the pack
wire_d   = 2.2;    // the two leads
wire_len = 10;

module rbox(x, y, z, r) {              // rounded box, centred
    hull() for (sx=[-1,1], sy=[-1,1], sz=[-1,1])
        translate([sx*(x/2-r), sy*(y/2-r), sz*(z/2-r)]) sphere(r);
}

module battery_dummy() {
    // pack body
    rbox(batt_w, batt_l, batt_h, edge_r);
    // connector block + two leads at the rear
    translate([0, batt_l/2 + lead_l/2 - 0.5, 0])
        cube([lead_w, lead_l, lead_h], center=true);
    for (s = [-1,1])
        translate([s*3, batt_l/2 + lead_l, 0])
            rotate([-90,0,0]) cylinder(d=wire_d, h=wire_len);
    // a faint "+ / -" so orientation reads on the print (shallow emboss)
    translate([0,0,batt_h/2-0.3])
        linear_extrude(0.4) {
            translate([-batt_w/4, batt_l/2-7]) square([3,0.8], center=true);   // minus
            translate([ batt_w/4, batt_l/2-7]) square([3,0.8], center=true);   // plus -
            translate([ batt_w/4, batt_l/2-7]) square([0.8,3], center=true);   // plus |
        }
}

battery_dummy();
echo(str("BATTERY DUMMY ", batt_w, " x ", batt_l, " x ", batt_h, " mm"));
