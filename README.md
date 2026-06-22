# Hexagonal Chess (Glinski's, 1949)

A browser-based implementation of Glinski's hexagonal chess variant, played on a 91-cell hex board with 11 files and 3 cell colors.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)

## Features

- **Full Glinski's rules** — en passant, pawn promotion, check/checkmate/stalemate detection
- **AI opponent** — negamax search with alpha-beta pruning and MVV-LVA move ordering (depth 2–4, default 3)
- **Interactive SVG board** — flat-top hexagons with Unicode chess pieces (♔♕♖♗♘♙)
- **Move highlighting** — selected piece in blue, valid destinations in green, last move in yellow
- **Illegal move explanations** — clicking an invalid destination explains why the move is not allowed
- **Color & difficulty selection** — play as white or black, choose AI search depth before starting

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

## How to Play

1. Choose your color (white/black) and AI depth (2–4), then click **Start Game**
2. Click a piece to select it — valid moves highlight in green
3. Click a highlighted cell to move, or click the selected piece again to deselect
4. The AI responds automatically after your move
5. For pawn promotion, a panel appears to choose the new piece

## Project Structure

```
main.py              FastAPI server and API endpoints
game/
  board.py           Axial coordinate system, notation, cell colors
  pieces.py          Piece constants, directions, starting positions
  moves.py           Pseudo-legal move generation, illegal move reasons
  rules.py           Legal move filtering, GameState, game-end detection
  ai.py              Negamax with alpha-beta pruning, evaluation
static/
  index.html         Single-page SVG frontend
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/state` | Current game state |
| `POST` | `/api/new_game` | Start a new game (`player_color`, `depth`) |
| `POST` | `/api/select` | Get valid moves for a cell |
| `POST` | `/api/move` | Make a move (triggers AI response) |
| `POST` | `/api/check_move` | Check why a move is illegal |
| `GET` | `/api/cells` | All 91 cells with color indices |

## Board Geometry

Glinski's board uses axial coordinates (q, r) where a cell is valid when `max(|q|, |r|, |q+r|) <= 5`, yielding exactly 91 hexagonal cells across 11 files (a–l, skipping j). Three cell colors are determined by `(q - r) % 3`. Each side starts with 18 pieces: 1 king, 1 queen, 2 rooks, 3 bishops, 2 knights, and 9 pawns.
