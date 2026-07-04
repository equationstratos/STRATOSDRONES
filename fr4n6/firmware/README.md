# Fr4n6-001 firmware — same `fc_core`, new backends

No fork. The flight stack is the repo's `fc_core/` (estimator, commander,
mixer, Tello SDK 2.0 parser) compiled with Fr4n6 backends and parameters —
exactly the Crazyflie→Bolt relationship: one firmware, two airframes.

## What's shared verbatim

- `fc_core/` — control, estimation, SDK parser, swarm semantics.
- `firmware/main/wifi_link.c` — C6 Wi-Fi 6 AP/STA, 192.168.10.1.
- `firmware/main/video_task.c` — OV5647 → HW H.264 → UDP 11111.
- Sensor drivers: `icm42688.c`, `spl06.c`, `vl53l1x.c`, `pmw3901.c`.
- The Android app, `stratospy`, djitellopy, the site playground.

## New (M2 work, tracked here)

| Backend | Replaces | Notes |
|---|---|---|
| `outputs_dshot.c` | `outputs.c` LEDC 20 kHz brushed PWM | DSHOT600 ×4 on P4 RMT; fallback DSHOT300/OneShot125; bidir-DSHOT later |
| `power_sense.c` | 100k/100k 1S divider | 2–6S divider + shunt amp → `battery?` %, sag-compensated |
| `esc_telem.c` | — | 4-in-1 UART telemetry (temp/RPM/current) → SDK `param` reads |
| `gps_task.c` | — | u-blox M10 UART; feeds outdoor position hold (M3+) |

## Parameter preset (apply with the SDK `param` extension)

`fc_core` params scale with the airframe; starting point (M0 estimates,
tune at M4):

```
param mass            0.62      # kg, 4S 1500 sport build
param arm_len         0.110     # m
param yaw_rate_max    260       # dps (5" can yaw much faster than 3")
param angle_max       35        # deg (education default; 45+ sport)
param vel_xy_max      8.0       # m/s outdoor cap (SDK 'speed' still 10-100 cm/s)
param takeoff_height  1.2       # m
param takeoff_vz      1.0       # m/s
param land_vz         0.6       # m/s
param flip_enable     0         # OFF by default on the 5" (safety)
param flip_min_bat    60
param batt_cells      4         # 4 or 6
```

The SDK surface (`command/takeoff/land/go/curve/flip/rc/…`) is identical —
`sdk/python/examples/03_swarm.py` must fly a mixed Fr4n7+Fr4n6 swarm with
zero changes. That's the acceptance test for this folder.
