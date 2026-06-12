"""Takeoff, hover, land — against a simulated or real STRATOSDRONE.

Simulated:  cd sim && cmake -B build && cmake --build build
            ./build/sitl_runner --ip 127.0.0.2     (or use spawn_sitl below)
            python 01_hover.py
Real drone: connect to its Wi-Fi, then: python 01_hover.py --real
"""
import sys
import time

sys.path.insert(0, __file__.rsplit("/examples", 1)[0])
from stratospy import StratosDrone, enable_sim, spawn_sitl

real = "--real" in sys.argv
sitl = None
if real:
    host = "192.168.10.1"  # drone in AP mode
else:
    enable_sim()
    sitl = spawn_sitl(index=2)
    host = sitl.ip

drone = StratosDrone(host=host)
drone.connect()
print(f"connected — battery {drone.get_battery()}%  fw {drone.firmware_version()}")

drone.takeoff()
for _ in range(5):
    time.sleep(1)
    print(f"  h={drone.get_height()} cm  tof={drone.get_distance_tof()} cm")
drone.land()
print(f"flight time: {drone.get_flight_time()} s")
drone.end()
if sitl:
    sitl.stop()
