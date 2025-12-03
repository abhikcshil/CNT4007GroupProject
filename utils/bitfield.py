class Bitfield:
    def __init__(self, num_pieces: int):
        self.num_pieces = num_pieces
        self._bytes = bytearray((num_pieces + 7) // 8)

    def set_have(self, index: int):
        byte_index = index // 8
        bit_index = index % 8
        self._bytes[byte_index] |= (1 << (7 - bit_index))

    def has(self, index: int) -> bool:
        byte_index = index // 8
        bit_index = index % 8
        return (self._bytes[byte_index] & (1 << (7 - bit_index))) != 0

    def to_bytes(self) -> bytes:
        return bytes(self._bytes)

    @classmethod
    def from_bytes(cls, num_pieces: int, data: bytes) -> "Bitfield":
        bf = cls(num_pieces)
        bf._bytes[:] = data[: len(bf._bytes)]
        return bf

    def is_full(self) -> bool:
        for i in range(self.num_pieces):
            if not self.has(i):
                return False
        return True
