import struct
from utils.constants import MessageType

class Message:
    def __init__(self, msg_type: int, payload: bytes = b""):
        self.msg_type = msg_type
        self.payload = payload or b""

    def encode(self) -> bytes:
        # message length (4 bytes) + type (1 byte) + payload
        length = len(self.payload) + 1
        return struct.pack("!IB", length, self.msg_type) + self.payload

    @staticmethod
    def decode(data: bytes):
        """Decode bytes into Message"""
        if len(data) < 5:
            raise ValueError("Message too short")

        length, msg_type = struct.unpack("!IB", data[:5])
        payload = data[5:5 + length - 1]
        return Message(msg_type, payload)

    def __repr__(self):
        return f"<Message type={self.msg_type} len={len(self.payload)}>"

def make_choke():
    return Message(MessageType.CHOKE)

def make_unchoke():
    return Message(MessageType.UNCHOKE)

def make_interested():
    return Message(MessageType.INTERESTED)

def make_not_interested():
    return Message(MessageType.NOT_INTERESTED)

def make_have(piece_index: int):
    return Message(MessageType.HAVE, struct.pack("!I", piece_index))

def make_bitfield(bitfield: bytes):
    return Message(MessageType.BITFIELD, bitfield)

def make_request(piece_index: int):
    return Message(MessageType.REQUEST, struct.pack("!I", piece_index))

def make_piece(piece_index: int, piece_data: bytes):
    return Message(MessageType.PIECE, struct.pack("!I", piece_index) + piece_data)

class MessageType:
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7

if __name__ == "__main__":
    # Example test
    msg = make_have(42)
    encoded = msg.encode()
    decoded = Message.decode(encoded)
    print("Encoded:", encoded)
    print("Decoded:", decoded)
