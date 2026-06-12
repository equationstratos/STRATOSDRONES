"""Helpers to run local SITL drone instances (no Gazebo needed)."""
import os
import shutil
import signal
import socket
import subprocess
import time
from dataclasses import dataclass


def wait_drone_ready(ip: str, timeout: float = 30.0) -> bool:
    """Probe <ip>:8889 with 'command' until the drone answers 'ok'.

    Use this after starting a simulator (SITL or Gazebo) and before creating
    djitellopy objects: it absorbs the simulator's cold-start latency on a
    throwaway socket, so djitellopy's first command gets a fresh, fast reply
    and its response queue never goes out of sync with late replies.
    """
    deadline = time.monotonic() + timeout
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.5)
    try:
        while time.monotonic() < deadline:
            try:
                s.sendto(b"command", (ip, 8889))
                data, _ = s.recvfrom(64)
                if data.strip() == b"ok":
                    return True
            except socket.timeout:
                continue
    finally:
        s.close()
    return False


def _default_binary() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.normpath(os.path.join(here, "..", "..", ".."))
    cand = os.path.join(repo, "sim", "build", "sitl_runner")
    if os.path.exists(cand):
        return cand
    found = shutil.which("sitl_runner")
    if found:
        return found
    raise FileNotFoundError(
        "sitl_runner not built. Run: cd sim && cmake -B build && cmake --build build"
    )


@dataclass
class SitlInstance:
    ip: str
    proc: subprocess.Popen

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def spawn_sitl(index: int = 2, rtf: float = 1.0, seed: int = 0,
               binary: str | None = None) -> SitlInstance:
    """Start one SITL drone on 127.0.0.<index>:8889 and return its handle.

    For a swarm, call with index 2, 3, 4, ... and pass the IPs to
    djitellopy's TelloSwarm / StratosDrone(host=...).
    """
    ip = f"127.0.0.{index}"
    binary = binary or _default_binary()
    proc = subprocess.Popen(
        [binary, "--ip", ip, "--rtf", str(rtf), "--seed", str(seed or index * 7)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(0.3)
    if proc.poll() is not None:
        raise RuntimeError(f"sitl_runner exited immediately for {ip}")
    return SitlInstance(ip=ip, proc=proc)
