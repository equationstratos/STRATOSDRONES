"""STRATOSDRONE client: djitellopy.Tello plus the STRATOS extensions."""
import socket

from djitellopy import Tello

_sim_enabled = False


def enable_sim() -> None:
    """Allow flying simulated drones bound to loopback IPs on this machine.

    djitellopy binds its client socket to the wildcard address on port 8889;
    simulated drones bind specific 127.0.0.X:8889 sockets on the same host.
    Linux only allows that coexistence when *both* sockets set SO_REUSEADDR,
    so this shims socket.bind to set it. Real drones over Wi-Fi don't need
    this (and are unaffected by it). Call once, before creating any Tello /
    StratosDrone object.
    """
    global _sim_enabled
    if _sim_enabled:
        return
    _sim_enabled = True
    orig_bind = socket.socket.bind

    def bind(self, addr):  # noqa: ANN001
        try:
            self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass
        return orig_bind(self, addr)

    socket.socket.bind = bind


class StratosDrone(Tello):
    """A Tello-compatible STRATOSDRONE with extension commands.

    Everything from djitellopy works unchanged (takeoff, move_*, go_xyz_speed,
    streamon/get_frame_read, TelloSwarm, ...). The methods below are STRATOS
    additions; they return normally or raise like other djitellopy commands.
    """

    def set_video_resolution_p(self, height: int) -> None:
        """Select the H.264 stream height: 720 (default) or 1080."""
        if height not in (720, 1080):
            raise ValueError("height must be 720 or 1080")
        self.send_control_command(f"video {height}")

    def set_led(self, r: int, g: int, b: int) -> None:
        """Set the RGB status LEDs (RMTT-compatible 'EXT led' command)."""
        self.send_expansion_command(f"led {r} {g} {b}")

    def get_param(self, name: str) -> float:
        """Read a flight-core parameter (e.g. 'pos_xy_kp')."""
        resp = self.send_read_command(f"param {name}?")
        return float(resp)

    def set_param(self, name: str, value: float) -> None:
        """Write a flight-core parameter. Use with care; see docs/bringup.md."""
        self.send_control_command(f"param {name} {value}")

    def firmware_version(self) -> str:
        return self.send_read_command("EXT version?")
