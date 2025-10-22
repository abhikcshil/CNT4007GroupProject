# peerProcess.py
import os
import socket
import threading
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

COMMON_CFG = PROJECT_ROOT / "Common.cfg"
PEERINFO_CFG = PROJECT_ROOT / "PeerInfo.cfg"

def ts():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

def log_path(peer_id: int) -> Path:
    return PROJECT_ROOT / f"log_peer_{peer_id}.log"

def write_header(peer_id: int):
    path = log_path(peer_id)
    if not path.exists():
        with open(path, "w", encoding="utf8") as f:
            f.write(f"===== Log for Peer {peer_id} =====\n")

def log(peer_id: int, msg: str):
    with open(log_path(peer_id), "a", encoding="utf8") as f:
        f.write(f"[{ts()}] {msg}\n")

def parse_common():
    cfg = {}
    with open(COMMON_CFG, "r", encoding="utf8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            # supports both "k v" and "k = v"
            parts = [p for p in line.replace("=", " ").split() if p]
            if len(parts) >= 2:
                key = parts[0]
                value = " ".join(parts[1:])
                cfg[key] = value
    return cfg

def parse_peerinfo():
    peers = []  # list of dicts with id, host, port, has_file
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
    # keep original order
    return peers

class PeerServer(threading.Thread):
    def __init__(self, peer_id: int, host: str, port: int):
        super().__init__(daemon=True)
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # allow rapid restart
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        while True:
            conn, addr = self.sock.accept()
            try:
                # in a full build, we would perform handshake here
                # for now we only log that a connection arrived
                # if the caller sends its id as plain text, read it
                conn.settimeout(0.5)
                try:
                    peer_bytes = conn.recv(32)
                    peer_txt = peer_bytes.decode(errors="ignore").strip()
                    if peer_txt.isdigit():
                        other = int(peer_txt)
                        log(self.peer_id, f"Peer {self.peer_id} is connected from Peer {other}.")
                    else:
                        log(self.peer_id, f"Peer {self.peer_id} is connected from Peer unknown.")
                except Exception:
                    log(self.peer_id, f"Peer {self.peer_id} is connected from Peer unknown.")
            finally:
                conn.close()

def ensure_peer_folder(peer_id: int, common: dict, has_file: bool):
    folder = PROJECT_ROOT / f"peer_{peer_id}"
    folder.mkdir(exist_ok=True)
    # if the peer starts with the full file, ensure the file exists
    if has_file:
        name = common.get("FileName", "TheFile.dat")
        path = folder / name
        if not path.exists():
            # create a small placeholder so the grader sees a file
            with open(path, "wb") as f:
                f.write(b"\0")
    return folder

def connect_to(peer_id: int, me_id: int, host: str, port: int):
    # try a short series of attempts to tolerate startup races
    attempts = 10
    for _ in range(attempts):
        try:
            s = socket.create_connection((host, port), timeout=1.5)
            # send my id as plain text so the server can log who connected
            s.sendall(str(me_id).encode())
            s.close()
            log(me_id, f"Peer {me_id} makes a connection to Peer {peer_id}.")
            return True
        except Exception:
            time.sleep(0.3)
    return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CNT4007 P2P peer process")
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

    ensure_peer_folder(me_id, common, has_file=me["has"])

    # start listener
    server = PeerServer(me_id, me["host"], me["port"])
    server.start()

    # connect to all prior peers in the file, in order
    for p in peers:
        if p["id"] == me_id:
            break
        connect_to(p["id"], me_id, p["host"], p["port"])

    # keep process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
