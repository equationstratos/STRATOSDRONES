# Fr4n7-F — design notes (fold kinematics, mechanism, `deploy` spec)

## 1. Fold kinematics (all derived in `cad/frame_foldable.scad`)

Frame coords: origin at pod centre, front = −Y. Motors at (±41.72, ±41.72)
(118 mm wheelbase). v2 was dimensioned **against the actual thing:1604440
STLs** (measured, clean-room): the original pivots are **M3 (Ø3.2) holes
set 6 mm INSIDE the plate corner** — so ours moved from outrigger ears to
**inset pivots at (±24.5, ±36)**, housed in compact corner plates that
blend into both pod faces. The arms are **sculpted flat PADDLES** (wide
shoulder, gentle waist, blending into the motor cup) with a slight
built-in **crank** so the folded beam still clears the wall.

Front-right canonical numbers (the other corners are mirrors):

| Quantity | Value |
|---|---|
| pivot → motor distance `L` | 18.15 mm |
| crank offset | 3.3 mm (folded beam axis at x = 27.8) |
| deployed direction `th_dep` | −18.38° |
| folded direction `th_fold` | +79.5° |
| **fold sweep `FOLD_A`** | **97.89°** |
| folded motor position | (27.8, ∓18.16) |
| folded width (over nacelles) | 68.3 mm (vs 96.1 deployed, **−35 %**) |
| pivot hardware | **M3 × 14 + nyloc** (as the original) |

Rotation signs: FR +, FL −, RR −, RL + (front folds rearward, rear folds
forward along the same flank). The paddle is born at the claw Ø8, swells
to an 11 mm shoulder, waists, then blends into the Ø12.4 cup — the root
rotates inside the corner-plate sandwich (mouth −110°/+88°; the plates
plus a ~64° C-pillar keep the hinge tied).

**Why the arms can never cross (the owner's inverted-front-arm trick):**
folded, the front beam occupies y ∈ [−37, −22.3] and the rear beam
y ∈ [+22.3, +37] — disjoint bands, 31.9 mm between nacelle rims. Only the
**props** overlap in plan; because the front pods are inverted, the front
prop plane (−3.5) and rear plane (+19.7) are 23 mm apart. Machine-checked:
`PART=collision_folded|collision_arms|collision_deployed` each export
**exactly 684 bytes** (an empty intersection + 1 mm marker cube; the
folded gate excludes only the cradle grip bumps, which seat 0.55 into the
nacelle groove by design) — re-run after any TUNE change.

**Transport rule:** with props mounted, align the blades along the arms
before folding (the viewer's animation does this automatically). Aligned,
the folded package is ≈ 68 × 83 mm plus ~13 mm of blade overhang nose/tail.

**Landing feet:** front props hang under the belly, so ground clearance
comes from four feet at (±16, 0) and (0, ±17) — inside the "dead diamond"
that no blade sweeps at the low prop plane, neither folded, nor aligned,
nor anywhere in the deploy swing fan (checked against all four pivots).

## 2. Pivots — springs, stops, detents

Each corner is a printed **clevis (C-clamp)**: bottom jaw 2.4 (nyloc pocket
underneath), 6.0 slot, top jaw 2.6 with a **torsion-spring pocket**
(Ø7.4 × 2.2, 0.5 mm wire, ~4 turns — 2 left-hand + 2 right-hand, mirrored
corners). The arm's Ø8 claw rides an **M3 × 14** screw. Springs preload
toward DEPLOYED.

- **Deployed stop + detent**: the claw carries a small dome that rides a
  shallow groove in the slot ceiling and clicks into a deeper recess at the
  deployed angle. Forward-flight drag tends to fold the FRONT arms, so
  their detent is load-bearing — first-print item to verify (`TUNE`).
- The clevis mouth opens ±76° around the sweep (the tapered bar root hugs
  the barrel), leaving a ~90° C-sector that ties the jaws — plus the full
  top/bottom bridge webs back to the pod corner.

## 3. « Les accroches sont sur les bras » — snap tabs + centred TOP button

Per the owner's direction, **nothing protrudes from the body**: the
retention lives ON the arms. Each nacelle carries a small **flexible tab**
(shank 1.4 thick, band z 8.6–11.3) that enters a **flush window** in the
side wall when folded; its **barb sits fully behind the wall's inner
face** and hooks it under the springs' preload. The four tabs share a
**uniform world layout** (all barbs point FORWARD), so one slider motion
releases everything:

- **Release**: the slider's four straight **fingers** (riding above the
  PCB, z 8.6–11.4) push the tab shanks **rearward ~1.5 mm** → the barbs
  clear the window edges → the torsion springs deploy the arms
  (slider stroke 3.2 mm, return by rubber band, `TUNE`).
- **Fold-in**: hold the button while rotating the arms until the barbs
  click into their windows (a moulded fold-in ramp on the barb is the
  planned upgrade, `TUNE`).
- **V1 button — ON TOP, CENTRED**: a vertical pin **on the axis at
  (0, −19)** (clear of the battery nose at y −16 and the ToF window; the
  PCB is uncut, so the pin is guided by the bridge's printed **sleeve** +
  the capot bore). Its **cone cams the slider's centre bridge** rearward —
  press down, arms pop open.
- **V2 servo — RETAINED mechanism = worm + toothed sector**: of the seven
  candidates in [`../viz/mechanisms_viewer.html`](../viz/), the owner's own
  window-operator (crank → single-start worm → toothed sector) was chosen and
  integrated (`servo_worm` + `servo_sector` in `cad/frame_foldable.scad`). A
  3.7 g nano-servo spins the worm; the sector's pin shoves the **same ejector
  slider** the V1 button does (drive tab + X-slot on `latch_u`). Why this one:
  it is **self-locking** — the worm can't be back-driven, so the weak servo
  holds all four spring-loaded arms folded at **zero holding torque** (no
  stall, no heat, nothing pops open under vibration) — and its huge reduction
  lets that tiny servo overcome the four torsion springs. It lives entirely in
  the release z-band (8.6–11.4), where the battery (z ≥ 13) and the ToF/flow
  windows (floor level) are in other layers. Machine-checked:
  `PART=collision_drive` (worm + swept sector + servo body vs. the walls, the
  slider rails and the V1 button) exports **exactly 684 bytes**. The V1 button
  stays as a manual backup on the same corps.

## 3bis. Alternative mechanisms — printable demo kits (`cad/mechanisms.scad`)

Per the owner's window-operator reference (crank + worm + toothed sector +
scissor arms), three PRINTABLE mechanism families are provided as
self-contained demo kits (assembled preview + flat `_kit` plates):

