import threading
import socket
from typing import Optional, Set

from utils.bitfield import Bitfield
from utils.message import (
    Message,
    make_bitfield,
    make_interested,
    make_not_interested,
    make_have,
    make_request,
    make_piece,
    make_choke,
    make_unchoke,
)
from utils.constants import MessageType
from utils.logger import Logger
from utils.file_manager import read_piece, write_piece
from utils.file_manager import read_piece, write_piece, merge_pieces


def recv_all(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("socket closed")
        data += chunk
    return data


class PeerConnection(threading.Thread):
    def __init__(
        self,
        me_id: int,
        remote_id: int,
        sock: socket.socket,
        my_bitfield: Bitfield,
        num_pieces: int,
        piece_size: int,
        file_name: str,
        logger: Optional[Logger] = None,
    ):
        super().__init__(daemon=True)
        self.me_id = me_id
        self.remote_id = remote_id
        self.sock = sock
        self.my_bitfield = my_bitfield
        self.num_pieces = num_pieces
        self.piece_size = piece_size
        self.file_name = file_name
        self.logger = logger

        self.remote_bitfield: Optional[Bitfield] = None

        self.am_interested = False
        self.peer_interested = False
        self.am_choked = False         # remote chokes me? start unchoked
        self.peer_choked = False       # I choke remote? start unchoked
        self.remote_interested = False # remote is interested in me?

        self._interval_downloaded = 0  # bytes downloaded in current interval

        self._send_lock = threading.Lock()
        self._alive = True

        self.requested: Set[int] = set()
        self.have_count = sum(1 for i in range(self.num_pieces) if self.my_bitfield.has(i))


    def get_and_reset_downloaded_bytes(self) -> int:
        value = self._interval_downloaded
        self._interval_downloaded = 0
        return value

    def choke(self):
        if not self.peer_choked:
            self.peer_choked = True
            try:
                self._send(make_choke())
            except OSError:
                return
            if self.logger:
                self.logger.choke(self.me_id, self.remote_id)

    def unchoke(self):
        if self.peer_choked:
            self.peer_choked = False
            try:
                self._send(make_unchoke())
            except OSError:
                return
            if self.logger:
                self.logger.unchoke(self.me_id, self.remote_id)
                
    def stop(self):
        self._alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass

    def send_message(self, msg: Message):
        encoded = msg.encode()
        with self._send_lock:
            self.sock.sendall(encoded)

    def _send(self, msg: Message) -> None:
        """
        Send a single Message to the remote peer.
        """
        try:
            self.sock.sendall(msg.encode())
        except OSError:
            # connection is broken, stop this thread gracefully if you like
            try:
                self.sock.close()
            except OSError:
                pass
            
    def run(self):
        try:
            while self._alive:
                hdr = recv_all(self.sock, 4)
                length = int.from_bytes(hdr, "big")
                if length <= 0:
                    continue
                frame = hdr + recv_all(self.sock, length)
                msg = Message.decode(frame)
                self._handle_message(msg)
        except Exception:
            self._alive = False
            self.stop()


    def _handle_message(self, msg: Message):
        t = msg.msg_type

        if t == MessageType.CHOKE:
            self.am_choked = True
            if self.logger:
                self.logger.choked_by(self.me_id, self.remote_id)
            # when choked we stop sending new requests and clear pending requests
            self.requested.clear()
            return

        if t == MessageType.UNCHOKE:
            self.am_choked = False
            if self.logger:
                self.logger.unchoked_by(self.me_id, self.remote_id)
            # we just got unchoked, try to request next piece
            self._maybe_request_piece()
            return

        if t == MessageType.INTERESTED:
            self.remote_interested = True
            if self.logger:
                self.logger.received_interested(self.me_id, self.remote_id)
            return

        if t == MessageType.NOT_INTERESTED:
            self.remote_interested = False
            if self.logger:
                self.logger.received_not_interested(self.me_id, self.remote_id)
            return

        if t == MessageType.HAVE:
            self._handle_have(msg.payload)
            return

        if t == MessageType.BITFIELD:
            if self.logger:
                self.logger.received_bitfield(self.me_id, self.remote_id)
            self._handle_bitfield(msg.payload)
            return

        if t == MessageType.REQUEST:
            self._handle_request(msg.payload)
            return

        if t == MessageType.PIECE:
            self._handle_piece(msg.payload)
            return

    def _handle_bitfield(self, payload: bytes):
        self.remote_bitfield = Bitfield.from_bytes(self.num_pieces, payload)
        self._update_interest()
        self._maybe_request_piece()

    def _handle_have(self, payload: bytes):
        if len(payload) < 4:
            return
        piece_index = int.from_bytes(payload[:4], "big")

        if self.remote_bitfield is None:
            self.remote_bitfield = Bitfield(self.num_pieces)
        self.remote_bitfield.set_have(piece_index)

        if self.logger:
            self.logger.received_have(self.me_id, self.remote_id, piece_index, self.remote_bitfield)

        self._update_interest()
        self._maybe_request_piece()

    def _handle_request(self, payload: bytes):
        if self.peer_choked:
            # I am choking this peer, ignore its request
            return
        if len(payload) < 4:
            return
        piece_index = int.from_bytes(payload[:4], "big")
        if not self.my_bitfield.has(piece_index):
            return
        try:
            data = read_piece(piece_index)
        except FileNotFoundError:
            return
        msg = make_piece(piece_index, data)
        
        
        if self.logger:
            self.logger.sent_piece(self.me_id, self.remote_id, piece_index)
    
        self.send_message(msg)

    def _handle_piece(self, payload: bytes):
        if len(payload) < 4:
            return
        piece_index = int.from_bytes(payload[:4], "big")
        data = payload[4:]
        
        self._interval_downloaded += len(data)
        
        write_piece(piece_index, data)

        if not self.my_bitfield.has(piece_index):
            self.my_bitfield.set_have(piece_index)
            self.have_count += 1
            if self.logger:
                self.logger.downloaded_piece(
                    self.me_id, self.remote_id, piece_index, self.have_count
                )
            self.send_message(make_have(piece_index))
            self.logger.sent_have(self.me_id, self.remote_id, piece_index)

        if piece_index in self.requested:
            self.requested.remove(piece_index)

        self._update_interest()
        self._maybe_request_piece()



    def _update_interest(self):
        if self.remote_bitfield is None:
            return

        interesting = False
        for i in range(self.num_pieces):
            if self.remote_bitfield.has(i) and not self.my_bitfield.has(i):
                interesting = True
                break

        if interesting and not self.am_interested:
            self.send_message(make_interested())
            self.am_interested = True
            self.logger.sent_interested(self.me_id, self.remote_id)
        elif not interesting and self.am_interested:
            self.send_message(make_not_interested())
            self.am_interested = False
            self.logger.sent_not_interested(self.me_id, self.remote_id)

    def _maybe_request_piece(self):
        if self.remote_bitfield is None:
            return
        if self.am_choked:
            return

        for i in range(self.num_pieces):
            if (
                self.remote_bitfield.has(i)
                and not self.my_bitfield.has(i)
                and i not in self.requested
            ):
                if self.logger:
                    self.logger.request_piece(self.me_id, self.remote_id, i)
                self.send_message(make_request(i))
                self.requested.add(i)
                break
