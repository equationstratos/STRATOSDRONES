// STRATOSDRONE Fr4n10-001 (TinyHoop MK1) — programmable/swarm 2.5" FPV frame.
//
// Clean-room parametric re-creation of the JeNo Pocket V2 design language
// (WE are FPV, CC-BY-4.0, printables.com/model/1704840): a wide-X 2.5"
// carbon frame — bottom 3 mm, top 2 mm, camera side plates 2 mm, whoop
// 25.5x25.5 M2 main stack + 13x13 rear RX stack, 9 mm motor mounts
// (1203-1303), O4-Lite-native camera bay, camera tilt 15-35 deg. Every line
// of geometry here is our own OpenSCAD, dimensioned from the published
// numbers (like the Eagle2 case in ../../fpv85/) — the JeNo design is KEPT
// per the owner's brief, re-branded STRATOS where possible. Thank you WE are
// FPV; go buy their carbon.
//
// Two output paths:
//   * STL — a printable PLA-CF/PETG PROTOTYPE (dry-fit before cutting carbon)
//   * DXF — the real 2-D carbon profiles (3 mm bottom, 2 mm top / cam plates)
//
//   # STL parts (printable proto + viewer meshes):
//   for P in bottom_classic bottom_xcore bottom_tank top cam_plate \
//            tpu_cam tpu_antenna tpu_guard tpu_bumper \
//            motor prop board o4lite battery; do
//     xvfb-run -a openscad -o stl/$P.stl --export-format binstl \
//       -D "PART=\"$P\"" frame.scad; done
//   # DXF carbon profiles (cut these):
//   for P in dxf_bottom_classic dxf_bottom_xcore dxf_bottom_tank \
//            dxf_top dxf_cam; do
//     xvfb-run -a openscad -o dxf/$P.dxf -D "PART=\"$P\"" frame.scad; done
//   # (PART="assembly" renders cad/preview/)
//
// SPDX-License-Identifier: CERN-OHL-P-2.0
$fn = 64;
eps = 0.01;

PART = "assembly";

/* ---------------- master parameters (TinyHoop MK1) ----------------------- */
prop_d     = 63.5;     // 2.5" (Gemfan 2520 tri-blade)                   // TUNE
motor_mx   = 42;       // motor X offset (wide-X: track wider than long) // TUNE
motor_my   = 39;       // motor Y offset                                  // TUNE
                       // wheelbase (diagonal) = 2*hypot(mx,my) ≈ 115
motor_bc   = 9.0;      // 1203-1303 mount: 3x M2 on a 9 mm circle
motor_hole = 2.3;      // M2 clearance
motor_shaft= 5.0;      // shaft / wire pass-through
arm_w      = 9.5;      // arm width at the root                           // TUNE
bottom_t   = 3.0;      // bottom plate: 3 mm CARBON (proto: print at 3-4 mm)
top_t      = 2.0;      // top plate: 2 mm carbon
cam_t      = 2.0;      // camera side plates: 2 mm carbon
stack      = 25.5;     // whoop AIO main stack, M2 (holes Ø2.3)
stack_hole = 2.3;
rx_stack   = 13.0;     // rear RX stack, M2
body_w     = 30;       // centre body width                               // TUNE
body_l     = 62;       // nose-to-tail body length                        // TUNE
batt_w     = 22;       // 2S-3S pack width (strap on top)                 // TUNE
strap_w    = 8; strap_l = 2.4;   // battery strap slots
cam_w      = 20;       // camera bay inner width (O4 Lite / 14 mm nano)   // TUNE
cam_tilt   = 25;       // uptilt (deg), JeNo range 15-35                  // TUNE
bus_h      = 16;       // standoff height (JeNo 14/16/18/20)              // TUNE
plate_style = "classic";   // classic | xcore | tank (bottom-plate centre)

// motor diagonal + prop clearance audit (fpv85 discipline)
wheelbase = 2 * sqrt(motor_mx*motor_mx + motor_my*motor_my);
prop_r = prop_d/2;
// nearest neighbour prop gap along the shorter (Y) axis:
disc_gap_y = 2*motor_my - prop_d;
echo(str("ASSERT wheelbase=", wheelbase, "  prop_d=", prop_d,
         "  disc_gap_y=", disc_gap_y, "  (want > 4 mm)"));

