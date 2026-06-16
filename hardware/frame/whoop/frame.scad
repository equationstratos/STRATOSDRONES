// STRATOSDRONE — whoop airframe BASE (deck + arms + motor mounts + guards).
// Variant chosen with `guard` in params.scad (or -D guard="ring"/"duct"/"none").
//   openscad -D guard=\"duct\" -o stl/frame_duct.stl --export-format binstl frame.scad
// SPDX-License-Identifier: CERN-OHL-P-2.0
include <params.scad>

// PCB standoffs (4) at the 26x60 pitch
module pcb_bosses() {
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*hole_x/2, sy*hole_y/2, deck_t-eps])
            difference() {
                cylinder(d=6, h=boss_h);
                translate([0,0,0.8]) cylinder(d=1.7, h=boss_h);   // M2 self-tap
            }
}

// rear slide-in battery cradle (open at +y, Tello-style), below the deck
module battery_bay() {
    for (s=[-1,1])                                   // side rails
        translate([s*(batt_w/2+1.2)-1.2, deck_y/2-batt_l-3, -batt_h])
            cube([2.4, batt_l, batt_h]);
    translate([-batt_w/2, deck_y/2-batt_l-3, -batt_h])   // floor
        cube([batt_w, batt_l-4, 1.6]);
    // front stop + retention clip lip at the rear opening
    translate([-batt_w/2, deck_y/2-batt_l-3, -batt_h]) cube([batt_w, 2.5, 4]);
    difference() {
        translate([-batt_w/2-1, deck_y/2-3.2, -batt_h]) cube([batt_w+2, 1.6, batt_h]);
        translate([-batt_w/2+2, deck_y/2-4, -batt_h+2]) cube([batt_w-4, 3, batt_h-3]);
    }
}

// canopy clip sockets around the deck rim (mate with canopy posts)
module canopy_sockets() {
    for (i=[0:clip_n-1]) {
        a = 360/clip_n*i + 45;
        x = (deck_x/2-3)*cos(a); y = (deck_y/2-3)*sin(a)*deck_y/deck_x;
        translate([x, y, deck_t-eps]) cylinder(d=4.4, h=3.2);
    }
}

module deck() {
    difference() {
        union() {
            rrect(deck_x, deck_y, 7, deck_t);                 // deck plate
            // raised rim for stiffness + canopy seat
            difference() {
                rrect(deck_x, deck_y, 7, 3.2);
                translate([0,0,-eps]) rrect(deck_x-2*wall, deck_y-2*wall, 6, 3.2+2*eps);
            }
        }
        // under-body sensor window (flow + ToF), forward of centre
        translate([0, 6, -eps]) rrect(sensor_win, sensor_win+10, 2, deck_t+2*eps);
        // camera notch at the nose (-y)
        translate([0, -deck_y/2-eps, -eps]) rrect(cam_w+2, 6, 1, deck_t+2*eps);
        // weight-relief / airflow slots
        for (sx=[-1,1]) translate([sx*13, -14, -eps]) rrect(5, 16, 2, deck_t+2*eps);
    }
    pcb_bosses();
    battery_bay();
    canopy_sockets();
}

module arms_and_motors() {
    for (sx=[-1,1], sy=[-1,1]) {
        // swept arm from deck corner to the motor
        swept_arm(sx*(deck_x/2-5), sy*(deck_y/2-9),
                  sx*motor_off,      sy*motor_off,
                  arm_w, arm_tip_w, arm_h);
        translate([sx*motor_off, sy*motor_off, 0]) motor_pocket();
    }
}

// guards (+ struts tying each guard to its arm/motor)
module guards() {
    if (guard != "none")
        for (sx=[-1,1], sy=[-1,1]) {
            translate([sx*motor_off, sy*motor_off, (guard=="duct")?0:arm_h])
                prop_guard(guard);
            // struts: motor boss -> guard inner wall, toward the hub
             a = atan2(sy, sx);
            for (da=[-118, 0, 118]) {
                ang = a + 180 + da;
                hull() {
                    translate([sx*motor_off, sy*motor_off, arm_h/2])
                        cylinder(d=3, h=arm_h, center=true);
                    translate([sx*motor_off + guard_ir*cos(ang),
                               sy*motor_off + guard_ir*sin(ang), arm_h/2])
                        cylinder(d=3, h=arm_h, center=true);
                }
            }
        }
}

module whoop_frame() {
    deck();
    arms_and_motors();
    guards();
}

whoop_frame();

echo(str("ASSERT wheelbase=", wheelbase));
echo(str("ASSERT pcb=", pcb_x, "x", pcb_y));
echo(str("ASSERT guard=", guard));
echo(str("ASSERT span=", 2*(motor_off + ((guard=="none")?prop_r:guard_ir+ (guard=="duct"?duct_t:ring_t)))));
