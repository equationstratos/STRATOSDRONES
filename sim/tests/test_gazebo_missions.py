"""Headless Gazebo mission tests (gz-sim Harmonic) via unmodified djitellopy.

Skipped automatically when gz or the plugin build is unavailable; the SITL
tests in test_sitl_missions.py cover the same protocol/flight assertions
without Gazebo. CI runs both.

Env overrides:
    GZ_BIN       path to the gz CLI            (default: gz, or /opt/gzenv/bin/gz)
    GZ_LIB_PATH  LD_LIBRARY_PATH for gz        (default: /opt/gzenv/lib if present)
"""
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SIM = REPO / "sim"
sys.path.insert(0, str(REPO / "sdk" / "python"))

from djitellopy import Tello, TelloSwarm  # noqa: E402
from stratospy import enable_sim, wait_drone_ready  # noqa: E402

Tello.LOGGER.setLevel(logging.WARNING)
enable_sim()

GZ_BIN = os.environ.get(
    "GZ_BIN", "/opt/gzenv/bin/gz" if os.path.exists("/opt/gzenv/bin/gz") else shutil.which("gz"))
PLUGIN = SIM / "build" / "libStratosFcSystem.so"

pytestmark = pytest.mark.skipif(
    not GZ_BIN or not PLUGIN.exists(),
    reason="gz or StratosFcSystem plugin not available",
)

# world RTF (keep in sync with worlds/*.sdf); wall sleeps are scaled by it
RTF = 4.0


def _gz_env() -> dict:
    env = os.environ.copy()
    env["GZ_SIM_SYSTEM_PLUGIN_PATH"] = str(SIM / "build")
    env["GZ_SIM_RESOURCE_PATH"] = str(SIM / "models")
    lib = os.environ.get("GZ_LIB_PATH",
                         "/opt/gzenv/lib" if os.path.exists("/opt/gzenv/lib") else "")
    if lib:
        env["LD_LIBRARY_PATH"] = lib + ":" + env.get("LD_LIBRARY_PATH", "")
    return env


def _launch_world(world: str, ips: list[str]):
    """Start a gz server in its own process group; wait until drones answer."""
    proc = subprocess.Popen(
        [GZ_BIN, "sim", "-s", "-r", str(SIM / "worlds" / world)],
        env=_gz_env(), start_new_session=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for ip in ips:
            assert wait_drone_ready(ip, 60), f"drone {ip} never became ready"
    except Exception:
        os.killpg(proc.pid, signal.SIGKILL)
        raise
    return proc


def _stop(proc) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        pass


@pytest.fixture
def gz_single():
    proc = _launch_world("hover_test.sdf", ["127.0.0.2"])
    yield "127.0.0.2"
    _stop(proc)


@pytest.fixture
def gz_swarm():
    ips = ["127.0.0.2", "127.0.0.3", "127.0.0.4"]
    proc = _launch_world("swarm_3.sdf", ips)
    yield ips
    _stop(proc)


def test_gazebo_full_mission(gz_single):
    d = Tello(host=gz_single)
    d.RESPONSE_TIMEOUT = 30
    d.connect()
    assert 50 <= d.get_battery() <= 100
    d.takeoff()
    time.sleep(2.0 / RTF)
    h = d.get_height()
    assert 55 <= h <= 105, f"hover height {h} cm"
    d.go_xyz_speed(100, 0, 0, 50)
    d.rotate_clockwise(90)
    yaw = d.get_yaw()
    assert 70 <= yaw <= 110, f"yaw {yaw}"
    d.land()
    assert d.get_height() <= 12
    d.end()


def test_gazebo_swarm(gz_swarm):
    swarm = TelloSwarm.fromIps(gz_swarm)
    for t in swarm.tellos:
        t.RESPONSE_TIMEOUT = 40
    swarm.connect()
    swarm.takeoff()
    swarm.parallel(lambda i, t: t.go_xyz_speed(50 + 30 * i, (i - 1) * 60, 0, 60))
    heights = [t.get_height() for t in swarm.tellos]
    assert all(55 <= h <= 115 for h in heights), heights
    swarm.land()
    swarm.end()
