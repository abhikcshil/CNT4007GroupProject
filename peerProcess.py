# peerProcess.py
import os
import socket
import threading
import time
import math
import random
from pathlib import Path
from typing import Dict

from utils import logger
from utils.handshake import pack_handshake, unpack_handshake, TOTAL_LEN as HS_LEN
from utils.bitfield import Bitfield
from utils.message import make_bitfield
from utils.logger import Logger
from utils.file_manager import split_file, write_piece, merge_pieces, cleanup_pieces
from peers.connection import PeerConnection

PROJECT_ROOT = Path(__file__).resolve().parent
COMMON_CFG = PROJECT_ROOT / "Common.cfg"
PEERINFO_CFG = PROJECT_ROOT / "PeerInfo.cfg"


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
            peers.append(
                {
                    "id": int(pid_s),
                    "host": host,
                    "port": int(port_s),
                    "has": int(has_s) == 1,
                }
            )
    return peers


def num_pieces_from_common(common: dict) -> int:
    size = int(common.get("FileSize", "0"))
    piece = int(common.get("PieceSize", "32768"))
    return math.ceil(size / piece) if piece > 0 else 0


def ensure_peer_folder(peer_id: int) -> Path:
    folder = PROJECT_ROOT / f"peer_{peer_id}"
    folder.mkdir(exist_ok=True)
    return folder


class PeerServer(threading.Thread):
    def __init__(
        self,
        peer_id: int,
        host: str,
        port: int,
        my_bitfield: Bitfield,
        num_pieces: int,
        piece_size: int,
        file_name: str,
        logger: Logger,
        neighbors: Dict[int, PeerConnection],
        neighbors_lock: threading.Lock,
    ):
        super().__init__(daemon=True)
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.my_bitfield = my_bitfield
        self.num_pieces = num_pieces
        self.piece_size = piece_size
        self.file_name = file_name
        self.logger = logger
        self.neighbors = neighbors
        self.neighbors_lock = neighbors_lock
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        while True:
            conn, addr = self.sock.accept()
            try:
                recv_buf = b""
                while len(recv_buf) < HS_LEN:
                    chunk = conn.recv(HS_LEN - len(recv_buf))
                    if not chunk:
                        raise ConnectionError("handshake closed")
                    recv_buf += chunk
                try:
                    other_id = unpack_handshake(recv_buf)
                    self.logger.connection_received(self.peer_id, other_id)
                    self.logger.received_handshake(self.peer_id, other_id)
                except Exception:
                    other_id = -1

                if other_id < 0:
                    conn.close()
                    continue

                conn.sendall(pack_handshake(self.peer_id))
                self.logger.sent_handshake(self.peer_id, other_id)

                bf_msg = make_bitfield(self.my_bitfield.to_bytes()).encode()
                conn.sendall(bf_msg)
                self.logger.sent_bitfield(self.peer_id, other_id)
                
                pc = PeerConnection(
                    me_id=self.peer_id,
                    remote_id=other_id,
                    sock=conn,
                    my_bitfield=self.my_bitfield,
                    num_pieces=self.num_pieces,
                    piece_size=self.piece_size,
                    file_name=self.file_name,
                    logger=self.logger,
                )
                with self.neighbors_lock:
                    self.neighbors[other_id] = pc
                pc.start()

            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass


def connect_to(
    peer_id: int,
    me_id: int,
    host: str,
    port: int,
    my_bitfield: Bitfield,
    num_pieces: int,
    piece_size: int,
    file_name: str,
    logger: Logger,
    neighbors: Dict[int, PeerConnection],
    neighbors_lock: threading.Lock,
) -> bool:
    attempts = 10
    for _ in range(attempts):
        try:
            s = socket.create_connection((host, port), timeout=1.5)

            s.sendall(pack_handshake(me_id))
            logger.sent_handshake(me_id, peer_id)

            recv_buf = b""
            while len(recv_buf) < HS_LEN:
                chunk = s.recv(HS_LEN - len(recv_buf))
                if not chunk:
                    raise ConnectionError("handshake closed")
                recv_buf += chunk

            logger.connection_made(me_id, peer_id)
            logger.received_handshake(me_id, peer_id)

            s.sendall(make_bitfield(my_bitfield.to_bytes()).encode())
            logger.sent_bitfield(me_id, peer_id)

            pc = PeerConnection(
                me_id=me_id,
                remote_id=peer_id,
                sock=s,
                my_bitfield=my_bitfield,
                num_pieces=num_pieces,
                piece_size=piece_size,
                file_name=file_name,
                logger=logger,
            )
            with neighbors_lock:
                neighbors[peer_id] = pc
            pc.start()

            return True
        except Exception:
            try:
                s.close()
            except Exception:
                pass
            time.sleep(0.3)
    return False