/* ---------------- helpers ---------------- */
module rrect(x, y, r) { offset(r) offset(-r) square([x, y], center=true); }  // 2D
module rrect3(x, y, r, h) { linear_extrude(h) rrect(x, y, r); }

/* ================= 2-D PROFILES (the carbon shapes; also DXF) ============ */

// motor-mount hole cluster at one corner
module motor_holes_2d() {
    circle(d=motor_shaft);
    for (a=[0:120:240]) rotate([0,0,a+30])
        translate([motor_bc/2, 0]) circle(d=motor_hole);
}

// one tapered arm from the body edge out to a motor pod (wide-X)
module arm_2d(mx, my) {
    hull() {
        translate([sign(mx)*body_w*0.32, sign(my)*body_l*0.20]) circle(d=arm_w+3);
        translate([mx, my]) circle(d=arm_w+7);   // motor pod
    }
}

module stack_holes_2d() {
    for (sx=[-1,1], sy=[-1,1]) translate([sx*stack/2, sy*stack/2]) circle(d=stack_hole);
    for (sx=[-1,1]) translate([sx*rx_stack/2, -body_l*0.5 + 6]) circle(d=stack_hole); // rear RX
}

// full bottom-plate outline (unibody carbon: body + 4 wide-X arms)
module bottom_outline_2d() {
    hull() rrect(body_w, body_l, 5);
    for (sx=[-1,1], sy=[-1,1]) arm_2d(sx*motor_mx, sy*motor_my);
    for (sx=[-1,1], sy=[-1,1]) translate([sx*motor_mx, sy*motor_my]) circle(d=arm_w+7);
}

// centre lightening / stiffening depends on the plate personality
module bottom_centre_cut(style) {
    if (style == "classic") {
        // "Classic": carbon CROSS in the centre — cut 4 corner windows
        for (sx=[-1,1], sy=[-1,1])
            translate([sx*9.5, sy*13]) rotate(45) rrect(9, 9, 1.6);
    } else if (style == "xcore") {
        // "X-Core": carbon X — cut the axis-aligned windows, keep diagonals
        for (a=[0,90]) rotate(a) translate([0, 13]) rrect(11, 12, 2);
        for (a=[0,90]) rotate(a) translate([0,-13]) rrect(11, 12, 2);
    } else {
        // "Tank": reinforced — minimal lightening (a few small diamonds)
        for (sx=[-1,1], sy=[-1,1]) translate([sx*8, sy*15]) rotate(45) rrect(5,5,1);
    }
}

module bottom_2d(style="classic") {
    difference() {
        bottom_outline_2d();
        for (sx=[-1,1], sy=[-1,1]) translate([sx*motor_mx, sy*motor_my]) motor_holes_2d();
        stack_holes_2d();
        bottom_centre_cut(style);
        // battery strap slots (pack lies along Y on the top plate; slots pass both)
        for (sx=[-1,1], sy=[-1,1]) translate([sx*(batt_w/2+3), sy*10]) rrect(strap_l, strap_w, 1);
        // STRATOS engraving cutout marker near the tail (through-cut dogtag hole)
        translate([0, -body_l*0.5 + 2]) rrect(10, 3, 1);
    }
}

// top plate: shorter, covers the stack + holds the camera plates
module top_2d() {
    difference() {
        hull() { rrect(body_w, body_l*0.62, 5);
                 translate([0, body_l*0.30]) rrect(cam_w+6, 8, 3); }  // nose for cam
        stack_holes_2d();
        for (sx=[-1,1], sy=[-1,1]) translate([sx*9, sy*8]) rotate(45) rrect(6,6,1.4); // lightening
        for (sx=[-1,1], sy=[-1,1]) translate([sx*(batt_w/2+3), sy*10]) rrect(strap_l, strap_w, 1);
    }
}

// camera side plate (two of these sandwich the O4 Lite / nano cam)
module cam_2d() {
    difference() {
        hull() { circle(d=14); translate([0, 15]) circle(d=10); }
        translate([0, 3]) circle(d=motor_hole);       // pivot / tilt screw
        for (t=[15:5:35]) translate([0, 3]) rotate(t) translate([0, 9]) circle(d=motor_hole); // tilt steps
    }
}

