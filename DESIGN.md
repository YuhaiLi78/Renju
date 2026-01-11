# Renju Game Design

## Overview
Renju is a variant of Gomoku played on a 15x15 grid. Players alternate placing stones, with Black moving first. The goal is to be the first to create a line of exactly five stones. To balance first-move advantage, Black is restricted by forbidden patterns (overlines, double-threes, double-fours). White is unrestricted.

This document specifies rules, data structures, modules, and UI/UX guidelines for a complete Renju game.

## Rules

### Board and Turns
- Board size: 15x15 intersections.
- Players: Black (first) and White (second).
- Each turn places exactly one stone on an empty intersection.

### Win Conditions
- **White** wins by forming a line of five or more stones.
- **Black** wins by forming **exactly** five stones in a line.

### Forbidden Moves (Black Only)
A black move is illegal if it creates any of the following:
- **Overline**: six or more stones in a continuous line.
- **Double-three**: a single move creates two or more *open threes*.
- **Double-four**: a single move creates two or more *open fours*.

#### Pattern Definitions
- **Line**: contiguous stones in any of the 8 directions.
- **Open three**: three stones in a row with two open ends (e.g., _XXX_).
- **Open four**: four stones in a row with two open ends (e.g., _XXXX_).

## Game Flow
1. Initialize empty 15x15 board.
2. Set current player to Black.
3. On a player action:
   - Verify the intersection is empty.
   - Simulate placement and check legality.
   - If legal, place the stone, then check for win.
4. End game when a player wins or no legal moves remain.

## Data Model

### Core Types
- **Point**: `{ row: number, col: number }` (0-indexed).
- **Cell**: `Empty | Black | White`.
- **Board**: `Cell[15][15]`.
- **Player**: `Black | White`.

### Derived Types
- **Line**: list of points from a start point in a direction.
- **PatternMatch**: `{ type: 'openThree' | 'openFour' | 'five' | 'overline', points: Point[] }`.

## Algorithms

### Line Scan
For a given point and direction, walk outward to collect contiguous stones of the same color, including the placed stone. This yields a line length for win detection.

### Win Check
- For White: win if any line length >= 5.
- For Black: win if any line length == 5.

### Forbidden Move Detection (Black)
1. Temporarily place the black stone.
2. Scan all four primary axes (horizontal, vertical, diagonals).
3. Detect:
   - **Overline**: any line length >= 6.
   - **Open threes/fours**: evaluate patterns on each axis using a sliding window around the placed stone.
4. If overline or (count of open threes >= 2) or (count of open fours >= 2), move is illegal.

## UI/UX Design

### Board
- 15x15 grid with coordinate labels.
- Stones rendered with clear contrast: Black (#111) and White (#f5f5f5).
- Hover preview for current player.

### Interactions
- Click/tap to place a stone.
- Invalid moves display a brief message: “Illegal move (double-three).”
- Win state highlights the winning five stones.

### Accessibility
- Keyboard navigation between intersections.
- Announce turn changes and win conditions for screen readers.

## System Architecture

### Modules
- **board/**: core board data model and helpers.
- **rules/**: win and forbidden move detection.
- **game/**: game state, turn logic, and history.
- **ui/**: rendering and user interaction.

### State Management
- Store a history stack of moves for undo/replay.
- Represent game state as:
  - `board: Board`
  - `currentPlayer: Player`
  - `status: 'playing' | 'blackWon' | 'whiteWon' | 'illegalMove' | 'draw'`

## Testing Strategy
- Unit tests for line scan, open three/four detection, and win logic.
- Scenario tests for known Renju positions (double-three, double-four, overline).
- UI tests for move placement and win highlight.

## Future Enhancements
- Opening rules (e.g., Renju standard opening sequences).
- AI opponent with minimax + heuristic evaluation.
- Online multiplayer with spectator mode.
