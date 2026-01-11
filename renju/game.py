from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

from renju.board import Board, Cell, Point
from renju.rules import ForbiddenResult, legal_move, winner_for_move, winning_line


class GameStatus(str, Enum):
    PLAYING = "playing"
    BLACK_WON = "blackWon"
    WHITE_WON = "whiteWon"
    ILLEGAL_MOVE = "illegalMove"
    DRAW = "draw"


@dataclass
class MoveResult:
    success: bool
    status: GameStatus
    message: str
    forbidden: Optional[ForbiddenResult] = None
    winning_points: List[Point] = field(default_factory=list)


class Game:
    def __init__(self, size: int = 15, history_path: str | Path = "history.log") -> None:
        self.board = Board(size=size)
        self.current_player = Cell.BLACK
        self.status = GameStatus.PLAYING
        self.history: List[Point] = []
        self.winning_points: List[Point] = []
        self.history_path = Path(history_path)
        self.last_forbidden: Optional[tuple[Point, str]] = None

    def reset(self) -> None:
        self.board = Board(size=self.board.size)
        self.current_player = Cell.BLACK
        self.status = GameStatus.PLAYING
        self.history.clear()
        self.winning_points.clear()
        self.last_forbidden = None

    def switch_player(self) -> None:
        self.current_player = Cell.WHITE if self.current_player == Cell.BLACK else Cell.BLACK

    def place_move(self, point: Point) -> MoveResult:
        if self.status != GameStatus.PLAYING:
            return MoveResult(False, self.status, "Game is already over.")

        if not self.board.in_bounds(point):
            return MoveResult(False, self.status, "Move is out of bounds.")

        if not self.board.is_empty(point):
            return MoveResult(False, self.status, "Intersection is already occupied.")

        self.board.place(point, self.current_player)
        forbidden = legal_move(self.board, point, self.current_player)
        if forbidden.is_forbidden:
            self.board.place(point, Cell.EMPTY)
            self.status = GameStatus.WHITE_WON
            self.last_forbidden = (point, forbidden.reason or "forbidden")
            return MoveResult(
                False,
                self.status,
                f"Forbidden move by Black ({forbidden.reason}). White wins!",
                forbidden=forbidden,
            )

        self.history.append(point)

        if winner_for_move(self.board, point, self.current_player):
            self.winning_points = list(winning_line(self.board, point, self.current_player))
            if self.current_player == Cell.BLACK:
                self.status = GameStatus.BLACK_WON
            else:
                self.status = GameStatus.WHITE_WON
            return MoveResult(True, self.status, f"{self.current_player.value} wins!")

        if not any(True for _ in self.board.empty_points()):
            self.status = GameStatus.DRAW
            return MoveResult(True, self.status, "Game ended in a draw.")

        self.switch_player()
        return MoveResult(True, self.status, "Move accepted.")

    def save_history(self) -> None:
        moves = []
        for idx, point in enumerate(self.history):
            player = Cell.BLACK if idx % 2 == 0 else Cell.WHITE
            moves.append(f"{player.value}({point.row + 1},{point.col + 1})")

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
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(content)