/* ================= 3-D PLATES (printable proto STL) ====================== */
module frame_bottom(style="classic") { linear_extrude(bottom_t) bottom_2d(style); }
module frame_top()  { linear_extrude(top_t) top_2d(); }
module cam_plate()  { linear_extrude(cam_t) cam_2d(); }

/* ================= TPU accessory parts (print in TPU) ==================== */
module tpu_cam() {   // O4 Lite / nano-cam mount cradle at the nose
    difference() {
        rrect3(cam_w+3, 16, 3, 15);
        translate([0, 0, 3]) rrect3(cam_w, 13, 2, 15);      // camera pocket
        translate([0, -9, 8]) rotate([90-cam_tilt,0,0]) cylinder(d=11.5, h=8); // lens exit
    }
}
module tpu_antenna() {   // rear antenna mount (two tubes, raked)
    difference() {
        rrect3(18, 8, 2, 10);
        for (sx=[-1,1]) translate([sx*5, 0, 3]) rotate([-35,0,0]) cylinder(d=3.2, h=16);
    }
}
module tpu_guard() {   // arm guard / prop bumper clip over one arm tip
    difference() {
        rrect3(arm_w+6, 14, 3, 8);
        translate([0,0,2]) rrect3(arm_w+1, 15, 1.5, 8);     // clips over the arm
    }
}
module tpu_bumper() {   // rear bumper protecting the XT30 + antennas
    difference() {
        rrect3(body_w, 8, 3, 9);
        translate([0, 2, 3]) rrect3(body_w-4, 8, 2, 9);
        translate([0, -1, 4]) rotate([90,0,0]) cylinder(d=6, h=10);  // XT30 exit
    }
}

