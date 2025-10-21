import os
import threading
from datetime import datetime

class Logger:
    """
    Thread-safe logger for each peer process.
    Each peer writes to its own log file: log_peer_[peerID].log
    """

    def __init__(self, peer_id: int, log_dir: str = "."):
        self.peer_id = peer_id
        self.log_path = os.path.join(log_dir, f"log_peer_{peer_id}.log")
        self.lock = threading.Lock()

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        # Start log file fresh each run
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(f"===== Log for Peer {peer_id} =====\n")

    # --------------------------
    # Helper
    # --------------------------
    def _timestamp(self) -> str:
        """Return formatted timestamp."""
        return datetime.now().strftime("[%Y/%m/%d %H:%M:%S]")

    def _write(self, message: str):
        """Thread-safe write to log file."""
        with self.lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"{self._timestamp()} {message}\n")

    # --------------------------
    # Log Events
    # --------------------------

    # Connection events
    def connection_made(self, peer1: int, peer2: int):
        self._write(f"Peer {peer1} makes a connection to Peer {peer2}.")

    def connection_received(self, peer1: int, peer2: int):
        self._write(f"Peer {peer1} is connected from Peer {peer2}.")

    # Neighbor state
    def change_preferred_neighbors(self, peer_id: int, neighbor_ids):
        ids = ", ".join(map(str, neighbor_ids))
        self._write(f"Peer {peer_id} has the preferred neighbors [{ids}].")

    def change_optimistic_neighbor(self, peer_id: int, opt_id: int):
        self._write(f"Peer {peer_id} has the optimistically unchoked neighbor {opt_id}.")

    # Choke / Unchoke
    def unchoked_by(self, peer1: int, peer2: int):
        self._write(f"Peer {peer1} is unchoked by Peer {peer2}.")

    def choked_by(self, peer1: int, peer2: int):
        self._write(f"Peer {peer1} is choked by Peer {peer2}.")

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