| PART | Principle | Why it's interesting |
|---|---|---|
| `worm_crank` ★ | crank → printed single-start worm → toothed sector → pin drives the slider | **RETAINED as the V2 drive** — huge reduction, **self-locking** (the window-operator, miniaturised) |
| `scissor` | central slider → two links → twin sweeping arms | the operator's dual-arm extension, prints flat |
| `iris_cam` | rotating disc with 4 Archimedean slots → 4 radial pins | **one twist releases all four corners** (servo horn or thumb wheel) — DJI-style |
| `rack_pinion` | 8-tooth pinion walks a straight rack | the simplest rotation→translation; direct servo drive |
| `cam_lever` | quarter-turn lever swings an ECCENTRIC disc against a flat follower | 2 moving parts, force grows toward end-of-travel, self-holding |
| `toggle_clamp` | handle + link snap PAST the dead centre (genouillère) | **positive over-centre lock** with zero holding force — transport-safe |
| `wiper` | knob → gear pair (13:8) → crank pin → rod → rocking sweep arm | the windscreen-wiper four-bar (crank-rocker); continuous rotation → alternating sweep |

All coarse-pitch, printed pins, generous clearances — M0 concept demos.
**Chosen after comparing all seven: `worm_crank`** — now integrated into the
airframe as the V2 servo drive (§3 above; the linear slider is kept and driven
by the sector's pin). **Compare them animated before printing**: open
[`../viz/mechanisms_viewer.html`](../viz/) — every part is the real
exported STL, driven by its true 2-D kinematics (worm ratio, scissor
linkage solve, Archimedean slots, over-centre pass, wiper crank-rocker),
with the parts in real CONTACT (worm on the sector teeth, pinion meshed,
cam rim on its follower…). The **« Vue drone »** toggle drops the folded
Fr4n7-F beside the mechanism at true scale and syncs the stroke with the
full opening sequence (button → latch → springs → arms). The uploaded original
STLs were used as **measurement reference only** and are not committed
(Thingiverse licence).

## 4. The `deploy` SDK verb — **SPECIFIED, NOT YET IMPLEMENTED**

Wire behaviour (Tello-SDK style, additive extension):

```
deploy        →  releases the fold latch (V2 servo worm cycle ≈ 1 s), "ok"
deploy 0      →  (reserved) re-arm/fold assist if a bidirectional cam is fitted
```

- Accepted only **landed + disarmed**; anything else → `error Not foldable`
  (also the reply on non-foldable airframes). Idempotent when already
  deployed (cam cycles harmlessly, `ok`).
- Physical triggers stay independent: V1's mechanical button, and on V2 a
  **long-press of BOOT (SW2/GPIO35)** — readable as a plain input after
  boot — can invoke the same routine.

Future implementation map (verified against the current tree — one sitting):

| Layer | File | Change |
|---|---|---|
| Verb | `fc_core/src/fc_sdk.c` ~l.129 | immediate-reply branch before the `pending` guard |
| Callback | `fc_core/include/fc_core/fc_sdk.h` l.35 | optional NULL-safe `set_actuator(user, deployed)` in `fc_sdk_platform_t` (pattern: `set_led`) |
| Servo | `firmware/components/drivers/outputs.c` | `servo_init/servo_write` — LEDC TIMER_1 @ 50 Hz on `PIN_EXP_IO` |
| Wiring | header **J9**: pin 6 = EXP_IO (**GPIO22**) signal, pin 3 = VBAT power, pin 2 = GND | **no PCB change** |
| Button | SW2/BOOT (**GPIO35**), active-low after boot | long-press = deploy |
| Sims | none required | the NULL-safe callback means Gazebo + SITL ack `ok` unmodified |
| Python | none required | `drone.send_control_command("deploy")` works via djitellopy today |

## 5. Print + BOM (per drone)

| Item | Qty | Note |
|---|---|---|
| `body`, `capot`, `latch` | 1 each | PETG; capot is foldable-specific (the tello_style top's skirt would hit the knuckles) |
| `arm_front` / `arm_rear` | 2 + 2 | print one of each mirrored (left side) |
| `button` (V1) | 1 | manual TOP button (kept as backup on V2) |
| `servo_worm` + `servo_sector` (V2) | 1 each | the retained worm+sector drive; V2 adds a 3.7 g nano servo |
| M3 × 14 + nyloc | 4 | pivot axes (as the original thing:1604440) |
| torsion springs, 0.5 mm wire, Øi 4 | 2 LH + 2 RH | preload = deployed |
| small rubber band | 1 | latch return (printed-flex spring planned) |

Everything tagged `TUNE` in the SCAD (clearances, detent depth, spring
seats, latch travel) is a first-print estimate. **Not flight-validated.**
