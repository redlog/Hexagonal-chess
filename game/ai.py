# Negamax with alpha-beta pruning for Glinski's hexagonal chess.

import math
from .board import ALL_CELLS
from .pieces import (
    WHITE, BLACK, KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN,
    PIECE_VALUES, opponent
)
from .rules import all_legal_moves, is_in_check, compute_en_passant_target, apply_move

# Center control bonus table: distance from center (0,0) → bonus
_CENTER_BONUS = {}
for (q, r) in ALL_CELLS:
    dist = max(abs(q), abs(r), abs(q + r))
    _CENTER_BONUS[(q, r)] = (5 - dist) * 2  # 0-10 bonus, higher near center


def evaluate(board, color):
    score = 0
    for (q, r), (c, piece) in board.items():
        val = PIECE_VALUES[piece]
        center = _CENTER_BONUS[(q, r)]
        if piece == PAWN:
            center //= 2
        if c == color:
            score += val + center
        else:
            score -= val + center
    return score


def _order_moves(board, moves):
    def priority(m):
        dst = board.get(m['to'])
        if dst is not None:
            victim_val = PIECE_VALUES.get(dst[1], 0)
            src = board.get(m['from'])
            attacker_val = PIECE_VALUES.get(src[1], 0) if src else 0
            return -(victim_val * 10 - attacker_val)
        return 0
    return sorted(moves, key=priority)


def negamax(board, color, depth, alpha, beta, en_passant_target=None):
    moves = all_legal_moves(board, color, en_passant_target)

    if not moves:
        if is_in_check(board, color):
            return -PIECE_VALUES[KING] - depth * 100, None
        return 0, None

    if depth == 0:
        return evaluate(board, color), None

    moves = _order_moves(board, moves)
    best_move = None
    best_score = -math.inf

    for move in moves:
        new_board = apply_move(board, move)
        ep = compute_en_passant_target(board, move)
        score, _ = negamax(new_board, opponent(color), depth - 1, -beta, -alpha, ep)
        score = -score
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)
        if alpha >= beta:
            break

    return best_score, best_move


def get_best_move(board, color, depth, en_passant_target=None):
    _, move = negamax(board, color, depth, -math.inf, math.inf, en_passant_target)
    return move
