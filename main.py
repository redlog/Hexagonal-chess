import os
import threading
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from game.rules import GameState
from game.board import from_notation, to_notation, ALL_CELLS
from game.pieces import WHITE, BLACK, opponent
from game.ai import get_best_move

app = FastAPI()

# Global game state (single-player local game)
_state: GameState = GameState()
_ai_lock = threading.Lock()


# ─── API ──────────────────────────────────────────────────────────────────────

class NewGameRequest(BaseModel):
    player_color: str = "white"
    depth: int = 3


class SelectRequest(BaseModel):
    cell: str


class MoveRequest(BaseModel):
    from_cell: str
    to_cell: str
    promotion: Optional[str] = None


@app.post("/api/new_game")
def new_game(req: NewGameRequest):
    global _state
    color = req.player_color.lower()
    if color not in (WHITE, BLACK):
        raise HTTPException(400, "player_color must be 'white' or 'black'")
    depth = max(2, min(4, req.depth))
    _state = GameState(player_color=color, depth=depth)
    result = _state.to_dict()
    # If human plays Black, AI makes first move as White
    if color == BLACK:
        _do_ai_move()
        result = _state.to_dict()
    return result


@app.get("/api/state")
def get_state():
    return _state.to_dict()


@app.post("/api/select")
def select_cell(req: SelectRequest):
    """Return valid move destinations for the selected cell."""
    try:
        q, r = from_notation(req.cell)
    except Exception:
        raise HTTPException(400, f"Invalid cell: {req.cell}")

    src = _state.board.get((q, r))
    if src is None:
        return {"valid_moves": [], "reason": "No piece on that cell."}
    if src[0] != _state.turn:
        return {"valid_moves": [], "reason": "It is not your turn to move that piece."}
    if _state.game_over:
        return {"valid_moves": [], "reason": "Game is over."}

    legal = _state.get_legal_moves(q, r)
    # Deduplicate by destination (multiple promotion choices → one highlighted cell)
    seen = set()
    dests = []
    for m in legal:
        dest = to_notation(*m['to'])
        if dest not in seen:
            seen.add(dest)
            dests.append(dest)
    return {"valid_moves": dests, "requires_promotion": any('promotion' in m for m in legal)}


@app.post("/api/check_move")
def check_move(req: MoveRequest):
    """Return reason why a move is illegal (or ok if legal)."""
    try:
        fq, fr = from_notation(req.from_cell)
        tq, tr = from_notation(req.to_cell)
    except Exception:
        raise HTTPException(400, "Invalid cell notation.")

    if _state.game_over:
        return {"legal": False, "reason": "Game is over."}

    legal = _state.is_legal(fq, fr, tq, tr, req.promotion)
    reason = None if legal else _state.get_illegal_reason(fq, fr, tq, tr)
    return {"legal": legal, "reason": reason}


@app.post("/api/move")
def do_move(req: MoveRequest):
    global _state
    if _state.game_over:
        return {"success": False, "reason": "Game is over.", **_state.to_dict()}

    try:
        fq, fr = from_notation(req.from_cell)
        tq, tr = from_notation(req.to_cell)
    except Exception:
        raise HTTPException(400, "Invalid cell notation.")

    # Validate it's the human player's turn
    if _state.turn != _state.player_color:
        return {"success": False, "reason": "It is not your turn.", **_state.to_dict()}

    ok, reason = _state.do_move(fq, fr, tq, tr, req.promotion)
    if not ok:
        return {"success": False, "reason": reason, **_state.to_dict()}

    state_after_human = _state.to_dict()

    # AI responds if game not over
    ai_move_notation = None
    if not _state.game_over and _state.turn != _state.player_color:
        ai_move_notation = _do_ai_move()

    result = _state.to_dict()
    result["success"] = True
    result["ai_move"] = ai_move_notation
    # Exact board position after the human's move but before the AI replies,
    # so the client can render/animate the two moves separately.
    result["state_after_human"] = state_after_human
    return result


def _do_ai_move():
    """Have the AI make a move. Returns the move in notation or None."""
    global _state
    ai_color = opponent(_state.player_color)
    with _ai_lock:
        move = get_best_move(
            _state.board, ai_color, _state.depth, _state.en_passant_target
        )
    if move is None:
        return None
    fq, fr = move['from']
    tq, tr = move['to']
    promotion = move.get('promotion')
    _state.do_move(fq, fr, tq, tr, promotion)
    return {
        'from': to_notation(fq, fr),
        'to': to_notation(tq, tr),
        'promotion': promotion,
    }


@app.get("/api/cells")
def get_cells():
    """Return all 91 cell notations with their color index (0/1/2)."""
    from game.board import cell_color
    return {
        to_notation(q, r): cell_color(q, r)
        for q, r in ALL_CELLS
    }


# ─── Static files ─────────────────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
