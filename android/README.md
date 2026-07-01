# Tello Pilote (Android)

A minimal Android ground-control app: takeoff/land/emergency/flip buttons, dual
virtual joysticks (Mode 2), live H.264 video, and battery/height/flight-time
telemetry. Originally written against the real DJI Tello; imported here
because STRATOSDRONE speaks the same Tello SDK 2.0 wire protocol
(`fc_core/src/fc_sdk.c`), so the app flies STRATOSDRONE unmodified.

| Class | Role |
|---|---|
| `net/WifiBinder` | Binds the app's traffic to the Wi-Fi network (required since Android 10 — the drone's AP has no internet, so the OS won't route to it otherwise) |
| `tello/TelloController` | UDP command socket (8889) + state telemetry socket (8890), `rc`/keepalive loop |
| `tello/TelloVideoReceiver` | Reassembles the H.264 stream from UDP 11111 (1460-byte chunks, short packet = end of frame) |
| `tello/H264Renderer` | Decodes with `MediaCodec` straight to the preview `Surface` |
| `ui/JoystickView` | Virtual joystick, normalized `[-1, 1]` |
| `MainActivity` | Wires it all together |

## Changes from the original (Tello) version

Two constants tied to the specific drone, corrected to match STRATOSDRONE's
firmware instead of the real Tello:

- `res/values/strings.xml` — status text referenced the real Tello's AP name
  (`TELLO-XXXXXX`); updated to STRATOSDRONE's (`STRATOS-XXXXXX`, set in
  `firmware/main/wifi_link.c`).
- `tello/H264Renderer.kt` — decoder was configured for the real Tello's video
  size (960×720); updated to STRATOSDRONE's default 720p encode size
  (1280×720, see `firmware/main/video_task.c`).

`TelloController.kt`'s hardcoded drone IP (`192.168.10.1`) needed no change —
STRATOSDRONE's AP is now pinned to that same address (see
`firmware/main/wifi_link.c`) specifically so unmodified Tello SDK clients,
this app included, work without any IP configuration step.

Everything else (command set, state-packet parsing, video chunking,
RC/keepalive cadence) was already an exact match — the real Tello and
STRATOSDRONE both implement Tello SDK 2.0.

## Build

Open `android/` in Android Studio (or `cd android && ./gradlew assembleDebug`).
Requires SDK 35 / min SDK 26 (Android 8+ for the joysticks and video pipeline;
Android 10+ needed for `WifiBinder` to actually work, since that's when
Android started requiring apps to explicitly bind to a network with no
internet access).

1. Power on the drone, connect the phone to its Wi-Fi (`STRATOS-XXXXXX`, open,
   no password by default).
2. Launch the app, tap **Connecter**.
3. **Décoller** / **Atterrir**, dual joysticks for flight, long-press
   **URGENCE** to cut the motors.

## Known gaps

- No `setresolution`/1080p toggle in the UI yet, even though both the app's
  decoder path and the firmware (`fc_sdk.c`) already support switching — it's
  just not wired to a button.
- Not tested against real hardware yet (STRATOSDRONE's PCB is still being
  routed — see `hardware/pcb/KNOWN_GAPS.md`); verified so far by protocol/code
  review only.
