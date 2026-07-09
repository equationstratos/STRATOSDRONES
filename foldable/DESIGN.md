# Fr4n7-F — design notes (fold kinematics, mechanism, `deploy` spec)

## 1. Fold kinematics (all derived in `cad/frame_foldable.scad`)

Frame coords: origin at pod centre, front = −Y. Motors at (±41.72, ±41.72)
(118 mm wheelbase). Pivot axes (M2 verticals) sit in the four corner "dead
zones" at **(±19, ±37)**, just outside the pod's r9 corner arc but inside
its 42 × 78 bbox.

Front-right canonical numbers (the other corners are mirrors):

| Quantity | Value |
|---|---|
| pivot → motor distance `L` | 23.21 mm |
| dogleg offset `crank_out` | 8.8 mm (folded beam centreline at x = 27.8) |
| along-beam length `a` | 21.48 mm |
| deployed direction `th_dep` | −11.74° |
| folded direction `th_fold` | 67.71° |
| **fold sweep `FOLD_A`** | **79.45°** |
| folded motor position | (27.8, ∓15.53) |
| folded width (over nacelles) | 68.3 mm (vs 96.1 deployed, **−35 %**) |

`crank_out` is sized so the folded **nacelle** (Ø12.7 on the 27.8 line)
clears the pod wall (21) by 0.45 mm — the beam alone would allow 25, the
pod is what binds. Rotation signs: FR +, FL −, RR −, RL + (front folds
rearward, rear folds forward along the same flank).

**Why the arms can never cross (the owner's inverted-front-arm trick):**
folded, the front beam occupies y ∈ [−37, −15.5] and the rear beam
y ∈ [+15.5, +37] — disjoint bands, 18.3 mm between nacelle rims. Only the
**props** overlap in plan; because the front pods are inverted, the front
prop plane (−3.5) and rear plane (+19.7) are 23 mm apart. Machine-checked:
`PART=collision_folded|collision_arms|collision_deployed` each export
**exactly 684 bytes** (an empty intersection + 1 mm marker cube) — re-run
after any TUNE change.

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
corners). The arm's Ø6.4 claw rides an **M2 × 12** screw. Springs preload
toward DEPLOYED.

- **Deployed stop + detent**: the claw carries a small dome that rides a
  shallow groove in the slot ceiling and clicks into a deeper recess at the
  deployed angle. Forward-flight drag tends to fold the FRONT arms, so
  their detent is load-bearing — first-print item to verify (`TUNE`).
- The clevis mouth opens 180° behind the deployed direction (the dogleg
  hugs the barrel), leaving a ~90° sector that ties the jaws together —
  where the corner web sits.

## 3. Latch — one slider, two release ends (V1/V2 share everything else)

Folded, each arm's **riser + overhang** enters the body through a wall
window and presents a Ø3 **pin** (top z 12.8, under the capot). A sliding
frame — two rails + keyhole **blades** — sits over the beams:

- slider **forward** → pins captured in the keyholes' round ends → arms
  locked folded (the spring torque presses the pins into the round ends,
  never out);
- slider pushed **rearward 4.5 mm** → pins land in the open rectangles →
  all four arms spring out; the deployed detents catch them.

Return: a small rubber band between the slider's rear hooks and the floor
hooks (printed-flex spring is the planned upgrade, `TUNE`). **Folding back
in is manual in both versions**: hold the release pressed while rotating
the arms until the pins drop into the keyholes.

- **V1 button**: Ø4.6 pin through the nose (Ø5 hole at (10, front face,
  z 10.6)) pressing the slider's crossbar — umbrella style.
- **V2 servo**: a 3.7 g nano-servo (20 × 8.5 × 11.5) on the PCB front-left
  drives `servo_cam` (Ø9 disc + lobe) against the same crossbar. The V1
  button stays as a manual backup.

## 4. The `deploy` SDK verb — **SPECIFIED, NOT YET IMPLEMENTED**

Wire behaviour (Tello-SDK style, additive extension):

```
deploy        →  releases the fold latch (V2 servo cam cycle ≈ 1 s), "ok"
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
| `button` (V1) *or* `servo_cam` (V2) | 1 | V2 adds a 3.7 g nano servo |
| M2 × 12 + nyloc | 4 | pivot axes |
| torsion springs, 0.5 mm wire, Øi 4 | 2 LH + 2 RH | preload = deployed |
| small rubber band | 1 | latch return (printed-flex spring planned) |

Everything tagged `TUNE` in the SCAD (clearances, detent depth, spring
seats, latch travel) is a first-print estimate. **Not flight-validated.**
