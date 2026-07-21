# TinyHoop MK1 — hardware & bill of materials

Two ways to build it: the **DIY STRATOS board** (fully programmable, swarm,
LoRa — the point of this project) or a **ready-to-buy** stack that flies the
JeNo frame today but is *not* programmable. Both share the JeNo Pocket V2
carbon frame (buy the plates from WE are FPV, or cut your own from the DXFs in
[`../cad/dxf/`](../cad/)).

## The custom board (recommended)

**STRATOS TINYHOOP AIO** — [`../../hardware/pcb_tinyhoop/`](../../hardware/pcb_tinyhoop/).
ESP32-P4 + C6 brain (so it runs `fc_core`: the 4 modes, show executor, Tello
SDK), 4× integrated BLHeli_S ESC, PMW3901 + VL53L1X for position hold, an
SX1262 LoRa module (optional) for the fleet link, a CRSF socket for ELRS, an
analog VTX bay, and a GPS connector. Order flow + the fab-blocking VERIFYs are
in that folder's [`KNOWN_GAPS.md`](../../hardware/pcb_tinyhoop/KNOWN_GAPS.md).

## Off-board module BOM (both build paths)

| Part | Choice | Notes |
|---|---|---|
| Frame | JeNo Pocket V2 carbon kit (WE are FPV) **or** cut from [`../cad/dxf/`](../cad/) | 3 mm bottom, 2 mm top/cam |
| Motors | 4× **1203-1303**, ~8000KV (2S) / ~6000KV (3S) | 9 mm mount, e.g. 1303.5 |
| Props | **Gemfan 2520** tri-blade (Avan Rush for Classic/Tank) | 2.5" |
| Battery | 2S-3S **450-560 mAh** LiPo, XT30 | |
| Radio RX | any **ExpressLRS** RX (EP1/RP1, ceramic ant for range) | CRSF socket |
| FPV video | **DJI O4 Lite** (native bay) *or* nano analog cam + 25-400 mW VTX | O4 powered off LiPo, see KNOWN_GAPS §C |
| Handset | ELRS radio (RadioMaster Boxer/Pocket) | |
| Goggles | DJI (for O4) or analog | |
| Ground link | **Heltec LoRa32 V3** (or LilyGO T3S3) dongle | [`../../sdk/lora_dongle/`](../../sdk/lora_dongle/) |
| GPS (optional) | any UART GPS + compass (M10/M8) | J15, for outdoor shows (M4) |
| Hardware | M2 screws/standoffs (bus 14-20 mm), nylon nuts, 18 AWG XT30 pigtail | |

## Ready-to-buy fallback (flies, but NOT programmable/swarm)

If you just want the JeNo airborne now and will add the STRATOS brain later:

- **FC/ESC**: JHEMCU **GHF435AIO V2 20 A** (or GHF722AIO-HD 40 A for O4) —
  Betaflight, 20 A ESCs.
- Same frame + motors + props + battery + ELRS RX + camera/VTX + handset +
  goggles as above.

This gives a normal Betaflight 2.5". It **cannot** do the programmable /
stabilized-show / swarm modes — those need `fc_core` on the STRATOS TINYHOOP
AIO. Treat it as the "learn to fly the airframe" build, then swap the stack.

## What makes it programmable / swarm

Only the **STRATOS TINYHOOP AIO** carries the ESP32-P4 + C6 running `fc_core`.
That is what gives you the Python SDK (`stratospy`), the four modes
(`mode manual|stab|prog|swarm`), the on-board figures (`figure …`), the show
executor, and the LoRa fleet link. The Betaflight fallback flies the frame but
none of that. See [`../DESIGN.md`](../DESIGN.md) for the mode + protocol
design and [`../ROADMAP.md`](../ROADMAP.md) for the M0→M4 path.
