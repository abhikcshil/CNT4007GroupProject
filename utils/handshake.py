# utils/handshake.py
import struct

HEADER = b"P2PFILESHARINGPROJ"   # 18 bytes
PAD = b"\x00" * 10               # 10 bytes
TOTAL_LEN = 18 + 10 + 4          # 32 bytes

def pack_handshake(peer_id: int) -> bytes:
    return HEADER + PAD + struct.pack("!I", int(peer_id))

def unpack_handshake(buf: bytes) -> int:
    if len(buf) != TOTAL_LEN:
        raise ValueError("bad handshake length")
    if buf[:18] != HEADER:
        raise ValueError("bad handshake header")
    peer_id, = struct.unpack("!I", buf[28:32])
    return peer_id
