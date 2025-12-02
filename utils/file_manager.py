from pathlib import Path


def get_piece_path(piece_index: int) -> Path:
    return Path(f"piece_{piece_index}.dat")


def split_file(file_path: str, piece_size: int) -> list[bytes]:
    pieces: list[bytes] = []
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(piece_size)
            if not chunk:
                break
            pieces.append(chunk)
    return pieces


def write_piece(piece_index: int, data: bytes) -> None:
    path = get_piece_path(piece_index)
    with open(path, "wb") as f:
        f.write(data)


def read_piece(piece_index: int) -> bytes:
    path = get_piece_path(piece_index)
    with open(path, "rb") as f:
        return f.read()


def merge_pieces(output_path: str, total_pieces: int) -> None:
    """
    Merge piece_0.dat ... piece_{total_pieces-1}.dat
    into a single file at output_path.
    """
    with open(output_path, "wb") as out:
        for i in range(total_pieces):
            path = get_piece_path(i)
            with open(path, "rb") as f:
                out.write(f.read())


# Optional helpers (not required, but harmless)
def load_piece_indices() -> list[int]:
    """
    Return all piece indices that exist on disk.
    """
    result: list[int] = []
    i = 0
    while True:
        path = get_piece_path(i)
        if not path.exists():
            break
        result.append(i)
        i += 1
    return result

def cleanup_pieces() -> None:
    i = 0
    while True:
        path = get_piece_path(i)
        if not path.exists():
            break
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        i += 1