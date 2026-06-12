"""Fly a 1 m square using go_xyz_speed, like a Tello EDU mission."""
import sys

sys.path.insert(0, __file__.rsplit("/examples", 1)[0])
from stratospy import StratosDrone, enable_sim, spawn_sitl

enable_sim()
sitl = spawn_sitl(index=2)

drone = StratosDrone(host=sitl.ip)
drone.connect()
drone.takeoff()
for leg in range(4):
    drone.go_xyz_speed(100, 0, 0, 50)
    drone.rotate_clockwise(90)
    print(f"leg {leg + 1}/4 done, h={drone.get_height()} cm")
drone.land()
drone.end()
sitl.stop()
print("square complete")