/* ============ electronics + realistic viewer meshes (buy, don't print) ==== */
module board() {         // STRATOS TINYHOOP AIO (viewer: 27 mm, mounts 25.5 @45°)
    bw = 27;
    difference() {
        color("#0b6b39") rrect3(bw, bw, 2.5, 1.6);
        for (sx=[-1,1], sy=[-1,1]) translate([sx*stack/2, sy*stack/2, -eps])
            cylinder(d=2.3, h=3, $fn=20);          // mount holes
    }
    color("#caa14a") for (sx=[-1,1], sy=[-1,1])    // gold plated mount rings
        translate([sx*stack/2, sy*stack/2, 1.55]) cylinder(d=4, h=0.25, $fn=20);
    color("#15161a") for (sx=[-1,1], sy=[-1,1])    // the two ESP32 + ESC chips
        translate([sx*6, sy*5.5, 1.6]) rrect3(6.5, 5.5, 0.6, 1.9);
    color("#20222a") translate([0, 0, 1.6]) rrect3(8, 8, 1, 1.4);   // P4 shield
    color("#c0c0c0") translate([11, -9.5, 1.6]) cube([5, 3.5, 2], center=true); // XT30 pads
    color("#d64541") translate([-11, 10, 1.6]) cube([4, 3, 1.6], center=true); // CRSF socket
}
module standoff(h) {     // aluminium M2 hex standoff
    color("#b9bcc2") cylinder(d=4.0, h=h, $fn=6);
}
module screw() {         // M2 button-head cap screw
    color("#e4e6ea") { cylinder(d=3.6, h=1.0, $fn=20);
        translate([0,0,-1.6]) cylinder(d=2.0, h=1.6, $fn=14); }
}
module motor() {         // 1203-class brushless, bell up (props-on-top build)
    color("#2a2d33") cylinder(d=9.0, h=1.2, $fn=40);              // mount base
    color("#17181c") translate([0,0,1.1]) cylinder(d=8.0, h=1.7, $fn=36);  // stator
    color("#c8402f") translate([0,0,2.4]) difference() {          // bell (red)
        cylinder(d=15.4, h=6.4, $fn=52);
        translate([0,0,1.4]) cylinder(d=13.6, h=6+eps, $fn=52);   // hollow (open top)
        for (a=[0:30:330]) rotate([0,0,a]) translate([6.7,0,-eps])// cooling vents
            cylinder(d=2.0, h=9, $fn=14);
    }
    color("#c8402f") translate([0,0,8.4]) cylinder(d=15.4, h=1.0, $fn=52);  // bell top (overlaps)
    color("#dfe1e6") for (a=[45:90:315]) rotate([0,0,a])          // 4 bell screws
        translate([4.3,0,9.3]) cylinder(d=1.7, h=0.7, $fn=12);
    color("#9a9da3") translate([0,0,1.0]) cylinder(d=3.2, h=9.6, $fn=24);   // shaft
}
module blade2d() {       // curved "scimitar" Gemfan-2520 planform (hull of arcs)
    R = prop_d/2;
    hull() for (i=[0:10]) {
        u = i/10; r = 3.5 + u*(R-4.0);
        y = 7.2*u*(1-u)*1.7 + 2.2*u;                 // camber sweep (scimitar curve)
        ch = 1.0 + 6.6*sin(u*180)*(1 - 0.28*u);      // chord: fat mid, fine tip
        translate([r, y]) circle(d=max(0.9, ch), $fn=16);
    }
}
module prop() {          // 2.5" (63.5 mm) curved tri-blade (Gemfan look)
    color("#2a2c30") cylinder(d=7.2, h=4.6, $fn=36);             // T-mount hub
    color("#1c1e22") translate([0,0,4.6]) cylinder(d=4.6, h=1.0, $fn=24);
    for (a=[0:120:240]) rotate([0,0,a])                          // 3 curved blades
        translate([0,0,3.2]) rotate([13,0,-5])                   // pitch + up-cone
            linear_extrude(0.85, twist=-6, convexity=4) blade2d();
}
module o4lite() {        // DJI O4-Lite-class HD cam unit (JeNo-native)
    color("#17181c") rrect3(19, 11, 1.5, 11);                    // body
    color("#202227") for (i=[-3:3])                             // rear heatsink fins
        translate([i*2.3, -5.4, 3]) cube([1.2, 1.6, 7]);
    translate([0, 5.5, 5.6]) rotate([-(90-cam_tilt),0,0]) {      // lens forward + up
        color("#0c0d10") cylinder(d=10.6, h=4.4, $fn=40);
        color("#0b1e3a") translate([0,0,4.4]) cylinder(d=8.4, h=1.1, $fn=40);
        color("#14315e") translate([0,0,5.2]) sphere(d=7, $fn=28);   // glass
    }
}
module battery_pack() {  // DOGCOM 3S 560 mAh — compact pack, 60 × 18 × 18 mm
    bl = 60; bw = 18; bt = 18;   // shortened so it clears the rear TPU parts
    color("#1a1a1e") rrect3(bw, bl, 2.5, bt);                    // black shrink pack
    // white label band with the LiPo spec text engraved
    color("#e8e8ea") translate([0, 2, bt-0.4]) rrect3(bw-2, 40, 1.5, 0.5);
    color("#111") translate([0, 14, bt+0.05]) linear_extrude(0.4)
        text("DOG&COM", size=3.0, halign="center", valign="center",
             font="Liberation Sans:style=Bold");
    color("#b0111a") translate([0, 6, bt+0.05]) linear_extrude(0.4)
        text("560 MAH", size=5.0, halign="center", valign="center",
             font="Liberation Sans:style=Bold");     // the big label, like the pack
    color("#333") translate([0, -0.5, bt+0.05]) linear_extrude(0.4)
        text("11.1V 3S 80C", size=2.1, halign="center", valign="center");
    // XT30 pigtail + balance lead out the tail
    color("#f0b000") translate([0,-bl/2-4, bt*0.4]) rotate([90,0,0]) cube([9,7,7],center=true);
    for (sx=[-1,1]) color(sx>0?"#c00":"#111")
        translate([sx*2.5,-bl/2-9, bt*0.4]) rotate([90,0,0]) cylinder(d=2, h=9, $fn=10);
    color("#e0e0e0") translate([5,-bl/2-6, bt*0.7]) rotate([90,0,0]) cube([4,3,7],center=true); // balance plug
}
module batt_strap(zbase, bt) {   // narrow rubber gates band over the pack
    color("#101216") difference() {
        translate([0, -10, zbase]) rrect3(31, 7, 1.5, bt + 3);
        translate([0, -10, zbase + 1.6]) rrect3(26, 9, 1.2, bt + 2);
        translate([0, -10, zbase - 1]) rrect3(26, 9, 1.2, 1.8);
    }
}
module antenna_vtx() {   // 5.8G pigtail + foam-tube tip
    color("#141414") cylinder(d=1.7, h=9, $fn=14);
    color("#d64541") translate([0,0,9]) cylinder(d=3.2, h=16, $fn=18);
    color("#efefef") translate([0,0,25]) sphere(d=3.4, $fn=18);
}
module antenna_elrs() {  // ELRS T-antenna: coax + two dipole tips
    color("#161616") cylinder(d=1.4, h=13, $fn=12);
    color("#c8a24a") translate([0,0,13]) rotate([0,90,0])
        cylinder(d=0.9, h=25, center=true, $fn=10);
}

