# Legal move filtering (removes moves that leave own king in check),
# game state management, and check/checkmate/stalemate detection.

import copy
from .board import ALL_CELLS, to_notation, from_notation
from .pieces import (
    WHITE, BLACK, KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN,
    WHITE_START, BLACK_START, PAWN_ADVANCE, opponent
)
from .moves import pseudo_legal_moves, all_pseudo_legal, illegal_reason


def make_initial_board():
    board = {}
    for (q, r), piece in WHITE_START:
        board[(q, r)] = (WHITE, piece)
    for (q, r), piece in BLACK_START:
        board[(q, r)] = (BLACK, piece)
    return board


def find_king(board, color):
    for (q, r), (c, p) in board.items():
        if c == color and p == KING:
            return (q, r)
    return None


def is_in_check(board, color):
    king_pos = find_king(board, color)
    if king_pos is None:
        return True
    opp = opponent(color)
    for m in all_pseudo_legal(board, opp):
        if m['to'] == king_pos:
            return True
    return False


def apply_move(board, move):
    """Return a new board after applying move (a dict with 'from', 'to', optional keys)."""
    new_board = dict(board)
    fq, fr = move['from']
    tq, tr = move['to']
    piece_entry = new_board.pop((fq, fr))
    color, piece = piece_entry

    # En passant capture: remove the captured pawn
    if move.get('en_passant_capture'):
        adv_dq, adv_dr = PAWN_ADVANCE[color]
        cap_q, cap_r = tq - adv_dq, tr - adv_dr
        new_board.pop((cap_q, cap_r), None)

    # Place piece (handle promotion)
    new_piece = move.get('promotion', piece)
    new_board[(tq, tr)] = (color, new_piece)
    return new_board


def legal_moves_for(board, q, r, en_passant_target=None):
    """Return legal moves for piece at (q,r), filtering out those that leave own king in check."""
    piece_entry = board.get((q, r))
    if piece_entry is None:
        return []
    color = piece_entry[0]
    result = []
    for move in pseudo_legal_moves(board, q, r, en_passant_target):
        new_board = apply_move(board, move)
        if not is_in_check(new_board, color):
            result.append(move)
    return result


def all_legal_moves(board, color, en_passant_target=None):
    result = []
    for (q, r), (c, _) in board.items():
        if c == color:
            result.extend(legal_moves_for(board, q, r, en_passant_target))
    return result


def compute_en_passant_target(board_before, move):
    """If move is a pawn double-step, return the skipped cell (en passant target)."""
    fq, fr = move['from']
    tq, tr = move['to']
    piece_entry = board_before.get((fq, fr))
    if piece_entry is None or piece_entry[1] != PAWN:
        return None
    adv_dq, adv_dr = PAWN_ADVANCE[piece_entry[0]]
    # Pawn advance is always (0, ±1), double step is (0, ±2)
    if tq == fq and (tr - fr) == 2 * adv_dr:
        return (fq, fr + adv_dr)
    return None


class GameState:
    def __init__(self, player_color=WHITE, depth=3):
        self.board = make_initial_board()
        self.turn = WHITE
        self.en_passant_target = None
        self.player_color = player_color
        self.depth = depth
        self.game_over = False
        self.winner = None   # None = draw, else WHITE or BLACK
        self.result_reason = None
        self.halfmove_clock = 0
        self.fullmove = 1

    def get_legal_moves(self, q=None, r=None):
        if q is not None:
            return legal_moves_for(self.board, q, r, self.en_passant_target)
        return all_legal_moves(self.board, self.turn, self.en_passant_target)

    def is_legal(self, fq, fr, tq, tr, promotion=None):
        moves = legal_moves_for(self.board, fq, fr, self.en_passant_target)
        for m in moves:
            if m['to'] == (tq, tr):
                if promotion is None or m.get('promotion') == promotion:
                    return True
        return False

    def needs_promotion(self, fq, fr, tq, tr):
        """Return True if this move requires choosing a promotion piece."""
        from .board import is_white_promotion_rank, is_black_promotion_rank
        src = self.board.get((fq, fr))
        if src is None or src[1] != PAWN:
            return False
        color = src[0]
        return (color == WHITE and is_white_promotion_rank(tq, tr)) or \
               (color == BLACK and is_black_promotion_rank(tq, tr))

    def do_move(self, fq, fr, tq, tr, promotion=None):
        """Apply a move. Returns True if successful. Promotion required for pawn promotion moves."""
        if self.game_over:
            return False, "Game is over."

        src = self.board.get((fq, fr))
        if src is None or src[0] != self.turn:
            return False, "It is not your turn to move that piece."

        # Find matching legal move
        moves = legal_moves_for(self.board, fq, fr, self.en_passant_target)
        chosen = None
        for m in moves:
            if m['to'] == (tq, tr):
                if 'promotion' not in m:
                    chosen = m
                    break
                elif promotion is not None and m.get('promotion') == promotion:
                    chosen = m
                    break
        if chosen is None:
            if not moves:
                reason = illegal_reason(self.board, fq, fr, tq, tr, self.turn, self.en_passant_target)
            else:
                # Check if move exists but leaves king in check
                pseudo = {m['to'] for m in pseudo_legal_moves(self.board, fq, fr, self.en_passant_target)}
                if (tq, tr) in pseudo:
                    reason = "That move would leave your king in check."
                else:
                    reason = illegal_reason(self.board, fq, fr, tq, tr, self.turn, self.en_passant_target)
            return False, reason or "Illegal move."

        # Apply
        ep_target = compute_en_passant_target(self.board, chosen)
        src = self.board.get((fq, fr))
        dst = self.board.get((tq, tr))
        self.board = apply_move(self.board, chosen)
        self.en_passant_target = ep_target

        # Update clocks
        if src and (src[1] == PAWN or dst is not None):
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        if self.turn == BLACK:
            self.fullmove += 1
        self.turn = opponent(self.turn)

        # Check game end
        self._check_game_end()
        return True, None

    def _check_game_end(self):
        moves = all_legal_moves(self.board, self.turn, self.en_passant_target)
        if not moves:
            if is_in_check(self.board, self.turn):
                self.game_over = True
                self.winner = opponent(self.turn)
                self.result_reason = "checkmate"
            else:
                self.game_over = True
                self.winner = None
                self.result_reason = "stalemate"
        elif self.halfmove_clock >= 100:
            self.game_over = True
            self.winner = None
            self.result_reason = "50-move rule"

    def get_illegal_reason(self, fq, fr, tq, tr):
        pseudo = {m['to'] for m in pseudo_legal_moves(self.board, fq, fr, self.en_passant_target)}
        legal = {m['to'] for m in legal_moves_for(self.board, fq, fr, self.en_passant_target)}
        if (tq, tr) in pseudo and (tq, tr) not in legal:
            return "That move would leave your king in check."
        return illegal_reason(self.board, fq, fr, tq, tr, self.turn, self.en_passant_target)

    def to_dict(self):
        pieces = {}
        for (q, r), (color, piece) in self.board.items():
            notation = to_notation(q, r)
            pieces[notation] = {'color': color, 'piece': piece}
        in_check = is_in_check(self.board, self.turn)
        return {
            'pieces': pieces,
            'turn': self.turn,
            'player_color': self.player_color,
            'depth': self.depth,
            'game_over': self.game_over,
            'winner': self.winner,
            'result_reason': self.result_reason,
            'in_check': in_check,
            'en_passant_target': to_notation(*self.en_passant_target) if self.en_passant_target else None,
            'fullmove': self.fullmove,
        }
