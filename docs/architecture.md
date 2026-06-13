# STRATOSDRONE architecture

A Tello-EDU-class drone whose flight behaviour is identical in simulation and
on real hardware, because the same flight-control code runs in both.

## The shared core (`fc_core/`)

`fc_core` is a pure-C99 library with **no OS, heap, or platform dependencies**.
One `fc_core_t` instance is one drone. It is compiled, unchanged, into:

- the **ESP32-P4 firmware** (`firmware/components/fc_core`), and
- the **Gazebo plugin** (`sim/gazebo/StratosFcSystem.cc`), and
- the **host tests** and **SITL runner**.

```
sensors ──► fc_core_imu_update()     1 kHz : Mahony AHRS → rate PID → mixer
            fc_core_flow_update()   100 Hz : optical-flow body velocity
            fc_core_tof_update()     50 Hz : ToF height (primary)
            fc_core_baro_update()    50 Hz : barometric height (fallback)
                  │
                  ▼
       estimators (decoupled, tunable, unit-tested)
         • complementary attitude (quaternion)
         • 3-state vertical KF  [z, vz, accel_bias]
         • flow velocity + leaky position hold
                  │
                  ▼
       cascaded control:  position 25 Hz → velocity 100 Hz
                          → attitude 500 Hz → rate 1 kHz → X-mixer
                  │
                  ▼
            fc_core_get_motors() → 4× duty 0..1
```

Why decoupled filters instead of one big EKF: the EKF is exactly what makes
the referenced ESP-Drone port flaky and hard to tune. Decoupled vertical and
horizontal estimators are independently unit-testable (CSV-replay fixtures in
`fc_core/test/`) and an EKF can be swapped behind the same API later.

## Protocol (`fc_core/src/fc_sdk.c`)

Transport-free Tello SDK 2.0 parser. The platform owns the UDP sockets and
pumps it. Because the wire protocol is byte-compatible with the real Tello,
**unmodified djitellopy** (and existing Tello swarm scripts) fly both the
simulator and the hardware. Extensions (`video 1080`, `param`, `EXT led`) are
additive and never break stock clients.

## Hardware vs simulation parity

| | Real (`firmware/`) | Simulated (`sim/`) |
|---|---|---|
| Flight code | `fc_core` on ESP32-P4 core 0 | `fc_core` in the gz plugin |
| IMU | ICM-42688-P @1 kHz SPI | gz IMU sensor + noise |
| Flow/ToF/baro | PMW3901 / VL53L1X / SPL06 | analytic models + same noise |
| Motors | 4× LEDC PWM → MOSFETs | first-order thrust → gz wrench |
| Camera | OV5647 → P4 H.264 → UDP 11111 | gz camera → libx264 → UDP 11111 |
| SDK endpoint | UDP on the drone's AP/STA IP | UDP on a per-drone 127.0.0.X |

The rotor/airframe constants in the SIL plant (`fc_core/test/sil_plant.c`) and
the Gazebo plugin are the same (92 g, 118 mm, first-order motor lag), so a
controller tuned in simulation transfers to the bench.

## Compute split on the ESP32-P4

- **Core 0**: the 1 kHz flight loop (`flight_task.c`) — sensors, `fc_core`,
  motor output. Highest priority, paced by the IMU data-ready interrupt.
- **Core 1**: Wi-Fi (via the ESP32-C6 over SDIO/esp-hosted), the SDK UDP
  task (`net_task.c`), and the hardware-H.264 video pipeline (`video_task.c`).

The two cores exchange only small queued messages (command lines in, replies
and state packets out), so the flight loop never blocks on the network.
