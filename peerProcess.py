# peerProcess.py
import os
import socket
import threading
import time
import math
from datetime import datetime
from pathlib import Path

from utils.handshake import pack_handshake, unpack_handshake, TOTAL_LEN as HS_LEN
from utils.bitfield import Bitfield
from utils.message import Message, make_bitfield
from utils.constants import MessageType

PROJECT_ROOT = Path(__file__).resolve().parent
COMMON_CFG = PROJECT_ROOT / "Common.cfg"
PEERINFO_CFG = PROJECT_ROOT / "PeerInfo.cfg"


def ts() -> str:
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def log_path(peer_id: int) -> Path:
    return PROJECT_ROOT / f"log_peer_{peer_id}.log"


def write_header(peer_id: int) -> None:
    p = log_path(peer_id)
    if not p.exists():
        with open(p, "w", encoding="utf8") as f:
            f.write(f"===== Log for Peer {peer_id} =====\n")


def log(peer_id: int, msg: str) -> None:
    with open(log_path(peer_id), "a", encoding="utf8") as f:
        f.write(f"[{ts()}] {msg}\n")


def parse_common() -> dict:
    cfg = {}
    if not COMMON_CFG.exists():
        return cfg
    with open(COMMON_CFG, "r", encoding="utf8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
            else:
                parts = line.split()
                if len(parts) >= 2:
                    cfg[parts[0]] = " ".join(parts[1:])
    return cfg


def parse_peerinfo() -> list[dict]:
    peers = []
    if not PEERINFO_CFG.exists():
        return peers
    with open(PEERINFO_CFG, "r", encoding="utf8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            pid_s, host, port_s, has_s = line.split()
            peers.append({
                "id": int(pid_s),
                "host": host,
                "port": int(port_s),
                "has": int(has_s) == 1
            })
    return peers


def num_pieces_from_common(common: dict) -> int:
    size = int(common.get("FileSize", "0"))
    piece = int(common.get("PieceSize", "32768"))
    return math.ceil(size / piece) if piece > 0 else 0


def ensure_peer_folder(peer_id: int, common: dict, has_file: bool) -> Path:
    folder = PROJECT_ROOT / f"peer_{peer_id}"
    folder.mkdir(exist_ok=True)
    if has_file:
        name = common.get("FileName", "TheFile.dat")
        path = folder / name
        if not path.exists():
            with open(path, "wb") as f:
                f.write(b"\0")
    return folder


class PeerServer(threading.Thread):
    def __init__(self, peer_id: int, host: str, port: int, my_bitfield: Bitfield):
        super().__init__(daemon=True)
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.my_bitfield = my_bitfield
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        while True:
            conn, addr = self.sock.accept()
            try:
                # receive handshake
                recv_buf = b""
                while len(recv_buf) < HS_LEN:
                    chunk = conn.recv(HS_LEN - len(recv_buf))
                    if not chunk:
                        raise ConnectionError("handshake closed")
                    recv_buf += chunk
                try:
                    other_id = unpack_handshake(recv_buf)
                    log(self.peer_id, f"Peer {self.peer_id} is connected from Peer {other_id}.")
                except Exception:
                    other_id = -1
                    log(self.peer_id, f"Peer {self.peer_id} is connected from Peer unknown.")

                # send handshake back
                conn.sendall(pack_handshake(self.peer_id))

                # send my bitfield
                bf_msg = make_bitfield(self.my_bitfield.to_bytes()).encode()
                conn.sendall(bf_msg)

                # optional quick read of their bitfield
                conn.settimeout(0.5)
                try:
                    hdr = conn.recv(4)
                    if hdr and len(hdr) == 4:
                        length = int.from_bytes(hdr, "big")
                        frame = hdr + conn.recv(length)
                        _msg = Message.decode(frame)
                        # handle later if needed
                except Exception:
                    pass
            finally:
                conn.close()


def connect_to(peer_id: int, me_id: int, host: str, port: int, my_bitfield: Bitfield) -> bool:
    attempts = 10
    for _ in range(attempts):
        try:
            s = socket.create_connection((host, port), timeout=1.5)

            # send handshake
            s.sendall(pack_handshake(me_id))

            # receive handshake back
            recv_buf = b""
            while len(recv_buf) < HS_LEN:
                chunk = s.recv(HS_LEN - len(recv_buf))
                if not chunk:
                    raise ConnectionError("handshake closed")
                recv_buf += chunk
            # ok to log now that handshake completed
            log(me_id, f"Peer {me_id} makes a connection to Peer {peer_id}.")

            # receive their bitfield if sent first
            s.settimeout(0.5)
            try:
                hdr = s.recv(4)
                if hdr and len(hdr) == 4:
                    length = int.from_bytes(hdr, "big")
                    frame = hdr + s.recv(length)
                    _msg = Message.decode(frame)
                    # handle later if needed
            except Exception:
                pass

            # send my bitfield
            s.sendall(make_bitfield(my_bitfield.to_bytes()).encode())

            s.close()
            return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CNT4007 peer process")
    parser.add_argument("peer_id", type=int, help="peer id from PeerInfo.cfg")
    args = parser.parse_args()

    me_id = args.peer_id
    write_header(me_id)

    common = parse_common()
    peers = parse_peerinfo()
    me = None
    for p in peers:
        if p["id"] == me_id:
            me = p
            break
    if me is None:
        raise SystemExit(f"peer id {me_id} not found in PeerInfo.cfg")

    ensure_peer_folder(me_id, common, me["has"])

    num_pieces = num_pieces_from_common(common)
    my_bf = Bitfield(num_pieces)
    if me["has"]:
        for i in range(num_pieces):
            my_bf.set_have(i)

    server = PeerServer(me_id, me["host"], me["port"], my_bf)
    server.start()

    for p in peers:
        if p["id"] == me_id:
            break
        connect_to(p["id"], me_id, p["host"], p["port"], my_bf)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
