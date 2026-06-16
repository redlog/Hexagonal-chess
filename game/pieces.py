# Piece constants, starting positions, and movement direction tables.

WHITE = 'white'
BLACK = 'black'

KING   = 'king'
QUEEN  = 'queen'
ROOK   = 'rook'
BISHOP = 'bishop'
KNIGHT = 'knight'
PAWN   = 'pawn'

PIECE_TYPES = [KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN]

UNICODE = {
    (WHITE, KING):   '♔',
    (WHITE, QUEEN):  '♕',
    (WHITE, ROOK):   '♖',
    (WHITE, BISHOP): '♗',
    (WHITE, KNIGHT): '♘',
    (WHITE, PAWN):   '♙',
    (BLACK, KING):   '♚',
    (BLACK, QUEEN):  '♛',
    (BLACK, ROOK):   '♜',
    (BLACK, BISHOP): '♝',
    (BLACK, KNIGHT): '♞',
    (BLACK, PAWN):   '♟',
}

PIECE_VALUES = {
    KING:   20000,
    QUEEN:  900,
    ROOK:   500,
    BISHOP: 330,
    KNIGHT: 320,
    PAWN:   100,
}

# Cardinal directions (rook moves)
CARDINAL = [(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]

# Diagonal directions (bishop moves)
DIAGONAL = [(2,-1),(-2,1),(1,1),(-1,-1),(1,-2),(-1,2)]

# Knight leaps
KNIGHT_MOVES = [
    (1,2),(2,1),(3,-1),(1,-3),(-1,-2),(-2,-1),
    (-3,1),(-1,3),(-2,3),(-3,2),(2,-3),(3,-2)
]

# Pawn advance and capture directions per color
PAWN_ADVANCE = {WHITE: (0, 1), BLACK: (0, -1)}
PAWN_CAPTURES = {WHITE: [(1, 0), (-1, 1)], BLACK: [(-1, 0), (1, -1)]}

# Starting position: list of ((q, r), piece_type)
WHITE_START = [
    ((1, -5),  KING),
    ((-1, -4), QUEEN),
    ((-3, -2), ROOK),
    ((3, -5),  ROOK),
    ((-2, -3), KNIGHT),
    ((2, -5),  KNIGHT),
    ((0, -5),  BISHOP),
    ((0, -4),  BISHOP),
    ((0, -3),  BISHOP),
    ((-4, -1), PAWN),
    ((-3, -1), PAWN),
    ((-2, -1), PAWN),
    ((-1, -1), PAWN),
    ((0,  -1), PAWN),
    ((1,  -2), PAWN),
    ((2,  -3), PAWN),
    ((3,  -4), PAWN),
    ((4,  -5), PAWN),
]

BLACK_START = [
    ((-q, -r), pt) for ((q, r), pt) in WHITE_START
]

# Pawn starting cells (for double-move eligibility)
WHITE_PAWN_START = frozenset(cell for cell, pt in WHITE_START if pt == PAWN)
BLACK_PAWN_START = frozenset(cell for cell, pt in BLACK_START if pt == PAWN)

def opponent(color: str) -> str:
    return BLACK if color == WHITE else WHITE
