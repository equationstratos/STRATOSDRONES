// STRATOSDRONE whoop — full assembly preview (visual only, not for print).
// frame(guard) + removable canopy + motors + 3" prop disks. For the website.
//   openscad -D guard=\"duct\" -o preview/assembly_duct.png assembly.scad
//   openscad -D show=\"canopy\" -o preview/canopy.png assembly.scad
//   openscad -D show=\"frame\"  -o preview/frame.png  assembly.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
include <params.scad>
use <frame.scad>
use <canopy.scad>

show = "all";   // "all" | "frame" (airframe + motors, no canopy) | "canopy"

if (show == "canopy") {
    color("#0e0e10") canopy_shell();
} else {
    color("#1a1a1d") whoop_frame();

    // motors + props
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*motor_off, sy*motor_off, 1.2]) {
            color("Silver") cylinder(d=motor_d, h=16);
            cw = (sx*sy > 0);
            color(cw ? "#e87722" : "#3a3a3a", 0.5)
                translate([0,0,16.5]) cylinder(d=prop_d, h=1.0);
        }

    // removable canopy floating just above the deck (omitted for "frame")
    if (show == "all")
        color("#0e0e10") translate([0,0,3.4]) canopy_shell();
}
