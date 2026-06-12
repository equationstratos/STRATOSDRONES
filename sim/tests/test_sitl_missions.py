"""Headless mission tests against the SITL runner, via unmodified djitellopy.

These are the CI gate for protocol + flight behavior. Run from repo root:
    cd sim && cmake -B build && cmake --build build
    pytest sim/tests -v
"""
import logging
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sdk" / "python"))

from djitellopy import Tello, TelloSwarm  # noqa: E402
from stratospy import StratosDrone, enable_sim, spawn_sitl  # noqa: E402

Tello.LOGGER.setLevel(logging.WARNING)
enable_sim()

RTF = 4.0  # sim faster than real time to keep CI snappy


@pytest.fixture
def sitl():
    inst = spawn_sitl(index=2, rtf=RTF)
    yield inst
    inst.stop()


@pytest.fixture
def sitl_swarm():
    insts = [spawn_sitl(index=i, rtf=RTF) for i in (2, 3, 4)]
    yield insts
    for i in insts:
        i.stop()


def _connect(host: str) -> StratosDrone:
    d = StratosDrone(host=host)
    d.RESPONSE_TIMEOUT = 20
    d.connect()
    return d


def test_connect_and_telemetry(sitl):
    d = _connect(sitl.ip)
    assert 50 <= d.get_battery() <= 100
    assert d.query_sdk_version() == "20"
    assert d.query_serial_number().startswith("STRATOSSITL")
    assert d.get_height() <= 3  # on ground (cm; small estimator noise is fine)
    d.end()


def test_full_mission(sitl):
    d = _connect(sitl.ip)
    d.takeoff()
    time.sleep(2.0 / RTF)
    h = d.get_height()
    assert 55 <= h <= 105, f"hover height {h} cm out of band"

    d.go_xyz_speed(100, 0, 0, 50)
    d.rotate_clockwise(90)
    yaw = d.get_yaw()
    assert 70 <= yaw <= 110, f"yaw {yaw} after cw 90"

    d.move_up(50)
    time.sleep(1.0 / RTF)
    assert d.get_height() >= 100

    d.land()
    assert d.get_height() <= 12
    d.end()


def test_extensions(sitl):
    d = _connect(sitl.ip)
    assert d.firmware_version().startswith("stratos")
    d.set_led(255, 0, 64)
    kp = d.get_param("pos_xy_kp")
    assert kp > 0
    d.set_param("pos_xy_kp", kp)  # write back unchanged
    d.set_video_resolution_p(1080)
    d.set_video_resolution_p(720)
    d.end()


def test_error_paths(sitl):
    d = _connect(sitl.ip)
    with pytest.raises(Exception):
        d.go_xyz_speed(50, 0, 0, 50)  # not flying -> error
    with pytest.raises(Exception):
        d.send_control_command("speed 999")
    d.end()


def test_swarm_three_drones(sitl_swarm):
    swarm = TelloSwarm.fromIps([s.ip for s in sitl_swarm])
    for t in swarm.tellos:
        t.RESPONSE_TIMEOUT = 25
    swarm.connect()
    swarm.takeoff()
    swarm.parallel(lambda i, t: t.go_xyz_speed(50 + 30 * i, (i - 1) * 60, 0, 60))
    heights = [t.get_height() for t in swarm.tellos]
    assert all(55 <= h <= 110 for h in heights), heights
    swarm.land()
    swarm.end()
