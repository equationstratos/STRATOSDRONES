"""TinyHoop MK1 — the four flight modes, from a Python script (sim).

MANUAL needs a live radio, so it is refused here (no ELRS in the sim) — that
refusal is the safety design, not a bug. STABILIZED / PROGRAM / SWARM are all
driveable from the PC. On real hardware the same `mode` verb travels over
LoRa (see 06_show_swarm.py's LoRa path and stratospy.lora).
"""
import sys

sys.path.insert(0, __file__.rsplit("/examples", 1)[0])
from stratospy import StratosDrone, enable_sim, spawn_sitl

enable_sim()
sitl = spawn_sitl(index=2)

d = StratosDrone(host=sitl.ip)
d.connect()
print("mode at boot:", d.send_read_command("mode?"))       # prog (default)

# MANUAL is radio-only: refused from the PC (expected)
try:
    d.send_control_command("mode manual")
    print("manual: unexpectedly accepted")
except Exception:
    print("mode manual refused without a live radio (correct)")

# STABILIZED: position hold; the PC can still nudge it with rc velocity
d.send_control_command("mode stab")
print("mode now:", d.send_read_command("mode?"))
d.takeoff()
d.send_rc_control(0, 30, 0, 0)   # ease forward
import time; time.sleep(1.5)
d.send_rc_control(0, 0, 0, 0)    # release -> brakes and holds
print("height after stabilized nudge:", d.get_height(), "cm")

# back to PROGRAM for scripted waypoints
d.send_control_command("mode prog")
d.go_xyz_speed(80, 0, 0, 50)
d.land()
d.end()
sitl.stop()
print("modes demo complete")
