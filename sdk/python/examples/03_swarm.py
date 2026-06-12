"""Three-drone swarm with djitellopy's TelloSwarm — Tello EDU style.

In simulation each drone is its own process on a loopback IP; on real
hardware put each drone in STA mode on your AP (`ap <ssid> <pass>`) and
list their DHCP addresses instead.
"""
import sys

sys.path.insert(0, __file__.rsplit("/examples", 1)[0])
from djitellopy import TelloSwarm

from stratospy import enable_sim, spawn_sitl

enable_sim()
sitls = [spawn_sitl(index=i) for i in (2, 3, 4)]

swarm = TelloSwarm.fromIps([s.ip for s in sitls])
swarm.connect()
print("batteries:", [t.get_battery() for t in swarm.tellos])

swarm.takeoff()
# spread out: each drone flies a different leg in parallel
swarm.parallel(lambda i, t: t.go_xyz_speed(60 + 40 * i, (i - 1) * 80, 0, 60))
swarm.parallel(lambda i, t: t.rotate_clockwise(120 * (i + 1)))
swarm.land()
swarm.end()
for s in sitls:
    s.stop()
print("swarm mission complete")
