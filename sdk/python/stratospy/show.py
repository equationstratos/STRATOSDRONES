"""stratospy.show — drone-show choreography: author, safety-check, upload.

A show is a set of per-drone keyframe tracks in each drone's local frame
(origin = its arm point, x forward, cm; yaw clockwise-positive — the same
frame ``go``/``fc_show`` use). Author it in JSON or with the figure DSL,
check fleet separation + speed, then upload:

  * to the **Gazebo sim** (or SITL): plain SDK verbs over UDP — ``show key``,
    ``show start`` — so the exact choreography previews before any hardware;
  * to the **real fleet**: SHOW_CHUNK frames over LoRa (``stratospy.lora``),
    then one broadcast ``SWARM_START`` at a common T0.

The keyframe wire format and verbs are identical on both paths — that is the
whole point of the transport-free ``fc_sdk`` layer.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

Keyframe = tuple  # (t_ms:int, x_cm:int, y_cm:int, z_cm:int, yaw_deg:int)


@dataclass
class Track:
    drone_id: int
    keys: list = field(default_factory=list)   # list[Keyframe], t strictly increasing

    def key(self, t_ms, x_cm, y_cm, z_cm, yaw_deg=0) -> "Track":
        if self.keys and t_ms <= self.keys[-1][0]:
            raise ValueError(f"drone {self.drone_id}: t must increase ({t_ms})")
        self.keys.append((int(t_ms), int(x_cm), int(y_cm), int(z_cm), int(yaw_deg)))
        return self

    def sample(self, t_ms: float) -> "tuple[float, float, float]":
        """Cosine-eased position at t_ms (matches fc_show.c interpolation)."""
        ks = self.keys
        if not ks:
            return (0.0, 0.0, 0.0)
        if t_ms <= ks[0][0]:
            return (ks[0][1], ks[0][2], ks[0][3])
        if t_ms >= ks[-1][0]:
            return (ks[-1][1], ks[-1][2], ks[-1][3])
        i = 0
        while i + 1 < len(ks) and ks[i + 1][0] < t_ms:
            i += 1
        a, b = ks[i], ks[i + 1]
        u = (t_ms - a[0]) / (b[0] - a[0])
        e = 0.5 - 0.5 * math.cos(math.pi * u)
        return tuple(a[1 + j] + (b[1 + j] - a[1 + j]) * e for j in range(3))


class Show:
    def __init__(self, name: str = "show"):
        self.name = name
        self.tracks: dict[int, Track] = {}

    def track(self, drone_id: int) -> Track:
        return self.tracks.setdefault(drone_id, Track(drone_id))

    # ---- authoring: JSON ----
    @classmethod
    def from_json(cls, path: str) -> "Show":
        with open(path) as f:
            data = json.load(f)
        show = cls(data.get("name", "show"))
        for d in data["drones"]:
            tr = show.track(int(d["id"]))
            for k in d["keys"]:
                tr.key(k["t"], k["x"], k["y"], k["z"], k.get("yaw", 0))
        return show

    def to_json(self, path: str) -> None:
        data = {"name": self.name, "drones": [
            {"id": t.drone_id, "keys": [
                {"t": k[0], "x": k[1], "y": k[2], "z": k[3], "yaw": k[4]}
                for k in t.keys]}
            for t in self.tracks.values()]}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ---- authoring: formation helpers (fill many drones at once) ----
    def formation_line(self, t_ms, ids, z_cm, spacing_cm, yaw=0) -> "Show":
        n = len(ids)
        for i, did in enumerate(ids):
            y = int((i - (n - 1) / 2) * spacing_cm)
            self.track(did).key(t_ms, 0, y, z_cm, yaw)
        return self

    def formation_circle(self, t_ms, ids, z_cm, radius_cm, yaw=0) -> "Show":
        n = len(ids)
        for i, did in enumerate(ids):
            a = 2 * math.pi * i / n
            self.track(did).key(t_ms, int(radius_cm * math.cos(a)),
                                int(radius_cm * math.sin(a)), z_cm, yaw)
        return self

    # ---- safety ----
    def check(self, min_sep_cm: float = 60.0, vmax_cms: float = 150.0,
              dt_ms: int = 100) -> "list[str]":
        """Sample every track over the show and flag close passes / overspeed."""
        problems = []
        end = max((t.keys[-1][0] for t in self.tracks.values() if t.keys), default=0)
        ids = list(self.tracks)
        # speed
        for tr in self.tracks.values():
            prev = None
            for t in range(0, end + 1, dt_ms):
                p = tr.sample(t)
                if prev is not None:
                    v = math.dist(p, prev) / (dt_ms / 1000.0)
                    if v > vmax_cms:
                        problems.append(
                            f"drone {tr.drone_id}: {v:.0f} cm/s > vmax at t={t}ms")
                        break
                prev = p
        # separation
        for t in range(0, end + 1, dt_ms):
            pos = {d: self.tracks[d].sample(t) for d in ids}
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    d = math.dist(pos[ids[i]], pos[ids[j]])
                    if d < min_sep_cm:
                        problems.append(
                            f"t={t}ms: drones {ids[i]}&{ids[j]} {d:.0f} cm "
                            f"< {min_sep_cm:.0f} cm")
                        break
                else:
                    continue
                break
        return problems

    # ---- upload ----
    def upload_sim(self, drones: dict, arm_mode: bool = True) -> None:
        """Send each track to a sim/SITL drone via SDK verbs (UDP).

        drones: {drone_id: object with .send_control_command(str)} — a
        StratosDrone (djitellopy) or any client exposing that method.
        """
        for did, tr in self.tracks.items():
            dv = drones[did]
            send = dv.send_control_command
            if arm_mode:
                send("mode swarm")
            send("show clear")
            for (t, x, y, z, yw) in tr.keys:
                send(f"show key {t} {x} {y} {z} {yw}")

    def start_sim(self, drones: dict, t0_ms: int = 0) -> None:
        for did in self.tracks:
            drones[did].send_control_command(f"show start {t0_ms}")

    def upload_lora(self, link, t0_delay_ms: int = 3000) -> None:
        """Upload every track over LoRa then broadcast a synced start.

        link: a stratospy.lora.LoRaLink.
        """
        for did, tr in self.tracks.items():
            link.command(did, "mode swarm")
            link.command(did, "show clear")
            link.upload_keyframes(did, tr.keys)
        import time
        t0 = int(time.time() * 1000) + t0_delay_ms
        link.time_beacon(t0)
        link.swarm_start(t0)


def _selftest() -> None:
    s = Show("triangle")
    s.formation_line(0, [1, 2, 3], z_cm=100, spacing_cm=100)
    s.formation_circle(4000, [1, 2, 3], z_cm=120, radius_cm=100)
    for did in (1, 2, 3):
        s.track(did).key(8000, 0, 0, 100)   # regroup at centre column
    probs = s.check(min_sep_cm=40)
    # the regroup at t=8000 deliberately converges; expect a separation flag
    assert any("40 cm" in p or "drones" in p for p in probs), probs
    # a well-spread hold has no problems
    s2 = Show()
    s2.formation_circle(0, [1, 2, 3, 4], z_cm=100, radius_cm=200)
    s2.formation_circle(5000, [1, 2, 3, 4], z_cm=100, radius_cm=200)
    assert s2.check(min_sep_cm=60) == [], s2.check(min_sep_cm=60)
    # sample eases monotonically along a straight leg
    tr = Track(1)
    tr.key(0, 0, 0, 100).key(2000, 200, 0, 100)
    assert tr.sample(0)[0] == 0 and abs(tr.sample(1000)[0] - 100) < 1
    print("stratospy.show self-test OK")


if __name__ == "__main__":
    _selftest()
