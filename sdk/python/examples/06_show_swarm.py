"""TinyHoop MK1 — a 3-drone choreography from JSON (sim-first).

Loads examples/shows/demo_triangle.json, safety-checks fleet separation and
speed, previews it in the Gazebo/SITL sim over UDP (the same `show key` /
`show start` verbs the real drones run), and — if a LoRa dongle is present —
uploads the identical keyframes over the radio with a synced start.

    ./sim/spawn_swarm.sh 3        # or three SITL instances (auto below)
    python3 sdk/python/examples/06_show_swarm.py
"""
import os
import sys
import time

sys.path.insert(0, __file__.rsplit("/examples", 1)[0])
from stratospy import StratosDrone, enable_sim, spawn_sitl
from stratospy.show import Show

SHOW = os.path.join(os.path.dirname(__file__), "shows", "demo_triangle.json")

show = Show.from_json(SHOW)

# 1. safety gate — never upload a show that fails separation / speed
problems = show.check(min_sep_cm=60, vmax_cms=200)
if problems:
    print("SHOW UNSAFE — fix before flying:")
    for p in problems[:10]:
        print("  -", p)
    sys.exit(1)
print(f"'{show.name}': {len(show.tracks)} drones, safety check OK")

# 2. preview in the sim (same verbs the drones run)
enable_sim()
sitls = {i: spawn_sitl(index=i + 1) for i in show.tracks}   # ids 1,2,3 -> .2,.3,.4
drones = {}
for did, sitl in sitls.items():
    dv = StratosDrone(host=sitl.ip)
    dv.connect()
    dv.takeoff()
    drones[did] = dv

show.upload_sim(drones)          # mode swarm + show clear + show key ...
show.start_sim(drones, t0_ms=0)  # synced start (UDP; TIME_BEACON on real LoRa)
print("show running in sim…")
time.sleep(13)

for dv in drones.values():
    dv.send_control_command("mode prog")
    dv.land()
    dv.end()
for s in sitls.values():
    s.stop()

# 3. real fleet (optional): identical keyframes over LoRa
#   from stratospy.lora import LoRaLink
#   link = LoRaLink("/dev/ttyUSB0")     # the dongle (sdk/lora_dongle/)
#   show.upload_lora(link, t0_delay_ms=3000)
print("swarm show complete")