/* Low-ESR capacitor across the battery leads — 25 V 22 uF, Ø6 × 12 mm. */
module capacitor() {
    color("#1b1b6a") cylinder(d=6, h=12, $fn=28);              // blue can
    color("#c9c9c9") translate([0,0,12]) cylinder(d=6, h=0.4, $fn=28); // top vent
    for (sx=[-1,1]) color(sx>0?"#c00":"#111")                 // radial leads
        translate([sx*1.5,0,-6]) cylinder(d=0.8, h=6, $fn=8);
}

/* 5 V piezo buzzer — small black can with two leads. */
module buzzer() {
    color("#141414") cylinder(d=8, h=4.5, $fn=28);
    color("#333") translate([0,0,4.5]) cylinder(d=2, h=0.6, $fn=16);  // sound port
    for (sx=[-1,1]) color("#c8a24a") translate([sx*2,0,-4]) cylinder(d=0.7,h=4,$fn=8);
}

/* Micro GPS + compass module (M10-class) — small PCB with a ceramic patch. */
module gps_module() {
    color("#1c3a1c") rrect3(14, 14, 1.2, 1.4);                 // green PCB
    color("#d8d8d8") translate([0,0,1.4]) rrect3(10, 10, 0.6, 3.2);  // ceramic patch antenna
    color("#111") translate([-5,-5,1.4]) cube([3,3,1.5]);     // u-blox chip
}

/* ELRS receiver whip antenna — coax + a T tip (ceramic-free micro RX). */
module rx_antenna() {
    color("#161616") cylinder(d=1.2, h=16, $fn=12);           // coax
    color("#d8b24a") translate([0,0,16]) cylinder(d=1.6, h=4, $fn=12); // active tip (sleeve)
}

/* A soft silicone motor lead bundle (3 phase wires) as a swept tube. */
module motor_cable() {
    pts = [for (i=[0:8]) [i*1.6, 2.4*sin(i*22), 0.3*i]];
    color("#20222a") for (i=[0:len(pts)-2])
        hull() { translate(pts[i]) sphere(d=1.6,$fn=8);
                 translate(pts[i+1]) sphere(d=1.6,$fn=8); }
}

/* STRATOS emblem — a tri-blade prop ring with a raised "S" hub (the PCB
 * logo): a thin decal to drop on the top plate (replaces the JeNo silk). */
module logo() {
    linear_extrude(0.6) {                              // 3 blades + hub disc
        for (a=[0:120:240]) rotate(a)
            translate([4.6, 0]) rotate(20) scale([1,0.42]) circle(d=9.5, $fn=36);
        circle(d=6.6, $fn=44);
    }
    translate([0,0,0.55]) linear_extrude(0.7)          // raised S on the hub
        text("S", size=7.5, halign="center", valign="center",
             font="Liberation Sans:style=Bold");
}

/* STRATOS "prop-S" emblem — a 2-D mark where a bold S sits over a tri-blade
 * propeller. Used both as a raised decal and (cut through) on the top plate. */
module strat_prop_s_2d(sz=16) {
    u = sz/16;
    for (a=[0:120:240]) rotate(a+30)               // 3 swept prop blades
        translate([5.6*u, 0]) rotate(20) scale([1.15,0.42]) circle(d=11*u, $fn=36);
    circle(d=6*u, $fn=40);                          // hub
    text("S", size=15*u, halign="center", valign="center",   // the S over it
         font="Liberation Sans:style=Bold Italic");
}

/* STRATOS top plate — same envelope as the real JeNo top plate
 * (26.6 × 68.3 × 2 mm, centred at y=-0.95), mount holes on the 3 real
 * standoffs, with the STRATOS prop-S mark CUT THROUGH, centred. */
