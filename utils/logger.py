from pathlib import Path
from datetime import datetime
import threading

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Logger:
    def __init__(self, peer_id: int):
        self.peer_id = peer_id
        self._lock = threading.Lock()
        self.log_path = PROJECT_ROOT / f"log_peer_{peer_id}.log"

        with self.log_path.open("w", encoding="utf8") as f:
            f.write(f"===== Log for Peer {peer_id} =====\n")

    def _ts(self) -> str:
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def _write(self, text: str):
        with self._lock, self.log_path.open("a", encoding="utf8") as f:
            f.write(f"[{self._ts()}] {text}\n")

    # --------------------------
    # Log Events
    # --------------------------

    # Connection events
    def connection_made(self, peer1: int, peer2: int):
        self._write(f"Peer {peer1} makes a connection to Peer {peer2}.")

    def connection_received(self, peer1: int, peer2: int):
        self._write(f"Peer {peer1} is connected from Peer {peer2}.")
    def choked_by(self, me_id: int, other_id: int):
        self._write(f"Peer {me_id} is choked by Peer {other_id}.")

    def unchoked_by(self, me_id: int, other_id: int):
        self._write(f"Peer {me_id} is unchoked by Peer {other_id}.")

    def choke(self, me_id: int, other_id: int):
        self._write(f"Peer {me_id} chokes Peer {other_id}.")

    def unchoke(self, me_id: int, other_id: int):
        self._write(f"Peer {me_id} unchokes Peer {other_id}.")

    def change_preferred_neighbors(self, me_id: int, neighbor_ids):
        ids_str = ", ".join(str(i) for i in neighbor_ids)
        self._write(f"Peer {me_id} has the preferred neighbors [{ids_str}].")

    def change_optimistic_neighbor(self, me_id: int, neighbor_id: int):
        self._write(
            f"Peer {me_id} has the optimistically unchoked neighbor {neighbor_id}."
        )

    # Message receipt
    def received_have(self, peer1: int, peer2: int, piece_index: int):
        self._write(f"Peer {peer1} received the 'have' message from Peer {peer2} for the piece {piece_index}.")

    def received_interested(self, peer1: int, peer2: int):
        self._write(f"Peer {peer1} received the 'interested' message from Peer {peer2}.")

    def received_not_interested(self, peer1: int, peer2: int):
        self._write(f"Peer {peer1} received the 'not interested' message from Peer {peer2}.")

    # Downloading
    def downloaded_piece(self, peer1: int, peer2: int, piece_index: int, num_pieces: int):
        self._write(
            f"Peer {peer1} has downloaded the piece {piece_index} from Peer {peer2}. "
            f"Now the number of pieces it has is {num_pieces}."
        )

    # Completion
    def completed_download(self, peer_id: int):
        self._write(f"Peer {peer_id} has downloaded the complete file.")

    # Generic custom entry (optional)
    def custom(self, msg: str):
        """Use for debug or temporary messages."""
        self._write(msg)


# --------------------------
# Self Test
# --------------------------
if __name__ == "__main__":
    logger = Logger(1001)
    logger.connection_made(1001, 1002)
    logger.connection_received(1001, 1003)
    logger.change_preferred_neighbors(1001, [1002, 1003])
    logger.change_optimistic_neighbor(1001, 1004)
    logger.unchoked_by(1001, 1002)
    logger.choked_by(1001, 1005)
    logger.received_have(1001, 1003, 15)
    logger.received_interested(1001, 1004)
    logger.received_not_interested(1001, 1005)
    logger.downloaded_piece(1001, 1002, 15, 42)
    logger.completed_download(1001)
    logger.custom("Debug: test complete.")
    print(f"Logs written to {logger.log_path}")
