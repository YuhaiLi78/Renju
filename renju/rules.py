from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Sequence

from renju.board import Board, Cell, Point

DIRECTIONS = [
    (0, 1),
    (1, 0),
    (1, 1),
    (1, -1),
]


@dataclass(frozen=True)
class LineResult:
    length: int
    points: List[Point]


@dataclass(frozen=True)
class ForbiddenResult:
    is_forbidden: bool
    reason: str | None = None


class RuleSet(str, Enum):
    RENJU = "renju"
    FREESTYLE = "freestyle"


def line_from_point(board: Board, point: Point, dr: int, dc: int, cell: Cell) -> LineResult:
    points: List[Point] = [point]
    length = 1

    row, col = point.row - dr, point.col - dc
    while 0 <= row < board.size and 0 <= col < board.size:
        if board.grid[row][col] != cell:
            break
        points.insert(0, Point(row, col))
        length += 1
        row -= dr
        col -= dc

    row, col = point.row + dr, point.col + dc
    while 0 <= row < board.size and 0 <= col < board.size:
        if board.grid[row][col] != cell:
            break
        points.append(Point(row, col))
        length += 1
        row += dr
        col += dc

    return LineResult(length=length, points=points)


def longest_line(board: Board, point: Point, cell: Cell) -> LineResult:
    best = LineResult(length=1, points=[point])
    for dr, dc in DIRECTIONS:
        current = line_from_point(board, point, dr, dc, cell)
        if current.length > best.length:
            best = current
    return best


def winner_for_move(board: Board, point: Point, cell: Cell, ruleset: RuleSet) -> bool:
    line = longest_line(board, point, cell)
    if ruleset == RuleSet.FREESTYLE:
        return line.length >= 5
    if cell == Cell.WHITE:
        return line.length >= 5
    return line.length == 5


def _axis_string(board: Board, point: Point, dr: int, dc: int) -> str:
    line: List[str] = []
    row, col = point.row, point.col
    while 0 <= row - dr < board.size and 0 <= col - dc < board.size:
        row -= dr
        col -= dc
    while 0 <= row < board.size and 0 <= col < board.size:
        line.append(board.grid[row][col].value)
        row += dr
        col += dc
    return "X" + "".join(line) + "X"


def _count_patterns(line: str, patterns: Sequence[str]) -> int:
    count = 0
    for pattern in patterns:
        start = 0
        while True:
            idx = line.find(pattern, start)
            if idx == -1:
                break
            count += 1
            start = idx + 1
    return count


def _open_three_count(line: str) -> int:
    patterns = [".BBB.", ".BB.B.", ".B.BB."]
    return _count_patterns(line, patterns)


def _open_four_count(line: str) -> int:
    patterns = [".BBBB.", ".BBB.B.", ".BB.BB.", ".B.BBB."]
    return _count_patterns(line, patterns)


def _overline_exists(board: Board, point: Point) -> bool:
    for dr, dc in DIRECTIONS:
        if line_from_point(board, point, dr, dc, Cell.BLACK).length >= 6:
            return True
    return False


def forbidden_move(board: Board, point: Point) -> ForbiddenResult:
    if _overline_exists(board, point):
        return ForbiddenResult(is_forbidden=True, reason="overline")

    open_threes = 0
    open_fours = 0
    for dr, dc in DIRECTIONS:
        line = _axis_string(board, point, dr, dc)
        open_threes += _open_three_count(line)
        open_fours += _open_four_count(line)

    if open_threes >= 2:
        return ForbiddenResult(is_forbidden=True, reason="double-three")
    if open_fours >= 2:
        return ForbiddenResult(is_forbidden=True, reason="double-four")

    return ForbiddenResult(is_forbidden=False, reason=None)


def legal_move(board: Board, point: Point, cell: Cell, ruleset: RuleSet) -> ForbiddenResult:
    if ruleset == RuleSet.FREESTYLE:
        return ForbiddenResult(is_forbidden=False, reason=None)
    if cell == Cell.WHITE:
        return ForbiddenResult(is_forbidden=False, reason=None)
    return forbidden_move(board, point)


def winning_line(board: Board, point: Point, cell: Cell, ruleset: RuleSet) -> Iterable[Point]:
    line = longest_line(board, point, cell)
    if ruleset == RuleSet.FREESTYLE and line.length >= 5:
        return line.points
    if ruleset == RuleSet.RENJU:
        if cell == Cell.WHITE and line.length >= 5:
            return line.points
        if cell == Cell.BLACK and line.length == 5:
            return line.points
    return []
