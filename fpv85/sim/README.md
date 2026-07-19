# fpv85 sim — parameter targets (Gazebo port = M3)

The browser **playground** (../viz/, `?playground=1`) is the M0 simulator:
same keyboard flight + presets as the Fr4n7 one, rebound on this airframe.

Gazebo/SITL port (M3) needs a new `sim/models/stratosdrone_fpv85/model.sdf`
AND new plugin constants — the thrust model is hard-coded in
`sim/gazebo/StratosFcSystem.cc:200` (`arm, kT, cQ, tau`), not read from the
SDF. Targets (TUNE):

| Param | Fr4n7 | fpv85 target |
|---|---|---|
| mass | 0.092 | **0.070** |
| arm | 0.0417 | **0.0230** |
| kT (N per unit duty) | 0.42 | **~0.42** (0802@2S 40 mm ≈ 43 g ≈ 0.42 N) |
| cQ | 0.006 | ~0.005 |
| battery | 4.12 V | **8.0 V (2S)** |
