# Fr4n7-F — design notes (fold kinematics, mechanism, `deploy` spec)

## 1. Fold kinematics (all derived in `cad/frame_foldable.scad`)

Frame coords: origin at pod centre, front = −Y. Motors at (±41.72, ±41.72)
(118 mm wheelbase). v1 follows thing:1604440's design language: the arms
are **sculpted flat PADDLES** (wide shoulder at the pivot, gentle waist,
blending into the motor cup) and each M2 pivot lives inside a rounded
**corner LOBE** at **(±27.8, ±37)** — two stacked plates flowing out of
the pod corner, the paddle rotating in the sandwich gap — so the folded
arm lies flat along the flank with the nacelle just clear of the wall,
and the whole thing reads as one silhouette.

Front-right canonical numbers (the other corners are mirrors):

| Quantity | Value |
|---|---|
| pivot → motor distance `L` | 14.70 mm |
| deployed direction `th_dep` | −18.73° |
| folded direction `th_fold` | +90° (along the flank) |
| **fold sweep `FOLD_A`** | **108.73°** |
| folded motor position | (27.8, ∓22.30) |
| folded width (over nacelles) | 68.3 mm (vs 96.1 deployed, **−35 %**) |

`pivot_x = 27.8` is sized so the folded **nacelle** (Ø12.7 centred on the
pivot line) clears the pod wall (21) by 0.45 mm. Rotation signs: FR +,
FL −, RR −, RL + (front folds rearward, rear folds forward along the same
flank). The paddle is born at the claw Ø6.4, swells to an 11 mm shoulder
7 mm out, then two concave flank scoops give the waist before the Ø12.4
cup blend — the root rotates inside the lobe sandwich (mouth ±88°, the
sandwich stays tied by a 75° C-pillar plus both full plates).

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
corners). The arm's Ø6.4 claw rides an **M2 × 12** screw. Springs preload
toward DEPLOYED.

- **Deployed stop + detent**: the claw carries a small dome that rides a
  shallow groove in the slot ceiling and clicks into a deeper recess at the
  deployed angle. Forward-flight drag tends to fold the FRONT arms, so
  their detent is load-bearing — first-print item to verify (`TUNE`).
- The clevis mouth opens ±76° around the sweep (the tapered bar root hugs
  the barrel), leaving a ~90° C-sector that ties the jaws — plus the full
  top/bottom bridge webs back to the pod corner.

## 3. Mooring at the MOTOR RING — cradles + ejector latch + TOP button

Per the owner's direction, the folded arm is moored to the body **at the
motor receptacle**: each nacelle carries a **circumferential groove at
mid-height** (z 3.5–7.5, 0.7 deep — « l'encoche au milieu du cercle
récepteur ») and docks against the flank at (±27.8, ∓22.3):

- a **far-side flexing lip** (body-centre side — the pivot side is the
  folded beam's corridor) carries **two grip bumps straddling the
  equator**: they snap 0.55 into the groove → over-centre retention at the
  heaviest point of the arm — the best hold;
- an **inboard stop pad** on the wall takes the spring preload;
- **fold-in needs NO button**: push the arms in until the cradles click.

**Release — the sliding ejector latch (shared V1/V2):** two rails inside
the side walls end in **45° wedges** behind each docked nacelle (through
wall windows, 1 mm standoff at rest). Slider pushed **rearward 4.5 mm** →
the wedges cam the nacelles **outboard past the lips** → the torsion
springs finish the deploy. Return: small rubber band to the floor hooks
(printed-flex spring is the planned upgrade, `TUNE`).

- **V1 button — ON TOP**: a vertical pin (head proud of the capot at
  (0, −26.6); tip guided in a floor boss) whose **cone cams the slider's
  crossbar rearward** — press down, arms pop open, umbrella style.
- **V2 servo**: a 3.7 g nano-servo drives `servo_cam` (Ø9 disc + lobe)
  against the same crossbar. The V1 button stays as a manual backup.

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
