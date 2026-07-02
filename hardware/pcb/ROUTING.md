# STRATOSDRONE PCB — Routing (AI-assisted, Freerouting)

The board is placed and plane-poured by `scripts/gen_pcb.py`, but the signal
nets ship as ratsnest. This document explains how the signals get routed, how
to reproduce it, and the fallbacks if you'd rather route on your own machine or
with an online AI service.

## TL;DR — what was done

**Current state: 1384 track segments + 172 vias, ~106 pad-pairs (73 nets)
still ratsnest — see `KNOWN_GAPS.md` item 1 for the exact net list and the
fastest way to close it.** Headless Freerouting 2.1.0 in *this* sandbox
converges on the routing (5-7 min) but its session-export step (`-do`)
never actually writes the `.ses` file — reproduced 5 ways (see KNOWN_GAPS),
looks like a real bug in that version's post-route save path under a
headless X server. `connect_power()` (pure `pcbnew`, no Freerouting, no
display needed) is still safe to re-run for extra power-stitch vias.
Don't burn more time re-attempting the exact headless flow below without a
different Freerouting version or a real display (Fallback B).

**A custom in-repo grid router was written and run** to try to close the 106
without Freerouting (`scripts/finish_routing.py` — clearance-correct A* on a
0.1 mm grid, F.Cu/B.Cu, tiers 0.15→0.127 mm, exact SHAPE::Collide checks,
differential MIPI/USB/crystal excluded; plus `scripts/stitch_planes.py` for
plane ties). **It closes essentially nothing new on this board, and that is
the expected result, not a bug** — verified with `GetUnconnectedCount`:
(1) the plane pads are already thermal-tied by the fill (19 stitch vias →
count unchanged `106→106`), so the 106 are all signal/local-power links; and
(2) every stuck signal net has an endpoint pad **boxed in** by neighbouring
pins' already-routed escape tracks (0 free grid neighbours), so closing them
needs **push-and-shove** rip-up routing that a greedy one-net-at-a-time A*
can't do. Net: use KiCad's **interactive router** (it shoves) or a desktop
autorouter — the scripts stay as the clearance-checker / island analyser and
the DSN/SES import path, not as a finisher for this layout.

`scripts/route_board.py` runs a fully-automated route in this repo (this is
how the *existing* 1384/172 got there, across earlier sessions):

1. **Export Specctra DSN** (`stratosdrone.dsn`) from the placed board via the
   `pcbnew` Python API, with the two **outer-layer pours temporarily removed**
   (`F.Cu` GND, `B.Cu` VBAT) so the autorouter has two free signal layers. The
   inner planes `In1.Cu` (GND) and `In2.Cu` (3V3) stay, so those nets reach
   copper through short vias.
2. **Autoroute with Freerouting** (the open-source maze/rip-up router) running
   **headless under `xvfb`** — `-de stratosdrone.dsn -do stratosdrone.ses`.
3. **Import the routed wires + vias** (`stratosdrone.ses`) back onto the full
   board (all four zones intact) with a self-contained S-expression parser.
4. **Fill zones + export gerbers** with `scripts/fill_zones_export.py`.

```
make -C hardware/pcb board        # (re)generate placed board
python3 scripts/route_board.py    # export DSN -> Freerouting -> import SES
python3 scripts/check_consistency.py
python3 scripts/fill_zones_export.py
```

## Why the outer pours are dropped for routing

This is a 4-layer stackup `F.Cu / In1.Cu(GND) / In2.Cu(3V3) / B.Cu`. The
generator pours copper on **all four** layers (GND top, VBAT bottom, plus the
inner planes). If both outer layers are full copper, the maze router has *no
free layer* and fails with "the maze search algorithm could not be created".
`route_board.py` removes only the `F.Cu`/`B.Cu` pours **for the DSN export**;
the real board keeps them and they re-fill **around** the finished traces when
`fill_zones_export.py` runs (a normal ground/VBAT fill on a signal layer).

## Reproducing / re-routing

Requirements: Java 17+, `xvfb` (Linux), and a Freerouting jar (v2.1.0
recommended). The script looks for the jar in `/tmp/fr-v2.1.0.jar`,
`/home/user/freerouting.jar`, … or pass `--jar`.

```
python3 scripts/route_board.py --passes 20          # more passes = tighter
python3 scripts/route_board.py --skip-route         # just re-import existing .ses
```

Notes / gotchas baked into the script:
- Freerouting **consumes its input** file, so we always route on a throwaway copy.
- Freerouting 2.1.0's telemetry/version-check throws on a null network reply and
  its crash handler needs a display; we disable telemetry in `freerouting.json`
  **and** run under `xvfb` so the exception is non-fatal.
- `gui.enabled=false` breaks input loading in 2.1.0 — keep GUI on, use `xvfb`.

## Fallback A — online AI autorouter (no install)

`stratosdrone.dsn` is committed precisely so you can route it anywhere:

1. Open **https://www.deeppcb.ai** (cloud AI autorouter, free tier), create a
   project, and upload `hardware/pcb/stratosdrone.dsn`.
2. Run the autoroute; download the resulting `.ses` session file.
3. Drop it in as `hardware/pcb/stratosdrone.ses` and finish locally:
   `python3 scripts/route_board.py --skip-route && python3 scripts/fill_zones_export.py`
   (or hand me the `.ses` and I'll import + finalize).

## Fallback B — Freerouting on your Windows 10 machine

Freerouting is a single Java app — no build needed:

1. Install a Java runtime (e.g. Adoptium Temurin 17+).
2. Download `freerouting-x.y.z.jar` from
   https://github.com/freerouting/freerouting/releases and double-click it
   (or `java -jar freerouting-*.jar`).
3. **File → Open** `hardware/pcb/stratosdrone.dsn`, press **Autoroute**, let it
   finish, then **File → Export Specctra Session** → save `stratosdrone.ses`.
4. Either import in KiCad 9 (**File → Import → Specctra Session**) and fill
   zones (hotkey **B**), or run `route_board.py --skip-route` to import here.

## Fallback C — KiCad 9 native

KiCad has no built-in autorouter, but you can route by hand: open
`stratosdrone.kicad_pcb`, route the ratsnest, fill zones (**B**), then
**File → Fabrication Outputs → Gerbers**. The critical nets below are worth
hand-routing regardless of which autorouter you use.

## Review before mass production (autoroute caveats)

A pure autoroute connects everything but does **not** impedance-tune or
length-match. Before a production run, review/hand-tune:

- **USB 2.0 `USB_D+/USB_D-`** — route as a ~90 Ω differential pair, matched
  length, no stubs, reference to a solid plane.
- **MIPI CSI camera pairs** `CSI_D0±`, `CSI_D1±`, `CSI_CK±` — ~100 Ω
  differential, tightly matched, short.
- **ESP32-C6 antenna** — keep the existing keepout clear of copper/traces; the
  RF feedline wants controlled impedance.
- **Power traces** (VBAT, motor FET drains) — widen beyond the default signal
  width for current.