module stratos_top() {
    tw = 26.6; tl = 68.3; th = 2.0; cy = -0.95;   // real top-plate envelope
    translate([0, cy, 17.0]) linear_extrude(th) difference() {
        offset(3) offset(-3) square([tw, tl], center=true);       // rounded plate
        for (p=[[0,25.6],[8.5,-32.2],[-8.5,-32.2]])               // 3 mount holes
            translate([p[0], p[1]-cy]) circle(d=2.4, $fn=22);
        for (sy=[-1,1]) translate([0, sy*24]) rrect(4, 10, 1.6);  // lightening
        translate([0, -cy]) strat_prop_s_2d(17);                  // CENTRED mark
    }
}

/* A JeNo-style "dumbbell" lightening slot: two holes joined by a bar. */
module jeno_bone(len=7, d=3.2) {
    hull() { translate([0,-len/2]) circle(d=d, $fn=22);
             translate([0, len/2]) circle(d=d, $fn=22); }
}
/* Original JeNo top plate — same 26.6 × 68.3 × 2 envelope, the JeNo lightening
 * pattern (end dumbbell slots, a centre slot row, two triangular cut-outs, four
 * corner holes) reproduced, but WITHOUT the "JeNo" wordmark (owner's request). */
module jeno_top() {
    tw = 26.6; tl = 68.3; th = 2.0; cy = -0.95;
    translate([0, cy, 17.0]) linear_extrude(th) difference() {
        offset(3) offset(-3) square([tw, tl], center=true);        // rounded plate
        for (p=[[0,25.6],[8.5,-32.2],[-8.5,-32.2]])                // 3 real mounts
            translate([p[0], p[1]-cy]) circle(d=2.4, $fn=22);
        for (sx=[-1,1]) for (sy=[-1,1])                            // 4 corner holes
            translate([sx*10.3, sy*30 - cy]) circle(d=2.2, $fn=20);
        for (sy=[-1,1]) for (sx=[-1,1])                            // end dumbbell slots
            translate([sx*6.2, sy*26 - cy]) jeno_bone(6, 3.0);
        for (yy=[-9, 0, 9])                                        // centre slot row
            translate([0, yy - cy]) rrect(5.4, 3.0, 1.2);
        for (sx=[-1,1])                                            // 2 triangular cut-outs
            translate([sx*7.6, 15 - cy]) rotate(sx>0?15:-15)
                polygon([[0,-4.6],[4.2,4.6],[-4.2,4.6]]);
    }
}

/* Round aluminium M2 standoff (bored) — 14 mm tall; scale Z for shorter runs. */
module standoff_post() {
    color("#c2c5cb") difference() {
        cylinder(d=4.0, h=14, $fn=24);
        translate([0,0,-0.5]) cylinder(d=2.0, h=15, $fn=16);
    }
}

/* Standard analog VTX module (small PCB with an RF can + u.FL). */
module vtx_module() {
    color("#1c3a1c") rrect3(16, 16, 1.5, 1.4);                  // green PCB
    color("#3a3a3a") translate([-3,-3,1.4]) rrect3(7, 8, 0.6, 2.4);  // RF shield
    color("#c8c8c8") translate([5.5, 5.5, 1.4]) cylinder(d=2.2, h=2.4, $fn=14); // u.FL
}

/* Standard RHCP "lollipop" FPV antenna — coax mast + SMA + round dome head. */
module antenna_lollipop() {
    color("#141414") cylinder(d=2.6, h=20, $fn=18);            // coax mast
    color("#d0a828") translate([0,0,20]) cylinder(d=4.2, h=2.4, $fn=18); // SMA
    color("#c23a33") translate([0,0,22]) {
        cylinder(d=3.2, h=6, $fn=18);                          // stem
        translate([0,0,6]) sphere(d=12, $fn=28);              // the "candy" dome
    }
}

/* DJI O4-Lite-style air unit — small finned box with two coax antennas. */
module o4_airunit() {
    color("#17181c") rrect3(21, 13, 1.6, 12);                 // body
    color("#202227") for (i=[-4:4]) translate([i*2.1, -6, 3]) cube([1.1, 1.4, 8]); // fins
    for (sx=[-1,1]) color("#1a1a1a")                          // 2 antenna pigtails
        translate([sx*6, -6, 4]) rotate([60,0,0]) cylinder(d=1.6, h=20, $fn=12);
}

