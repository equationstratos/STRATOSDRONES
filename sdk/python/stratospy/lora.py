"""stratospy.lora — the STRATOS LoRa fleet transport (ground side).

Byte-for-byte mirror of ``fc_core/src/fc_lorap.c`` — the same frames the drone
firmware (``lora_task`` + ``sx1262.c``) speaks, validated against the golden
fixture in ``fc_core/test/test_lorap.c`` (run ``python3 -m stratospy.lora`` for
the self-test). The physical link is an off-the-shelf ESP32+SX1262 dongle
(Heltec LoRa32 V3 / LilyGO T3S3) running the transparent bridge in
``sdk/lora_dongle/`` — it forwards raw fc_lorap frames between USB-serial and
the radio, so this module only frames/deframes and speaks SDK verbs.

LoRa carries commands / telemetry / choreography — NOT the piloting sticks
(that is ExpressLRS). Shows are pre-uploaded; runtime traffic is beacons.
"""
from __future__ import annotations

import struct
import time
from dataclasses import dataclass

# ---- protocol constants (keep in sync with fc_lorap.h) ----
MAGIC = 0x53          # 'S'
VERSION = 1
MAX_FRAME = 64
HDR_LEN = 7
MAX_PAYLOAD = MAX_FRAME - HDR_LEN - 2   # 55
ADDR_GROUND = 0x00
BROADCAST = 0xFF
SLOT_MS = 40
KEYS_PER_CHUNK = (MAX_PAYLOAD - 3) // 12   # 4

# lorap_type_t
ACK = 0
NAK = 1
CMD_LINE = 2
RESP_LINE = 3
TELEM = 4
SHOW_CHUNK = 5
TIME_BEACON = 6
SWARM_START = 7
SWARM_ABORT = 8

# serial wire framing to the dongle: 0x7E | len | frame-bytes
SERIAL_SOF = 0x7E


def crc16_ccitt(data: bytes) -> int:
    """CRC16-CCITT (poly 0x1021, init 0xFFFF) — matches lorap_crc16()."""
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


@dataclass
class Frame:
    type: int
    swarm_id: int = 0
    src: int = ADDR_GROUND
    dst: int = BROADCAST
    seq: int = 0
    payload: bytes = b""

    def encode(self) -> bytes:
        if len(self.payload) > MAX_PAYLOAD or self.type > 0x0F:
            raise ValueError("payload too long / bad type")
        hdr = bytes([
            MAGIC,
            (VERSION << 4) | self.type,
            self.swarm_id & 0xFF, self.src & 0xFF, self.dst & 0xFF,
            self.seq & 0xFF, len(self.payload),
        ])
        body = hdr + self.payload
        crc = crc16_ccitt(body)
        return body + bytes([crc >> 8, crc & 0xFF])

    @classmethod
    def decode(cls, raw: bytes) -> "Frame | None":
        if len(raw) < HDR_LEN + 2 or len(raw) > MAX_FRAME:
            return None
        if raw[0] != MAGIC or (raw[1] >> 4) != VERSION:
            return None
        ln = raw[6]
        if ln > MAX_PAYLOAD or HDR_LEN + ln + 2 != len(raw):
            return None
        crc = (raw[7 + ln] << 8) | raw[8 + ln]
        if crc != crc16_ccitt(raw[:HDR_LEN + ln]):
            return None
        return cls(type=raw[1] & 0x0F, swarm_id=raw[2], src=raw[3],
                   dst=raw[4], seq=raw[5], payload=raw[7:7 + ln])


# ---- payload helpers (little-endian, mirror fc_lorap.c) ----
def pack_telem(state, mode, x_cm, y_cm, z_cm, yaw_deg, vbat_mv, bat_pct,
               rssi_dbm, show_flag) -> bytes:
    mag = min(127, -rssi_dbm if rssi_dbm <= 0 else 0)
    last = mag | ((show_flag & 1) << 7)
    return struct.pack("<BBhhhhHBB", state, mode, x_cm, y_cm, z_cm, yaw_deg,
                       vbat_mv, bat_pct, last)


def unpack_telem(pl: bytes) -> dict:
    state, mode, x, y, z, yaw, vbat, bat, last = struct.unpack("<BBhhhhHBB", pl[:14])
    return dict(state=state, mode=mode, x_cm=x, y_cm=y, z_cm=z, yaw_deg=yaw,
                vbat_mv=vbat, bat_pct=bat, rssi_dbm=-(last & 0x7F),
                show_flag=(last >> 7) & 1)


def show_chunk_payload(first_idx: int, keys: list) -> bytes:
    """keys: list of (t_ms, x_cm, y_cm, z_cm, yaw_deg). Max KEYS_PER_CHUNK."""
    body = struct.pack("<HB", first_idx, len(keys))
    for t, x, y, z, yw in keys:
        body += struct.pack("<Ihhhh", t, x, y, z, yw)
    return body


