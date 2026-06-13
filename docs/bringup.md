# Bring-up — first power-on to first hover

> Read `safety.md` first. Keep **props off** until step 4 says otherwise.

## 1. Toolchain

```bash
git clone --branch v5.4 --recursive https://github.com/espressif/esp-idf
cd esp-idf && ./install.sh esp32p4 && . ./export.sh
```

## 2. Flash the ESP32-C6 Wi-Fi co-processor (once)

The C6 runs the standard **esp-hosted** slave firmware; the P4 talks to it
over SDIO. Flash the C6 first, via its UART pads (`J11`: GND/TXD/RXD, hold
`C6_BOOT` low at reset):

```bash
# from the esp-hosted repo, build the C6 slave for SDIO, then:
esptool.py --chip esp32c6 -p /dev/ttyUSB0 write_flash @flash_args
```

(See the esp-hosted docs for the exact slave build; the P4 can also OTA the
C6 later over SDIO.) **VERIFY** the SDIO pin wiring matches `board_pinmap.h`
and the build's sdkconfig before relying on this.

## 3. Flash the ESP32-P4 flight firmware

```bash
cd firmware
idf.py set-target esp32p4
idf.py -p /dev/ttyACM0 flash monitor     # native USB-Serial-JTAG
```

On boot the status LED is amber (booting) → green (sensors OK). **Red** means
a sensor failed to init — check the monitor log; flight stays inhibited.

## 4. Pre-flight checks — PROPS OFF

1. Connect a charged 1S pack. Confirm green LED and that `battery?` is sane.
2. Connect to the drone's Wi-Fi (`STRATOS-XXXXXX`) and:
   ```python
   from djitellopy import Tello
   t = Tello(host="192.168.10.1"); t.connect()
   print(t.get_battery(), t.query_serial_number())
   ```
3. **Motor direction/response, props still off:** `t.takeoff()` and watch which
   way each motor spins (M1 FR/CCW, M2 BR/CW, M3 BL/CCW, M4 FL/CW — see the
   mixer in `fc_core/src/fc_control.c`). Tilt the drone by hand: the motors
   that should speed up to correct must speed up. If a motor spins the wrong
   way, swap its two leads. `t.emergency()` to stop. **Do not proceed until
   directions and the tilt response are correct.**

## 5. Sensor calibration

- **Gyro bias**: keep the drone still on power-up; the AHRS learns the bias.
- **Accelerometer level**: rest on a flat surface; confirm `agz` ≈ −1000.
- **Optical flow / ToF**: point at a textured surface 0.1–2 m away; confirm
  `tof` tracks height and `vgx/vgy` read ~0 when still. Featureless/shiny
  floors degrade flow — fly over texture.

## 6. First hover — props on, guards on, open area

`t.takeoff()`, let it self-hover on flow + ToF, watch for drift, then
`t.land()`. If it drifts or oscillates, tune in small steps via the `param`
extension (start with `pos_xy_kp`, then `vel_xy_kp`); the same gains were
tuned in the SIL bench (`fc_core/test/test_sil_flight.c`), so changes there
should track the sim. Log and compare sim vs real telemetry to close the loop.

## Troubleshooting

| Symptom | Look at |
|---|---|
| Red LED at boot | sensor init in the monitor log; SPI/I2C wiring |
| No Wi-Fi | C6 slave firmware + SDIO wiring (`board_pinmap.h`) |
| Drifts in hover | flow quality (texture/lighting), `pos_xy_kp`/`vel_xy_kp` |
| Oscillates | lower `rate_rp_kp`/`att_kp`; check prop balance & IMU mount |
| No video | `streamon`; camera FFC orientation; `video 720` vs `1080` |
| Won't climb | weight (≤95 g), battery health, motor wear |
