# Pseudo-legal move generation (does not check for self-check).
# A Move is a dict: {from, to, promotion (optional), en_passant_capture (optional)}

from .board import is_valid, is_white_promotion_rank, is_black_promotion_rank
from .pieces import (
    WHITE, BLACK, KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN,
    CARDINAL, DIAGONAL, KNIGHT_MOVES, PAWN_ADVANCE, PAWN_CAPTURES,
    WHITE_PAWN_START, BLACK_PAWN_START, opponent, PIECE_TYPES
)


def _slide(board, q, r, dq, dr, color):
    """Yield all cells reachable by sliding from (q,r) in direction (dq,dr)."""
    nq, nr = q + dq, r + dr
    while is_valid(nq, nr):
        occupant = board.get((nq, nr))
        if occupant is None:
            yield (nq, nr)
        else:
            if occupant[0] != color:
                yield (nq, nr)  # capture
            break
        nq += dq
        nr += dr


def pseudo_legal_moves(board, q, r, en_passant_target=None):
    """Return list of pseudo-legal move dicts for the piece at (q, r)."""
    occupant = board.get((q, r))
    if occupant is None:
        return []
    color, piece = occupant
    moves = []

    if piece == ROOK:
        for dq, dr in CARDINAL:
            for nq, nr in _slide(board, q, r, dq, dr, color):
                moves.append({'from': (q,r), 'to': (nq,nr)})

    elif piece == BISHOP:
        for dq, dr in DIAGONAL:
            for nq, nr in _slide(board, q, r, dq, dr, color):
                moves.append({'from': (q,r), 'to': (nq,nr)})

    elif piece == QUEEN:
        for dq, dr in CARDINAL + DIAGONAL:
            for nq, nr in _slide(board, q, r, dq, dr, color):
                moves.append({'from': (q,r), 'to': (nq,nr)})

    elif piece == KING:
        for dq, dr in CARDINAL:
            nq, nr = q + dq, r + dr
            if is_valid(nq, nr):
                occupant2 = board.get((nq, nr))
                if occupant2 is None or occupant2[0] != color:
                    moves.append({'from': (q,r), 'to': (nq,nr)})

    elif piece == KNIGHT:
        for dq, dr in KNIGHT_MOVES:
            nq, nr = q + dq, r + dr
            if is_valid(nq, nr):
                occupant2 = board.get((nq, nr))
                if occupant2 is None or occupant2[0] != color:
                    moves.append({'from': (q,r), 'to': (nq,nr)})

    elif piece == PAWN:
        adv_dq, adv_dr = PAWN_ADVANCE[color]
        # Single step forward
        nq, nr = q + adv_dq, r + adv_dr
        if is_valid(nq, nr) and board.get((nq, nr)) is None:
            _add_pawn_move(moves, q, r, nq, nr, color)
            # Double step from starting square
            start_set = WHITE_PAWN_START if color == WHITE else BLACK_PAWN_START
            if (q, r) in start_set:
                nq2, nr2 = nq + adv_dq, nr + adv_dr
                if is_valid(nq2, nr2) and board.get((nq2, nr2)) is None:
                    _add_pawn_move(moves, q, r, nq2, nr2, color)

        # Captures
        for cdq, cdr in PAWN_CAPTURES[color]:
            nq, nr = q + cdq, r + cdr
            if not is_valid(nq, nr):
                continue
            occupant2 = board.get((nq, nr))
            if occupant2 is not None and occupant2[0] != color:
                _add_pawn_move(moves, q, r, nq, nr, color)
            elif en_passant_target == (nq, nr):
                moves.append({
                    'from': (q,r), 'to': (nq,nr),
                    'en_passant_capture': True
                })

    return moves


def _add_pawn_move(moves, fq, fr, tq, tr, color):
    """Add pawn move, expanding to promotion moves if applicable."""
    promotes = (
        (color == WHITE and is_white_promotion_rank(tq, tr)) or
        (color == BLACK and is_black_promotion_rank(tq, tr))
    )
    if promotes:
        for promo in [QUEEN, ROOK, BISHOP, KNIGHT]:
            moves.append({'from': (fq,fr), 'to': (tq,tr), 'promotion': promo})
    else:
        moves.append({'from': (fq,fr), 'to': (tq,tr)})


def all_pseudo_legal(board, color, en_passant_target=None):
    """All pseudo-legal moves for the given color."""
    moves = []
    for (q, r), (c, _) in board.items():
        if c == color:
            moves.extend(pseudo_legal_moves(board, q, r, en_passant_target))
    return moves


def illegal_reason(board, fq, fr, tq, tr, color, en_passant_target=None):
    """
    Return a human-readable reason why (fq,fr)->(tq,tr) is not in pseudo-legal moves,
    or None if it is pseudo-legal (ignoring check).
    """
    src = board.get((fq, fr))
    if src is None:
        return "No piece on that cell."
    if src[0] != color:
        return "That is your opponent's piece."
    if not is_valid(tq, tr):
        return "Destination is off the board."

    _, piece = src
    dst = board.get((tq, tr))
    if dst is not None and dst[0] == color:
        return "You cannot capture your own piece."

    legal_targets = {m['to'] for m in pseudo_legal_moves(board, fq, fr, en_passant_target)}
    if (tq, tr) not in legal_targets:
        if piece == PAWN:
            adv_dq, adv_dr = PAWN_ADVANCE[color]
            nq, nr = fq + adv_dq, fr + adv_dr
            if (tq, tr) == (nq, nr) and dst is not None:
                return "Pawns cannot capture straight ahead; they capture diagonally."
            if dst is None and (tq - fq, tr - fr) not in PAWN_CAPTURES[color]:
                return "Pawns can only capture diagonally (one step to an adjacent file)."
            if dst is None and (tq, tr) not in legal_targets:
                return "That cell is blocked or not reachable by this pawn."
            return "Pawns can only advance straight forward (one or two steps from start)."
        if piece == KNIGHT:
            return ("Knights leap in an L-shape: 2 steps along a hex axis then 1 step "
                    "to the side (12 possible destinations).")
        if piece == BISHOP:
            return ("Bishops slide diagonally, staying on cells of the same color "
                    "(direction between two adjacent file-directions).")
        if piece == ROOK:
            return "Rooks slide along one of the 6 straight hex-grid lines."
        if piece == QUEEN:
            return "Queens slide along any of the 12 straight or diagonal hex lines."
        if piece == KING:
            return "Kings move one step to any of the 6 adjacent cells."
    return None
