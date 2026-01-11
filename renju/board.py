from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional


class Cell(str, Enum):
    EMPTY = "."
    BLACK = "B"
    WHITE = "W"


@dataclass(frozen=True)
class Point:
    row: int
    col: int


BoardGrid = List[List[Cell]]


class Board:
    size: int
    grid: BoardGrid

    def __init__(self, size: int = 15) -> None:
        self.size = size
        self.grid = [[Cell.EMPTY for _ in range(size)] for _ in range(size)]

    def in_bounds(self, point: Point) -> bool:
        return 0 <= point.row < self.size and 0 <= point.col < self.size

    def get(self, point: Point) -> Cell:
        return self.grid[point.row][point.col]

    def place(self, point: Point, cell: Cell) -> None:
        self.grid[point.row][point.col] = cell

    def is_empty(self, point: Point) -> bool:
        return self.get(point) == Cell.EMPTY

    def iter_line(self, point: Point, dr: int, dc: int) -> Iterable[Point]:
        row = point.row
        col = point.col
        while 0 <= row < self.size and 0 <= col < self.size:
            yield Point(row, col)
            row += dr
            col += dc

    def to_lines(self) -> List[str]:
        header = "   " + " ".join(f"{i:2d}" for i in range(1, self.size + 1))
        lines = [header]
        for idx, row in enumerate(self.grid, start=1):
            row_str = " ".join(cell.value for cell in row)
            lines.append(f"{idx:2d} {row_str}")
        return lines

    def render(self) -> str:
        return "\n".join(self.to_lines())

    def empty_points(self) -> Iterable[Point]:
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == Cell.EMPTY:
                    yield Point(r, c)

    def last_move_point(self, history: List[Point]) -> Optional[Point]:
        if not history:
            return None
        return history[-1]
