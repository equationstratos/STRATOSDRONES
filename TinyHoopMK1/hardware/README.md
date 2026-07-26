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

This is the **exact parts list modelled in the 3-D viewer**
([`../viz/drone_viewer.html`](../viz/)) — same references, same quantities.

| Part | Choice | Notes |
|---|---|---|
| Frame | JeNo Pocket V2 carbon kit (WE are FPV) **or** cut from [`../cad/dxf/`](../cad/) | 3 mm bottom, 2 mm top/cam; top plate has a rear **cable slot** for the XT30 |
| Motors | 4× **1104 7500KV** (Readytosky) | 9 mm mount; **3 phase wires per motor** routed along the arm + a **TPU cable guard** per arm (prop protection) |
| Props | **Gemfan 2520** tri-blade (Avan Rush for Classic/Tank) | 2.5" |
| Battery | **DOGCOM 560 mAh 3S 60C**, XT30 | 28 × 52,5 × 18,5 mm; red/black pair with a service loop + **JST-XH** balance lead |
| Radio RX | any **ExpressLRS** 2.4 GHz RX | CRSF socket; PCB in a **TPU cradle**, T-antenna **horizontal** out the rear bay |
| Camera | **DJI O4 Lite** *or* a **nano analog** cam — M12 lens (Flywoo Wylde type) | selector in the viewer; TPU top+bottom mounts, rubber seal, lens cradle, **2 gold cage standoffs** |
| FPV video | **DJI O4 Lite** air unit (native bay) *or* nano analog cam + 25-400 mW VTX | O4 powered off LiPo, see KNOWN_GAPS §C |
| VTX antenna | one of: **DJI O4** · **RHCP LP A1** · **Foxeer Lollipop** · **TrueRC Matchstick** · **Micro Lollipop U.FL** | selector in the viewer; seated head-up in the rear TPU bay |
| Capacitor | **25 V 22 µF** low-ESR | sits in its printed **TPU holder**, clear of the bottom plate |
| Handset | ELRS radio (RadioMaster Boxer/Pocket) | |
| Goggles | DJI (for O4) or analog | |
| Ground link | **Heltec LoRa32 V3** (or LilyGO T3S3) dongle | [`../../sdk/lora_dongle/`](../../sdk/lora_dongle/) |
| GPS (optional) | any UART GPS + compass (M10/M8) | J15, for outdoor shows (M4); mounted **inside** the frame footprint |
| Hardware | M2 screws + **smooth alu standoffs** (14-20 mm), nylon nuts, 18 AWG XT30 pigtail, TPU bumpers | |

## Ready-to-buy fallback (flies, but NOT programmable/swarm)

If you just want the JeNo airborne now and will add the STRATOS brain later:

- **FC/ESC**: JHEMCU **GHF411 AIO** (the board modelled in the viewer) —
  Betaflight; GHF435AIO V2 20 A or GHF722AIO-HD 40 A are drop-in alternatives.
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
