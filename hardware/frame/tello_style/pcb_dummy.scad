// STRATOSDRONE — PCB DUMMY at real size, for print-fit testing only.
//
// A stand-in for the real mainboard so you can check, in plastic, that the
// board drops onto the four bosses, the bottom sensors line up with the floor
// window, and the edge connectors (USB, camera, battery) line up with the
// frame's openings — BEFORE committing to the actual PCB. Outline + holes come
// straight from design.py BOARD; component blocks use the design.py placements.
// Print flat at low infill; it is a size/alignment gauge, not a functional PCB.
//
//   openscad -o stl/pcb_dummy.stl --export-format binstl pcb_dummy.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 48;
eps = 0.01;

/* ---- board envelope (design.py BOARD) — origin at a corner, 0..bw / 0..bh ---- */
bw = 38; bh = 74; br = 6; bt = 1.6;            // width, length, corner_r, thickness
mh_d = 2.2;                                     // M2 clearance hole
holes = [[6,6],[32,6],[6,68],[32,68]];          // mount holes (26 x 62 pitch)

module board2d() {
    translate([bw/2, bh/2]) offset(br) square([bw-2*br, bh-2*br], center=true);
}

// a top-side component block, centred at board (px,py)
module comp(px, py, sx, sy, hz) {
    translate([px-sx/2, py-sy/2, bt]) cube([sx, sy, hz]);
}

module pcb_dummy() {
    // centre the board on the origin so it sits in the frame bay like the real one
    translate([-bw/2, -bh/2, 0]) {
        difference() {
            linear_extrude(bt) board2d();
            for (p = holes) translate([p[0], p[1], -eps]) cylinder(d=mh_d, h=bt+2*eps);
        }
        // --- key TOP components (ref : design.py PLACE) ---
        comp(19.5, 18.6, 14, 13, 3.2);   // U3  ESP32-C6 module  (tallest → canopy clearance)
        comp(18.8, 38.6,  9,  9, 1.2);   // U1  ESP32-P4
        comp(27.0, 60.9,  5,  5, 3.0);   // L1  buck inductor
        comp(35.4, 47.0,  4, 16, 3.5);   // SW1/SW2 reset+boot, right edge
        // --- edge connectors (must line up with the frame openings) ---
        comp( 4.0, 29.6,  5,  9, 3.2);   // J2  USB-C, LEFT edge
        comp(19.0,  5.2, 12,  3, 2.0);   // J4  camera FFC, NOSE
        comp(19.0, 69.5,  8,  5, 5.0);   // J1  battery JST, REAR edge
        // --- bottom-side downward sensors (should sit over the floor window) ---
        for (p = [[19,33.1],[19,45.3]])
            translate([p[0]-2.5, p[1]-2.5, -2]) cube([5, 5, 2]);   // U8 ToF / U9 flow
    }
}

pcb_dummy();
echo(str("PCB DUMMY ", bw, " x ", bh, " x ", bt, " mm, holes at 26x62"));
