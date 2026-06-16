// STRATOSDRONE — whoop REMOVABLE canopy (smooth, Tello-style, clip-on).
// Snaps onto the deck sockets (no screws) so it lifts off for customising.
// Smooth swept crown, chamfered camera nose, side air intakes.
//   openscad -o stl/canopy.stl --export-format binstl canopy.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
include <params.scad>

module canopy_shell() {
    difference() {
        // smooth crown: hull of a low base ring up to a swept, nose-biased dome
        hull() {
            rrect(can_x, can_y, 8, eps);
            translate([0,-6,can_h]) rrect(can_x-16, can_y-26, 9, eps);  // crown biased forward (aggressive)
        }
        // hollow
        difference() {
            hull() {
                translate([0,0,-eps]) rrect(can_x-2*can_wall, can_y-2*can_wall, 7, eps);
                translate([0,-6,can_h-can_wall]) rrect(can_x-16-2*can_wall, can_y-26-2*can_wall, 8, eps);
            }
        }
        // camera window at the nose (-y)
        translate([0,-can_y/2-eps,can_h*0.34])
            rotate([-90,0,0]) cylinder(d=cam_w+0.6, h=can_wall+4);
        // swept side air intakes (aero) — angled slots both sides
        for (sx=[-1,1]) for (j=[0:2])
            translate([sx*(can_x/2-1.5), -8+j*9, can_h*0.5])
                rotate([0,90,18])
                    hull() { cylinder(d=2.4,h=4); translate([7,0,0]) cylinder(d=2.4,h=4); }
        // two LED light pipes (front shoulders)
        for (sx=[-1,1])
            translate([sx*(can_x/2-9), -can_y/2+10, can_h-can_wall-1])
                cylinder(d=3, h=can_wall+2);
    }
    // camera cradle inside the nose
    translate([0,-can_y/2+5,can_h*0.34])
        rotate([-90,0,0]) difference() {
            cylinder(d=cam_w+3, h=6);
            translate([0,0,-eps]) cylinder(d=cam_w+0.3, h=7);
            translate([-cam_w,-cam_w,-eps]) cube([2*cam_w,cam_w,8]);
        }
    // clip posts matching the deck sockets (snap fit)
    for (i=[0:clip_n-1]) {
        a = 360/clip_n*i + 45;
        x = (deck_x/2-3)*cos(a); y = (deck_y/2-3)*sin(a)*deck_y/deck_x;
        translate([x, y, 0]) difference() {
            cylinder(d=4.0, h=4.5);
            translate([0,0,1.5]) cylinder(d=2.6, h=4);   // hollow -> springy snap
        }
    }
}

whoop_canopy_marker = true;
canopy_shell();

echo(str("ASSERT canopy=", can_x, "x", can_y, "x", can_h));
