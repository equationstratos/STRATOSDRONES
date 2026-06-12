// Canopy / top shell: protects the PCB, holds the front camera at 10 deg
// uptilt, snaps onto the PCB standoff screws region. Print in 2 perimeters,
// 10% infill, no supports (flat top down or 45 deg).
// SPDX-License-Identifier: CERN-OHL-P-2.0

pcb_w        = 42;
wall         = 1.2;
inner_h      = 13;    // clearance over PCB (ESP32-P4 + C6 module + connectors)
cam_w        = 8.6;   // OV5647 'spy' module barrel width (or RPi v1 25x24 board: use cam_board variant)
cam_tilt     = 10;    // deg up
vent_n       = 6;

$fn = 48;
eps = 0.01;
W = pcb_w + 2 * wall + 1.6;

module shell() {
    difference() {
        // outer rounded box
        hull() for (x = [-1, 1], y = [-1, 1])
            translate([x * (W / 2 - 3), y * (W / 2 - 3), 0])
                cylinder(r = 3, h = inner_h + wall);
        // inner cavity
        translate([0, 0, -eps])
            hull() for (x = [-1, 1], y = [-1, 1])
                translate([x * (W / 2 - 3 - wall), y * (W / 2 - 3 - wall), 0])
                    cylinder(r = 3, h = inner_h + eps);
        // vents
        for (i = [0:vent_n - 1])
            translate([-W / 2 - eps, -W / 2 + 7 + i * (W - 14) / (vent_n - 1), inner_h - 4])
                rotate([0, 90, 0]) cylinder(d = 2.6, h = W + 2 * eps);
        // USB-C window (back)
        translate([-W / 2 - eps, -5.5, 2.5]) cube([wall + 1.6 + 2 * eps, 11, 5]);
        // camera barrel hole (front, tilted)
        translate([W / 2 - wall - 1, 0, inner_h * 0.55])
            rotate([0, 90 - cam_tilt, 0])
                cylinder(d = cam_w + 0.4, h = 8);
        // LED light pipes (top rear corners)
        for (s = [-1, 1])
            translate([-W / 2 + 6, s * (W / 2 - 6), inner_h + wall - 1.5])
                cylinder(d = 3.2, h = 2);
    }
    // camera cradle inside
    translate([W / 2 - wall - 6, 0, inner_h * 0.55])
        rotate([0, 90 - cam_tilt, 0])
            difference() {
                cylinder(d = cam_w + 3.2, h = 6);
                translate([0, 0, -eps]) cylinder(d = cam_w + 0.3, h = 6 + 2 * eps);
                translate([-cam_w, -cam_w / 2 - 1.6, -eps]) cube([cam_w, cam_w + 3.2, 7]);
            }
}

shell();
echo(str("ASSERT canopy_w=", W));
