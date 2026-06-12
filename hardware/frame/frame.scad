// STRATOSDRONE main frame — parametric X-frame for 8520 brushed motors,
// 3" props, 118 mm wheelbase (Tello-class geometry), printable flat without
// supports. PETG or tough PLA recommended, 4 perimeters, 30% gyroid.
//
// Exports (CI renders these):  openscad -o frame.stl frame.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0

/* ---------------- parameters ---------------- */
wheelbase        = 118;    // motor-to-motor diagonal, mm (Tello: 118)
motor_d          = 8.5;    // 8520 motor diameter
motor_pocket_h   = 12;     // press-fit sleeve height
motor_wall       = 1.6;    // sleeve wall thickness
motor_fit        = 0.15;   // press-fit clearance (tune for your printer)
arm_w            = 9;      // arm width
arm_h            = 3.6;    // arm thickness
hub_w            = 58;     // central hub square width
hub_h            = 3.6;    // hub plate thickness
pcb_w            = 42;     // PCB size (square)
pcb_hole_pitch   = 36;     // PCB mounting hole pitch (square pattern)
pcb_standoff_h   = 4;      // standoff height under PCB
pcb_screw_d      = 2.0;    // M2 self-tapping
flow_window      = 16;     // bottom aperture for PMW3901 + VL53L1X, square
batt_w           = 27;     // 1S 1100 mAh pack width
batt_l           = 52;     // pack length (fits below hub between rails)
batt_h           = 12;     // pack thickness
wire_slot_w      = 3.5;    // motor wire channels along arms

eps = 0.01;
off = wheelbase / 2 / sqrt(2);   // motor x/y offset (41.7 mm at 118 wb)

/* ---------------- modules ---------------- */
module motor_pocket() {
    difference() {
        cylinder(d = motor_d + motor_fit * 2 + motor_wall * 2, h = motor_pocket_h, $fn = 48);
        translate([0, 0, 1.2])
            cylinder(d = motor_d + motor_fit * 2, h = motor_pocket_h, $fn = 48);
        // wire exit
        translate([-wire_slot_w / 2, 0, 1.2])
            cube([wire_slot_w, motor_d, motor_pocket_h]);
        // bottom vent / prop-wash relief
        cylinder(d = motor_d - 2.5, h = 3, center = true, $fn = 32);
    }
}

module arm(angle) {
    rotate([0, 0, angle]) {
        hull() {
            translate([hub_w / 2 - 8, -arm_w / 2, 0]) cube([eps, arm_w, arm_h]);
            translate([off / cos(45) - motor_d / 2 - motor_wall, -arm_w / 2 * 0.8, 0])
                cube([eps, arm_w * 0.8, arm_h]);
        }
        // wire channel groove on top of the arm
        translate([hub_w / 2 - 6, -wire_slot_w / 2, arm_h - 1.0])
            cube([off / cos(45) - hub_w / 2, wire_slot_w, 1.0 + eps]);
    }
}

module hub() {
    difference() {
        // rounded square hub plate
        linear_extrude(hub_h)
            offset(r = 4) square(hub_w - 8, center = true);
        // flow/ToF window, centered, chamfered
        translate([0, 0, -eps]) {
            linear_extrude(hub_h + 2 * eps)
                square(flow_window, center = true);
        }
        translate([0, 0, hub_h - 1])
            linear_extrude(1 + eps)
                square(flow_window + 3, center = true);
        // weight relief pattern
        for (a = [0:90:270]) rotate([0, 0, a + 45])
            translate([hub_w / 2 - 12, 0, -eps])
                linear_extrude(hub_h + 2 * eps)
                    circle(d = 7, $fn = 24);
        // battery strap slots
        for (s = [-1, 1])
            translate([s * (batt_w / 2 + 3) - 1.5, -9, -eps])
                cube([3, 18, hub_h + 2 * eps]);
    }
    // PCB standoffs with screw pilot holes
    for (x = [-1, 1], y = [-1, 1])
        translate([x * pcb_hole_pitch / 2, y * pcb_hole_pitch / 2, hub_h - eps])
            difference() {
                cylinder(d = 6, h = pcb_standoff_h, $fn = 24);
                translate([0, 0, 0.6]) cylinder(d = pcb_screw_d * 0.85, h = pcb_standoff_h, $fn = 16);
            }
    // battery side rails under the hub
    for (s = [-1, 1])
        translate([s * (batt_w / 2 + 1.5) - 1.5, -batt_l / 2 + 6, -batt_h])
            cube([3, batt_l - 12, batt_h + eps]);
    // battery floor lip (front/back stops)
    for (s = [-1, 1])
        translate([-batt_w / 2, s * (batt_l / 2 - 7.5) - 1.5, -batt_h])
            cube([batt_w, 3, 2.5]);
}

module frame() {
    hub();
    for (a = [45, 135, 225, 315]) arm(a);
    for (x = [-1, 1], y = [-1, 1])
        translate([x * off, y * off, 0]) motor_pocket();
}

frame();

// dimension assertions echoed for CI
echo(str("ASSERT wheelbase=", wheelbase));
echo(str("ASSERT motor_offset=", off));
echo(str("ASSERT prop_clearance=", wheelbase / sqrt(2) - 76.2, " mm between adjacent 3in props"));
