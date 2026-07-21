"""TinyHoop MK1 — on-board figure generators (single drone, sim).

The `figure` verb compiles a parametric path into the drone's show buffer
(fc_figures.c), then `show start` flies it — no keyframe upload needed. Great
for practising one drone before choreographing the fleet.
"""
import sys
import time

sys.path.insert(0, __file__.rsplit("/examples", 1)[0])
from stratospy import StratosDrone, enable_sim, spawn_sitl

enable_sim()
sitl = spawn_sitl(index=2)

d = StratosDrone(host=sitl.ip)
d.connect()
d.takeoff()

d.send_control_command("mode swarm")   # the mode that runs the show executor

# a 1 m circle over 8 s
d.send_control_command("figure circle 100 8000 1")
d.send_control_command("show start 0")
time.sleep(9)
print("circle done, pos:", d.get_state_field("x") if hasattr(d, "get_state_field") else "?")

# a climbing spiral: r=80 cm, +60 cm/turn, 2 turns over 12 s
d.send_control_command("figure spiral 80 60 6000 2")
d.send_control_command("show start 0")
time.sleep(13)

d.send_control_command("mode prog")
d.land()
d.end()
sitl.stop()
print("figures demo complete")