/* ---------------- ghosts (previews only) ---------------- */
module ghost_props() {
    for (sx=[-1,1], sy=[-1,1]) translate([sx*motor_mx, sy*motor_my, bottom_t+9.6])
        %cylinder(d=prop_d, h=0.6, center=true);
}

module assembly() {
    // bottom carbon plate
    color("#1a1c1f") frame_bottom(plate_style);
    // motors + props at the four arm tips (props-up)
    for (sx=[-1,1], sy=[-1,1]) translate([sx*motor_mx, sy*motor_my, bottom_t]) {
        motor();
        translate([0,0,9.4]) prop();
    }
    // centre stack: 4 hex standoffs carry the board + top plate
    for (sx=[-1,1], sy=[-1,1]) translate([sx*stack/2, sy*stack/2, bottom_t])
        standoff(bus_h);
    // FC board soft-mounted low on the stack
    translate([0, 0, bottom_t + 3]) board();
    // top carbon plate + its cap screws
    color("#1a1c1f") translate([0, 0, bottom_t + bus_h]) frame_top();
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*stack/2, sy*stack/2, bottom_t + bus_h + top_t]) screw();
    // camera at the nose, between two carbon side plates (lens out front + up)
    translate([0, body_l*0.40, bottom_t + bus_h + 4]) o4lite();
    color("#1a1c1f") for (sx=[-1,1])
        translate([sx*(cam_w/2 + cam_t/2), body_l*0.36, bottom_t + bus_h])
            rotate([90,0,90]) cam_plate();
    // battery strapped on the top plate, set back to clear the camera
    translate([0, -10, bottom_t + bus_h + top_t]) battery_pack();
    batt_strap(bottom_t + bus_h + top_t, 13);
    // antennas out the tail, raked back
    translate([9, -body_l*0.42, bottom_t + bus_h]) rotate([-38,0,8]) antenna_vtx();
    translate([-8, -body_l*0.40, bottom_t + bus_h]) rotate([-34,0,-10]) antenna_elrs();
    ghost_props();
}

/* ---------------- dispatch ---------------- */
// STL: printable plates + viewer meshes
if      (PART == "bottom_classic") frame_bottom("classic");
else if (PART == "bottom_xcore")   frame_bottom("xcore");
else if (PART == "bottom_tank")    frame_bottom("tank");
else if (PART == "top")            frame_top();
else if (PART == "cam_plate")      cam_plate();
else if (PART == "tpu_cam")        tpu_cam();
else if (PART == "tpu_antenna")    tpu_antenna();
else if (PART == "tpu_guard")      tpu_guard();
else if (PART == "tpu_bumper")     tpu_bumper();
else if (PART == "motor")          motor();
else if (PART == "prop")           prop();
else if (PART == "board")          board();
else if (PART == "o4lite")         o4lite();
else if (PART == "battery")        battery_pack();
else if (PART == "screw")          screw();
else if (PART == "logo")           logo();
else if (PART == "antenna_vtx")    antenna_vtx();
else if (PART == "antenna_elrs")   antenna_elrs();
else if (PART == "stratos_top")    stratos_top();
else if (PART == "jeno_top")       jeno_top();
else if (PART == "standoff_post")  standoff_post();
else if (PART == "vtx_module")     vtx_module();
else if (PART == "antenna_lollipop") antenna_lollipop();
else if (PART == "o4_airunit")     o4_airunit();
else if (PART == "capacitor")      capacitor();
else if (PART == "buzzer")         buzzer();
else if (PART == "gps_module")     gps_module();
else if (PART == "rx_antenna")     rx_antenna();
else if (PART == "motor_cable")    motor_cable();
// DXF: 2-D carbon profiles (render the flat shapes for cutting)
else if (PART == "dxf_bottom_classic") bottom_2d("classic");
else if (PART == "dxf_bottom_xcore")   bottom_2d("xcore");
else if (PART == "dxf_bottom_tank")    bottom_2d("tank");
else if (PART == "dxf_top")            top_2d();
else if (PART == "dxf_cam")            cam_2d();
else                                   assembly();
