# TinyHoop MK1 sim — parameter targets (Gazebo port = M3)

The browser **playground** ([`../viz/`](../viz/), `?playground=1`) is the M0
simulator: keyboard flight + SDK scripts, kinematic, airframe-agnostic.

Because the mode manager and show executor live in `fc_core`, the **swarm and
show pipeline already runs in the existing Gazebo/SITL** with zero plugin
changes — the `mode`, `show`, `figure` and `timesync` verbs travel over the
same UDP the sim already speaks. Fly `../../sdk/python/examples/06_show_swarm.py`
against `sim/spawn_swarm.sh 3` today.

What a **dedicated Gazebo model** (M3) adds is dynamics fidelity for the 2.5"
airframe: a new `sim/models/stratos_tinyhoop/model.sdf` plus plugin thrust
constants (hard-coded in `sim/gazebo/StratosFcSystem.cc`, not read from SDF).
Targets (TUNE):

| Param | Fr4n7 | TinyHoop MK1 target |
|---|---|---|
| mass | 0.092 | **0.130** (2S build; ~0.145 with O4/3S) |
| arm (motor offset) | 0.0417 | **~0.0570** (wide-X, wheelbase 115 mm) |
| kT (N per unit duty) | 0.42 | **~1.0** (1203@2S-3S on 2520 ≈ 100 g ≈ 1.0 N) |
| cQ | 0.006 | ~0.007 |
| battery | 4.12 V | **8.0 V (2S) / 12.0 V (3S)** |

For a multi-drone show rehearsal, spawn N drones (`spawn_swarm.sh N`) and use
`stratospy.show.Show.upload_sim()` + `start_sim()`; the LoRa `TIME_BEACON`
that syncs the real fleet is replaced by the `timesync` / `show start` verbs
over UDP.
