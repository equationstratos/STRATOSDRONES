# Safety

A STRATOSDRONE is a ~90 g machine with four propellers spinning near
40,000 rpm. The props will cut skin and eyes. Read this before powering one up.

## Always

- **Props off for every first power-up** of a new board or new firmware. Verify
  the motors spin the right direction and the mixer responds correctly with
  props removed before you ever fit them.
- **Prop guards on** for all early flights (the printed `prop_guards.scad`).
- Fly in an open space, away from people, pets and faces. Keep bystanders back.
- Keep a hand near the `emergency` cut (kills motors instantly) — in djitellopy,
  `Tello.emergency()`. Bind it to a key in any manual-control script.
- Power order: connect the battery last, with the drone on a flat surface and
  the script not yet armed.

## Never

- Never hand-catch a flying drone. Use `land` or `emergency`.
- Never fly with a swollen, hot, or damaged LiPo. Never charge unattended.
- Never bypass the gate that keeps motors off during boot/flash (the firmware
  drives the FET gates low first thing, and the board has 100 k gate pulldowns
  — do not remove them).

## LiPo handling (1S LiHV/LiPo)

- Charge at ≤1C on the onboard USB-C charger (TP4056, ~1 A). Charge on a
  non-flammable surface.
- Storage charge ≈ 3.8 V/cell if unused for more than a few days.
- Dispose of puffed cells properly; do not puncture.

## First flight checklist

1. Props **off**: power on, confirm sensors initialise (status LED green — see
   `bringup.md`), arm and check each motor's direction/response.
2. Props on, guards on, open area, `streamon` optional.
3. `takeoff`, let it hover, confirm it holds position (optical flow + ToF),
   then `land`. Tune gains via `param` only after a stable hover.
