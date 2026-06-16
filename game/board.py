# Board coordinate utilities for Glinski's hexagonal chess.
# Axial coordinates (q, r); valid cells satisfy max(|q|,|r|,|q+r|) <= 5.
# Files a-l (sans j): q = -5 to +5 (skipping nothing in q, j is just absent as a label).
# Center cell f6 = (0, 0).

FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'k', 'l']
FILE_TO_Q = {f: i - 5 for i, f in enumerate(FILES)}
Q_TO_FILE = {i - 5: f for i, f in enumerate(FILES)}


def is_valid(q: int, r: int) -> bool:
    return max(abs(q), abs(r), abs(q + r)) <= 5


def all_cells():
    return [(q, r) for q in range(-5, 6) for r in range(-5, 6) if is_valid(q, r)]


ALL_CELLS = all_cells()
ALL_CELLS_SET = set(ALL_CELLS)


def to_notation(q: int, r: int) -> str:
    rank = r + 6 + min(0, q)
    return Q_TO_FILE[q] + str(rank)


def from_notation(notation: str) -> tuple[int, int]:
    file_char = notation[0]
    rank = int(notation[1:])
    q = FILE_TO_Q[file_char]
    r = rank - 6 - min(0, q)
    return (q, r)


def cell_color(q: int, r: int) -> int:
    """3-coloring: adjacent cells always differ. Returns 0, 1, or 2."""
    return (q - r) % 3


def is_white_promotion_rank(q: int, r: int) -> bool:
    """True if this cell is the last rank in White's advancing direction."""
    return r == (5 - q if q >= 0 else 5)


def is_black_promotion_rank(q: int, r: int) -> bool:
    """True if this cell is the last rank in Black's advancing direction."""
    return r == (-5 if q >= 0 else -5 - q)
