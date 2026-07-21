# STRATOS LoRa ground dongle

The PC talks to the TinyHoop fleet by **radio, not Wi-Fi**. That radio side is
an off-the-shelf **ESP32 + SX1262** board running a tiny *transparent bridge*:
it forwards raw `fc_lorap` frames between USB-serial and the LoRa air, nothing
more. `stratospy.lora.LoRaLink` frames/deframes; the dongle just relays.

## Buy (ready-to-use, ~15-25 €)

Any ESP32-S3 + SX1262 dev board with USB-C works. Recommended:

- **Heltec WiFi LoRa 32 V3** (ESP32-S3 + SX1262, 863-928 MHz, u.FL/SMA) — the
  reference; pin map below matches it.
- **LilyGO T3-S3** (ESP32-S3 + SX1262) — equivalent, adjust the pins.

Pick the **868 MHz** variant for EU (915 MHz for the Americas — set the same
band on the drones' `hardware/pcb_tinyhoop` module and in the firmware).

## Flash the bridge

Two options; the Arduino one is the fastest:

### Arduino (RadioLib)
1. Arduino IDE → boards: *esp32* by Espressif → select "Heltec WiFi LoRa 32(V3)".
2. Library Manager → install **RadioLib**.
3. Open [`bridge.ino`](bridge.ino), set `BAND` to your region, upload.

### ESP-IDF
The same logic ports to ESP-IDF with the `sx1262.c` driver from
[`../../firmware/components/drivers/`](../../firmware/components/drivers/) — the
drone and the dongle then share one SX1262 driver. See the header of
`bridge.ino` for the exact command sequence.

## Serial wire framing (dongle ↔ PC)

USB-serial is a byte stream, so each LoRa frame is wrapped:

```
0x7E | len (1 byte) | fc_lorap frame (len bytes)
```

in **both** directions. `LoRaLink.send_frame()` writes it; `LoRaLink.poll()`
reads it. Baud 921600. This is the *only* thing the bridge adds on top of the
radio — it never parses `fc_lorap` itself, so protocol changes need no dongle
re-flash.

## Use

```python
from stratospy.lora import LoRaLink, StratosLoRaDrone
link = LoRaLink("/dev/ttyUSB0", swarm_id=0)

d1 = StratosLoRaDrone(link, drone_id=1)
d1.connect(); d1.mode("stab"); d1.takeoff()
d1.figure("circle", 100, 8000, 1); d1.send("show start 0")

# or a whole choreography (stratospy.show):
#   Show.from_json("…").upload_lora(link)
print(link.telemetry())     # {1: {state, x_cm, …, bat_pct, rssi_dbm}}
```

## Honesty (M0)

`bridge.ino` is written from the RadioLib API and the EU868 profile that
matches `sx1262.c` / `stratospy.lora`; it **compiles against RadioLib but has
not been flashed/flown here**. Verify the SX1262 pins for your exact board and
the regional band before transmitting — 868/915 MHz is licence-free only
within the ETSI/FCC duty-cycle limits (see
`../../hardware/pcb_tinyhoop/KNOWN_GAPS.md` §F).
