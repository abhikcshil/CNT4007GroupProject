# utils/bitfield.py
import math

class Bitfield:
    def __init__(self, num_pieces: int, data: bytes | None = None):
        self.num_pieces = int(num_pieces)
        nbytes = math.ceil(self.num_pieces / 8) if self.num_pieces > 0 else 0
        self._bits = bytearray(nbytes) if data is None else bytearray(data[:nbytes])

    def set_have(self, index: int) -> None:
        if index < 0 or index >= self.num_pieces:
            raise IndexError("piece index out of range")
        self._bits[index // 8] |= 0x80 >> (index % 8)

    def has(self, index: int) -> bool:
        if index < 0 or index >= self.num_pieces:
            return False
        return (self._bits[index // 8] & (0x80 >> (index % 8))) != 0

    def to_bytes(self) -> bytes:
        return bytes(self._bits)

    @classmethod
    def from_bytes(cls, num_pieces: int, data: bytes) -> "Bitfield":
        return cls(num_pieces, data)
