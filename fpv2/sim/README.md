# fpv2 sim — parameter targets (Gazebo port = M3)

Browser playground = `../viz/drone_viewer.html?playground=1` (M0 simulator).

Gazebo/SIL targets (constants hard-coded in `sim/gazebo/StratosFcSystem.cc:200`,
to port at M3):

| Param | Fr4n7 | fpv2 target |
|---|---|---|
| mass | 0.092 | **0.100** |
| arm | 0.0417 | **0.0346** |
| kT (N per unit duty) | 0.42 | **~0.75** (1102@2S 2" ≈ 75 g) |
| battery | 4.12 V | **8.0 V (2S)** |
