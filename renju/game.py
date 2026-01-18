from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from renju.board import Board, Cell, Point
from renju.rules import ForbiddenResult, legal_move, winner_for_move, winning_line


class GameStatus(str, Enum):
    PLAYING = "playing"
    BLACK_WON = "blackWon"
    WHITE_WON = "whiteWon"
    ILLEGAL_MOVE = "illegalMove"
    DRAW = "draw"


class Player(str, Enum):
    ONE = "Player 1"
    TWO = "Player 2"


@dataclass(frozen=True)
class Move:
    player: Player
    cell: Cell
    point: Point


@dataclass
class MoveResult:
    success: bool
    status: GameStatus
    message: str
    forbidden: Optional[ForbiddenResult] = None
    winning_points: List[Point] = field(default_factory=list)


class Game:
    def __init__(self, size: int = 15, history_dir: str | Path = "history") -> None:
        self.board = Board(size=size)
        self.current_player = Player.ONE
        self.status = GameStatus.PLAYING
        self.history: List[Move] = []
        self.winning_points: List[Point] = []
        self.history_dir = Path(history_dir)
        self.history_path = self._new_history_path()
        self.history_saved = False
        self.last_forbidden: Optional[tuple[Point, str]] = None
        self.player_colors: Dict[Player, Cell] = {
            Player.ONE: Cell.BLACK,
            Player.TWO: Cell.WHITE,
        }
        self.swap_available = False
        self.swap_decided = False
        self.candidate_points: List[Point] = []
        self.candidate_removal_required = False
        self.candidate_player: Optional[Player] = None

    def reset(self) -> None:
        self.board = Board(size=self.board.size)
        self.current_player = Player.ONE
        self.status = GameStatus.PLAYING
        self.history.clear()
        self.winning_points.clear()
        self.last_forbidden = None
        self.history_path = self._new_history_path()
        self.history_saved = False
        self.player_colors = {
            Player.ONE: Cell.BLACK,
            Player.TWO: Cell.WHITE,
        }
        self.swap_available = False
        self.swap_decided = False
        self.candidate_points.clear()
        self.candidate_removal_required = False
        self.candidate_player = None

    def switch_player(self) -> None:
        self.current_player = self.other_player(self.current_player)

    def other_player(self, player: Player) -> Player:
        return Player.TWO if player == Player.ONE else Player.ONE

    def current_cell(self) -> Cell:
        return self.player_colors[self.current_player]

    def decide_swap(self, swap: bool) -> str:
        if not self.swap_available or self.swap_decided:
            return "Swap decision is not available."
        if self.current_cell() != Cell.WHITE:
            return "Only the white player can decide whether to swap."
        self.swap_decided = True
        self.swap_available = False
        if swap:
            self.player_colors[Player.ONE], self.player_colors[Player.TWO] = (
                self.player_colors[Player.TWO],
                self.player_colors[Player.ONE],
            )
            self.current_player = self._player_for_cell(Cell.WHITE)
            return "Colors swapped."
        self.current_player = self._player_for_cell(Cell.WHITE)
        return "Colors unchanged."

    def _player_for_cell(self, cell: Cell) -> Player:
        for player, player_cell in self.player_colors.items():
            if player_cell == cell:
                return player
        raise ValueError(f"No player assigned to {cell}.")

    def should_start_candidate_phase(self) -> bool:
        return (
            len(self.history) == 4
            and self.current_cell() == Cell.BLACK
            and not self.candidate_points
            and not self.candidate_removal_required
        )

    def place_candidate(self, point: Point) -> MoveResult:
        if self.candidate_removal_required:
            return MoveResult(
                False,
                self.status,
                "White must remove one of the candidate moves before continuing.",
            )

        if not self.candidate_points:
            self.candidate_player = self.current_player

        if not self.board.in_bounds(point):
            return MoveResult(False, self.status, "Move is out of bounds.")

        if not self.board.is_empty(point):
            return MoveResult(False, self.status, "Intersection is already occupied.")

        self.board.place(point, self.current_cell())
        forbidden = legal_move(self.board, point, self.current_cell())
        if forbidden.is_forbidden:
            self.board.place(point, Cell.EMPTY)
            self.status = GameStatus.WHITE_WON
            self.last_forbidden = (point, forbidden.reason or "forbidden")
            self._finalize_if_complete()
            return MoveResult(
                False,
                self.status,
                f"Forbidden move by Black ({forbidden.reason}). White wins!",
                forbidden=forbidden,
            )

        self.candidate_points.append(point)
        if len(self.candidate_points) < 2:
            return MoveResult(True, self.status, "First candidate placed. Place a second.")

        self.candidate_removal_required = True
        self.switch_player()
        return MoveResult(
            True,
            self.status,
            "Two candidate moves placed. White must remove one of them.",
        )

    def remove_candidate(self, point: Point) -> MoveResult:
        if not self.candidate_removal_required or not self.candidate_points:
            return MoveResult(False, self.status, "No candidate moves to remove.")

        if point not in self.candidate_points:
            return MoveResult(False, self.status, "Select one of the candidate moves to remove.")

        self.board.place(point, Cell.EMPTY)
        remaining = next(pt for pt in self.candidate_points if pt != point)
        candidate_player = self.candidate_player
        self.candidate_points.clear()
        self.candidate_removal_required = False
        self.candidate_player = None

        if candidate_player is None:
            return MoveResult(False, self.status, "Candidate move tracking error.")

        cell = self.player_colors[candidate_player]
        self.history.append(Move(player=candidate_player, cell=cell, point=remaining))

        if winner_for_move(self.board, remaining, cell):
            self.winning_points = list(winning_line(self.board, remaining, cell))
            self.status = GameStatus.BLACK_WON if cell == Cell.BLACK else GameStatus.WHITE_WON
            self._finalize_if_complete()
            return MoveResult(True, self.status, f"{cell.value} wins!")

        if not any(True for _ in self.board.empty_points()):
            self.status = GameStatus.DRAW
            self._finalize_if_complete()
            return MoveResult(True, self.status, "Game ended in a draw.")

        return MoveResult(True, self.status, "Candidate removed. White to move.")

    def place_move(self, point: Point) -> MoveResult:
        if self.status != GameStatus.PLAYING:
            return MoveResult(False, self.status, "Game is already over.")

        if self.swap_available and not self.swap_decided:
            return MoveResult(
                False,
                self.status,
                "White must decide whether to swap colors before continuing.",
            )

        if self.should_start_candidate_phase() or self.candidate_points:
            return self.place_candidate(point)

        if self.candidate_removal_required:
            return MoveResult(
                False,
                self.status,
                "White must remove one of the candidate moves before continuing.",
            )

        if not self.board.in_bounds(point):
            return MoveResult(False, self.status, "Move is out of bounds.")

        if not self.board.is_empty(point):
            return MoveResult(False, self.status, "Intersection is already occupied.")

        cell = self.current_cell()
        self.board.place(point, cell)
        forbidden = legal_move(self.board, point, cell)
        if forbidden.is_forbidden:
            self.board.place(point, Cell.EMPTY)
            self.status = GameStatus.WHITE_WON
            self.last_forbidden = (point, forbidden.reason or "forbidden")
            self._finalize_if_complete()
            return MoveResult(
                False,
                self.status,
                f"Forbidden move by Black ({forbidden.reason}). White wins!",
                forbidden=forbidden,
            )

        self.history.append(Move(player=self.current_player, cell=cell, point=point))

        if winner_for_move(self.board, point, cell):
            self.winning_points = list(winning_line(self.board, point, cell))
            self.status = GameStatus.BLACK_WON if cell == Cell.BLACK else GameStatus.WHITE_WON
            self._finalize_if_complete()
            return MoveResult(True, self.status, f"{cell.value} wins!")

        if not any(True for _ in self.board.empty_points()):
            self.status = GameStatus.DRAW
            self._finalize_if_complete()
            return MoveResult(True, self.status, "Game ended in a draw.")

        self.switch_player()
        if len(self.history) == 3 and not self.swap_decided:
            self.swap_available = True
        return MoveResult(True, self.status, "Move accepted.")

    def _finalize_if_complete(self) -> None:
        if self.status != GameStatus.PLAYING and not self.history_saved:
            self.save_history()

    def _new_history_path(self) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        unique_id = uuid4().hex
        filename = f"history_{timestamp}_{unique_id}.log"
        return self.history_dir / filename

    def save_history(self) -> None:
        if self.history_saved:
            return
        moves = []
        for move in self.history:
            moves.append(
                f"{move.player.value}-{move.cell.value}({move.point.row + 1},{move.point.col + 1})"
            )

        summary_lines = [
            f"Result: {self.status.value}",
            f"Moves: {' '.join(moves) if moves else 'none'}",
        ]

        if self.last_forbidden:
            point, reason = self.last_forbidden
            summary_lines.append(
                f"Forbidden: B({point.row + 1},{point.col + 1}) {reason}"
            )

        content = "\n".join(summary_lines) + "\n" + ("-" * 40) + "\n"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("w", encoding="utf-8") as handle:
            handle.write(content)
        self.history_saved = True
