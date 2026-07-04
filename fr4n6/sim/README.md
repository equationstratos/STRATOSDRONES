# Fr4n6-001 simulation — same Gazebo plugin, 5" physics

The Gazebo Harmonic plugin (`sim/gazebo/StratosFcSystem.cc`) and the SITL
runner already read the airframe from the SDF — the Fr4n6 is a new model
folder, not new sim code.

## Model parameters (M0 estimates, refine at M3)

| Quantity | Fr4n7-001 | **Fr4n6-001** |
|---|---|---|
| Mass (AUW) | 0.092 kg | **0.62 kg** (4S 1500) / 0.78 kg (6S Li-ion) |
| Wheelbase | 118 mm | **220 mm** |
| Ixx / Iyy / Izz | ~6e-5 / 6e-5 / 1e-4 | **~2.9e-3 / 2.9e-3 / 5.2e-3 kg·m²** |
| Rotor | 76 mm, 8520 brushed | **127 mm, 2207 1750 KV** |
| Max thrust/rotor | ~0.35 N | **~11 N** (5×4.3×3 @ 4S) |
| Hover throttle | ~55 % | **~28 %** |

## M3 deliverables

1. `sim/models/stratosdrone_fr4n6/model.sdf` — scaled visuals + the
   inertias above, same `StratosFcSystem` plugin block (`bind_ip` per
   drone, as today).
2. `spawn_swarm.sh --model fr4n6` (and mixed fleets: some Fr4n7, some
   Fr4n6 on the same loopback range — same TelloSwarm script drives both).
3. `sim/tests/` mission parity: hover, square, swarm, plus an outdoor-
   style 8 m/s dash only the Fr4n6 can do.
4. Site playground: a `?model=fr4n6` variant (bigger grid pitch, scaled
   kinematic constants) once M3 lands.