def preferred_unchoke_loop(
    me_id: int,
    my_bitfield: Bitfield,
    neighbors: Dict[int, PeerConnection],
    neighbors_lock: threading.Lock,
    logger: Logger,
    num_pref: int,
    interval: int,
):
    current_preferred: set[int] = set()

    while True:
        time.sleep(interval)

        with neighbors_lock:
            items = list(neighbors.items())

        # only consider interested neighbors
        candidates = []
        for pid, conn in items:
            if conn.remote_interested:
                downloaded = conn.get_and_reset_downloaded_bytes()
                candidates.append((downloaded, pid, conn))

        if not candidates:
            # no interested peers, choke all
            with neighbors_lock:
                for pid, conn in neighbors.items():
                    conn.choke()
            current_preferred.clear()
            logger.change_preferred_neighbors(me_id, [])
            continue

        if not my_bitfield.is_full():
            # sort by download amount, desc
            candidates.sort(key=lambda x: x[0], reverse=True)
        else:
            # as a seed, pick random interested neighbors
            random.shuffle(candidates)

        selected_ids: set[int] = set()
        for downloaded, pid, conn in candidates[:num_pref]:
            selected_ids.add(pid)

        # apply choke/unchoke
        with neighbors_lock:
            for pid, conn in neighbors.items():
                if pid in selected_ids:
                    conn.unchoke()
                else:
                    conn.choke()

        logger.change_preferred_neighbors(me_id, sorted(selected_ids))


def optimistic_unchoke_loop(
    me_id: int,
    neighbors: Dict[int, PeerConnection],
    neighbors_lock: threading.Lock,
    logger: Logger,
    interval: int,
):
    while True:
        time.sleep(interval)

        with neighbors_lock:
            items = list(neighbors.items())

        # choose among choked but interested neighbors
        candidates = []
        for pid, conn in items:
            if conn.remote_interested and conn.peer_choked:
                candidates.append((pid, conn))

        if not candidates:
            continue

        pid, conn = random.choice(candidates)
        conn.unchoke()
        logger.change_optimistic_neighbor(me_id, pid)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CNT4007 peer process")
    parser.add_argument("peer_id", type=int, help="peer id from PeerInfo.cfg")
    args = parser.parse_args()

    me_id = args.peer_id

    common = parse_common()
    peers = parse_peerinfo()
    me = None
    for p in peers:
        if p["id"] == me_id:
            me = p
            break
    if me is None:
        raise SystemExit(f"peer id {me_id} not found in PeerInfo.cfg")

    file_name = common.get("FileName", "TheFile.dat")
    file_size = int(common.get("FileSize", "0"))
    piece_size = int(common.get("PieceSize", "32768"))
    num_pieces = num_pieces_from_common(common)

    num_pref = int(common.get("NumberOfPreferredNeighbors", "2"))
    unchoke_interval = int(common.get("UnchokingInterval", "5"))
    optimistic_interval = int(common.get("OptimisticUnchokingInterval", "15"))

    logger = Logger(me_id)
    neighbors: Dict[int, PeerConnection] = {}
    neighbors_lock = threading.Lock()

    peer_folder = ensure_peer_folder(me_id)
    os.chdir(peer_folder)

    my_bf = Bitfield(num_pieces)

    if me["has"]:
        src_path = peer_folder / file_name
        if not src_path.exists():
            raise SystemExit(f"{src_path} does not exist but has_file = 1")
        pieces = split_file(str(src_path), piece_size)
        for idx, data in enumerate(pieces):
            write_piece(idx, data)
            my_bf.set_have(idx)

    logger.startup(common, me["has"], my_bf)
    logger.peerinfo_loaded(peers)
        
    server = PeerServer(
        peer_id=me_id,
        host=me["host"],
        port=me["port"],
        my_bitfield=my_bf,
        num_pieces=num_pieces,
        piece_size=piece_size,
        file_name=file_name,
        logger=logger,
        neighbors=neighbors,
        neighbors_lock=neighbors_lock,
    )
    server.start()

    for p in peers:
        if p["id"] == me_id:
            break
        connect_to(
            peer_id=p["id"],
            me_id=me_id,
            host=p["host"],
            port=p["port"],
            my_bitfield=my_bf,
            num_pieces=num_pieces,
            piece_size=piece_size,
            file_name=file_name,
            logger=logger,
            neighbors=neighbors,
            neighbors_lock=neighbors_lock,
        )

    # start choking managers
    pref_thread = threading.Thread(
        target=preferred_unchoke_loop,
        args=(
            me_id,
            my_bf,
            neighbors,
            neighbors_lock,
            logger,
            num_pref,
            unchoke_interval,
        ),
        daemon=True,
    )
    pref_thread.start()

    opt_thread = threading.Thread(
        target=optimistic_unchoke_loop,
        args=(
            me_id,
            neighbors,
            neighbors_lock,
            logger,
            optimistic_interval,
        ),
        daemon=True,
    )
    opt_thread.start()

    finished = False
    if my_bf.is_full():
        output_path = peer_folder / file_name
        merge_pieces(str(output_path), num_pieces)
        logger.completed_download(me_id)
        finished = True
    try:
        while True:
            time.sleep(1)

            # if I just became complete, merge and log once
            if (not finished) and my_bf.is_full():
                output_path = peer_folder / file_name
                merge_pieces(str(output_path), num_pieces)
                logger.completed_download(me_id)
                finished = True

            # after I am complete: if no neighbor is interested in me, I can exit
            with neighbors_lock:
                if neighbors and my_bf.is_full():
                    all_not_interested = True
                    for conn in neighbors.values():
                        if conn.remote_interested:
                            all_not_interested = False
                            break
                    if all_not_interested:
                        logger.custom(
                            f"Peer {me_id} stops service because all peers have completed download (no neighbor is interested)."
                        )
                        break

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup_pieces()
