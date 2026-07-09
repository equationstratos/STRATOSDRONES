# STRATOSDRONE SDK reference

STRATOSDRONE speaks the **DJI Tello SDK 2.0** text protocol over UDP, so any
Tello client works unchanged. Implementation: `fc_core/src/fc_sdk.c`.

- Commands in:  `<drone>:8889`  (replies come back from the same socket)
- State out:    `<client>:8890` at 10 Hz
- Video out:    `<client>:11111` — raw H.264 Annex-B (real) / from `gz_video_bridge` (sim)

Send `command` first to enter SDK mode (everything before it is ignored, like
the Tello). Motion commands reply `ok` only when the motion **completes**;
`rc` and `emergency` send no reply.

## Supported commands

| Command | Notes |
|---|---|
| `command` | enter SDK mode → `ok` |
| `takeoff` / `land` | auto height ≈ 0.8 m; reply on completion |
| `emergency` | cut motors immediately (no reply); `command` again to re-arm via reset |
| `up/down/left/right/forward/back x` | x = 20–500 cm |
| `cw x` / `ccw x` | x = 1–360° |
| `flip l/r/f/b` | battery-gated |
| `go x y z speed` | cm, speed 10–100 cm/s |
| `curve x1 y1 z1 x2 y2 z2 speed` | arc through two points |
| `stop` | hover in place |
| `speed x` / `speed?` | set/get cm/s |
| `rc lr fb ud yaw` | −100..100 sticks, no reply |
| `battery?` `time?` `wifi?` `sdk?` `sn?` | reads (`sdk?`→`20`) |
| `streamon` / `streamoff` | H.264 on 11111 |
| `wifi ssid pass` / `ap ssid pass` | reconfigure AP / join as STA (swarm); reboots |
| `mon` `moff` `mdirection` | accepted (`ok`) but mission pads are not in v1 |

## STRATOS extensions (additive; stock clients unaffected)

| Command | Effect |
|---|---|
| `video 720` / `video 1080` | select H.264 stream height (default 720p30) |
| `param <name> <value>` / `param <name>?` | set/get a flight-core gain (see `fc_params.c`) |
| `EXT led r g b` | set the RGB status LEDs (0–255) |
| `EXT version?` | → `stratos <version>` |
| `deploy` | **Fr4n7-F foldable only — SPECIFIED, NOT YET IMPLEMENTED.** Releases the folded-arm latch (V2 servo cam, ≈1 s) then `ok`; `error Not foldable` otherwise. Full spec + implementation map: `foldable/DESIGN.md` §4 |

## State packet (10 Hz, Tello format)

```
pitch:%d;roll:%d;yaw:%d;vgx:%d;vgy:%d;vgz:%d;templ:%d;temph:%d;
tof:%d;h:%d;bat:%d;baro:%.2f;time:%d;agx:%.2f;agy:%.2f;agz:%.2f;
```

## Python

Stock djitellopy works:

```python
from djitellopy import Tello
t = Tello(host="192.168.10.1")   # drone AP; or a sim loopback IP
t.connect(); t.takeoff(); t.move_forward(50); t.land()
```

`stratospy` adds the extensions and simulation helpers — see
`sdk/python/stratospy/` and `sdk/python/examples/`.