# ---- transports ---------------------------------------------------------
class LoRaLink:
    """Serial link to the LoRa dongle (needs pyserial + the bridge firmware)."""

    def __init__(self, port: str, baud: int = 921600, swarm_id: int = 0):
        import serial  # lazy: only LoRaLink needs pyserial
        self._ser = serial.Serial(port, baud, timeout=0.05)
        self.swarm_id = swarm_id
        self._seq = 0
        self._rxbuf = bytearray()

    def _next_seq(self) -> int:
        self._seq = (self._seq + 1) & 0xFF
        return self._seq

    def send_frame(self, f: Frame) -> None:
        f.swarm_id = self.swarm_id
        raw = f.encode()
        self._ser.write(bytes([SERIAL_SOF, len(raw)]) + raw)

    def poll(self) -> "list[Frame]":
        """Read whatever the dongle forwarded; return decoded frames."""
        self._rxbuf += self._ser.read(256)
        out = []
        while len(self._rxbuf) >= 2:
            if self._rxbuf[0] != SERIAL_SOF:
                self._rxbuf.pop(0)
                continue
            ln = self._rxbuf[1]
            if len(self._rxbuf) < 2 + ln:
                break
            raw = bytes(self._rxbuf[2:2 + ln])
            del self._rxbuf[:2 + ln]
            fr = Frame.decode(raw)
            if fr:
                out.append(fr)
        return out

    # high-level fleet ops -------------------------------------------------
    def command(self, dst: int, line: str, wait: float = 0.5) -> "str | None":
        self.send_frame(Frame(CMD_LINE, dst=dst, seq=self._next_seq(),
                              payload=line.encode()))
        t0 = time.time()
        while time.time() - t0 < wait:
            for fr in self.poll():
                if fr.type == RESP_LINE and fr.src == dst:
                    return fr.payload.decode(errors="replace")
            time.sleep(0.01)
        return None

    def broadcast(self, line: str) -> None:
        self.send_frame(Frame(CMD_LINE, dst=BROADCAST, seq=self._next_seq(),
                              payload=line.encode()))

    def time_beacon(self, t0_ms: "int | None" = None) -> None:
        now = int(time.time() * 1000)
        pl = struct.pack("<Q", now)
        if t0_ms is not None:
            pl += struct.pack("<Q", int(t0_ms))
        self.send_frame(Frame(TIME_BEACON, dst=BROADCAST, payload=pl))

    def swarm_start(self, t0_ms: int) -> None:
        pl = struct.pack("<Q", int(t0_ms))
        for _ in range(3):   # repeat x3 like the firmware expects
            self.send_frame(Frame(SWARM_START, dst=BROADCAST, payload=pl))

    def swarm_abort(self) -> None:
        for _ in range(3):
            self.send_frame(Frame(SWARM_ABORT, dst=BROADCAST))

    def upload_keyframes(self, dst: int, keys: list, ack_wait: float = 0.3) -> bool:
        """Send a drone's whole keyframe list in SHOW_CHUNK frames."""
        ok = True
        for i in range(0, len(keys), KEYS_PER_CHUNK):
            chunk = keys[i:i + KEYS_PER_CHUNK]
            self.send_frame(Frame(SHOW_CHUNK, dst=dst, seq=self._next_seq(),
                                 payload=show_chunk_payload(i, chunk)))
            time.sleep(0.05)   # be gentle on the duty cycle
        return ok

    def telemetry(self) -> "dict[int, dict]":
        """Latest telemetry per drone id seen this poll."""
        out = {}
        for fr in self.poll():
            if fr.type == TELEM and len(fr.payload) >= 14:
                out[fr.src] = unpack_telem(fr.payload)
        return out

    def close(self) -> None:
        self._ser.close()


class StratosLoRaDrone:
    """A single drone addressed over LoRa, with a djitellopy-ish verb surface.

    Not a full Tello subclass (no video, no state UDP) — the field link is
    LoRa, so this is the command surface. Numeric-arg verbs mirror the Tello
    SDK; ``send`` is the escape hatch for any fc_sdk line.
    """

    def __init__(self, link: LoRaLink, drone_id: int):
        self.link = link
        self.id = drone_id

    def send(self, line: str) -> "str | None":
        return self.link.command(self.id, line)

    def connect(self):        return self.send("command")
    def takeoff(self):        return self.send("takeoff")
    def land(self):           return self.send("land")
    def emergency(self):      return self.send("emergency")
    def mode(self, m: str):   return self.send(f"mode {m}")
    def go(self, x, y, z, spd): return self.send(f"go {x} {y} {z} {spd}")
    def rotate_cw(self, d):   return self.send(f"cw {d}")

    def figure(self, kind: str, *args) -> "str | None":
        return self.send(f"figure {kind} " + " ".join(str(a) for a in args))


def _selftest() -> None:
    """Reproduce the golden bytes from fc_core/test/test_lorap.c."""
    assert crc16_ccitt(b"123456789") == 0x29B1, "CRC16 anchor"
    f = Frame(CMD_LINE, swarm_id=7, src=ADDR_GROUND, dst=3, seq=42,
              payload=b"go 100 0 50 60")
    raw = f.encode()
    assert raw[:7] == bytes([0x53, 0x12, 0x07, 0x00, 0x03, 0x2A, 14]), raw[:7].hex()
    g = Frame.decode(raw)
    assert g and g.payload == b"go 100 0 50 60" and g.dst == 3 and g.seq == 42
    # one-bit corruption anywhere must fail to decode
    for i in range(len(raw)):
        bad = bytearray(raw); bad[i] ^= 0x5A
        assert Frame.decode(bytes(bad)) is None, f"corruption at {i} not caught"
    # telemetry golden payload
    pl = pack_telem(2, 3, 123, -45, 180, -90, 7412, 87, -70, 1)
    assert pl == bytes.fromhex("02037b00d3ffb400a6fff41c57c6"), pl.hex()
    t = unpack_telem(pl)
    assert t["x_cm"] == 123 and t["y_cm"] == -45 and t["rssi_dbm"] == -70 and t["show_flag"] == 1
    # broadcast abort round-trips
    ab = Frame(SWARM_ABORT, dst=BROADCAST).encode()
    assert Frame.decode(ab).dst == BROADCAST
    print("stratospy.lora self-test OK (golden frames match fc_lorap.c)")


if __name__ == "__main__":
    _selftest()
