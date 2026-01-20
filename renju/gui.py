from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from renju.board import Cell, Point
from renju.game import Game, GameStatus, Player
from renju.rules import RuleSet


class RenjuGUI:
    def __init__(self, root: tk.Tk, size: int = 15) -> None:
        self.root = root
        self.root.title("Renju")
        self.game = Game(size=size, ruleset=self._choose_ruleset())
        self.size = size
        self.margin = 30
        self.cell_size = 32
        self.stone_radius = 12

        self.status_var = tk.StringVar()
        self.detail_var = tk.StringVar()
        self.message_var = tk.StringVar()

        self._build_layout()
        self._draw_board()
        self._refresh_ui()

    def _choose_ruleset(self) -> RuleSet:
        choice = simpledialog.askstring(
            "Choose Ruleset",
            "Select ruleset: renju or freestyle",
            parent=self.root,
        )
        if choice and choice.strip().lower() == "freestyle":
            return RuleSet.FREESTYLE
        return RuleSet.RENJU

    def _build_layout(self) -> None:
        status_frame = tk.Frame(self.root, padx=10, pady=8)
        status_frame.pack(fill=tk.X)

        status_label = tk.Label(status_frame, textvariable=self.status_var, font=("Arial", 12, "bold"))
        status_label.pack(anchor="w")

        detail_label = tk.Label(status_frame, textvariable=self.detail_var, font=("Arial", 10))
        detail_label.pack(anchor="w")

        message_label = tk.Label(status_frame, textvariable=self.message_var, font=("Arial", 10))
        message_label.pack(anchor="w")

        canvas_size = self.margin * 2 + self.cell_size * (self.size - 1)
        self.canvas = tk.Canvas(self.root, width=canvas_size, height=canvas_size, bg="#f0d9a6")
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._handle_click)

        controls = tk.Frame(self.root, padx=10, pady=8)
        controls.pack(fill=tk.X)

        self.swap_yes_button = tk.Button(
            controls, text="Swap Colors", command=lambda: self._decide_swap(True)
        )
        self.swap_yes_button.pack(side=tk.LEFT)

        self.swap_no_button = tk.Button(
            controls, text="Keep Colors", command=lambda: self._decide_swap(False)
        )
        self.swap_no_button.pack(side=tk.LEFT, padx=(8, 0))

        reset_button = tk.Button(controls, text="New Game", command=self._reset_game)
        reset_button.pack(side=tk.RIGHT)

    def _draw_board(self) -> None:
        self.canvas.delete("all")
        for i in range(self.size):
            offset = self.margin + i * self.cell_size
            self.canvas.create_line(self.margin, offset, self.margin + self.cell_size * (self.size - 1), offset)
            self.canvas.create_line(offset, self.margin, offset, self.margin + self.cell_size * (self.size - 1))

        star_points = [3, 7, 11] if self.size >= 15 else []
        for row in star_points:
            for col in star_points:
                x, y = self._point_to_canvas(Point(row=row, col=col))
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#4a3820", outline="")

    def _refresh_ui(self) -> None:
        self._draw_board()
        self._draw_stones()
        self._update_status()
        self._update_controls()

    def _draw_stones(self) -> None:
        for row in range(self.size):
            for col in range(self.size):
                cell = self.game.board.grid[row][col]
                if cell == Cell.EMPTY:
                    continue
                point = Point(row=row, col=col)
                self._draw_stone(point, cell)

    def _draw_stone(self, point: Point, cell: Cell) -> None:
        x, y = self._point_to_canvas(point)
        color = "#111111" if cell == Cell.BLACK else "#f7f7f7"
        outline = "#444444" if cell == Cell.BLACK else "#aaaaaa"
        if point in self.game.candidate_points and self.game.candidate_removal_required:
            outline = "#1e5fff"
        if point in self.game.winning_points:
            outline = "#d62828"
        self.canvas.create_oval(
            x - self.stone_radius,
            y - self.stone_radius,
            x + self.stone_radius,
            y + self.stone_radius,
            fill=color,
            outline=outline,
            width=2,
        )

    def _update_status(self) -> None:
        if self.game.status != GameStatus.PLAYING:
            if self.game.status == GameStatus.BLACK_WON:
                self.status_var.set("Game over: Black wins!")
            elif self.game.status == GameStatus.WHITE_WON:
                self.status_var.set("Game over: White wins!")
            else:
                self.status_var.set("Game over: Draw.")
            if self.game.winning_points:
                coords = ", ".join(f"({pt.row + 1},{pt.col + 1})" for pt in self.game.winning_points)
                self.detail_var.set(
                    f"Winning line: {coords} | History saved to {self.game.history_path}."
                )
            else:
                self.detail_var.set(f"History saved to {self.game.history_path}.")
            return

        current_cell = self.game.current_cell().value
        self.status_var.set(f"{self.game.current_player.value} [{current_cell}] to move")

        detail_parts = [
            f"Player 1: {self.game.player_colors[Player.ONE].value}",
            f"Player 2: {self.game.player_colors[Player.TWO].value}",
        ]

        if self.game.ruleset == RuleSet.RENJU and self.game.swap_available and not self.game.swap_decided:
            detail_parts.append("White may swap colors after the third move.")

        if self.game.ruleset == RuleSet.RENJU and self.game.candidate_removal_required:
            detail_parts.append("White must remove one candidate move.")
        elif self.game.ruleset == RuleSet.RENJU and (
            self.game.should_start_candidate_phase() or self.game.candidate_points
        ):
            candidate_number = len(self.game.candidate_points) + 1
            detail_parts.append(f"Black to place candidate {candidate_number} of 2.")

        detail_parts.append(f"Ruleset: {self.game.ruleset.value}.")
        self.detail_var.set(" ".join(detail_parts))

    def _update_controls(self) -> None:
        swap_active = (
            self.game.ruleset == RuleSet.RENJU and self.game.swap_available and not self.game.swap_decided
        )
        state = tk.NORMAL if swap_active and self.game.status == GameStatus.PLAYING else tk.DISABLED
        self.swap_yes_button.configure(state=state)
        self.swap_no_button.configure(state=state)

    def _handle_click(self, event: tk.Event) -> None:
        if self.game.status != GameStatus.PLAYING:
            self.message_var.set("Game is over. Start a new game to play again.")
            return

        if self.game.ruleset == RuleSet.RENJU and self.game.swap_available and not self.game.swap_decided:
            self.message_var.set("White must decide whether to swap colors.")
            return

        point = self._canvas_to_point(event.x, event.y)
        if point is None:
            return

        if self.game.ruleset == RuleSet.RENJU and self.game.candidate_removal_required:
            result = self.game.remove_candidate(point)
        else:
            result = self.game.place_move(point)

        self.message_var.set(result.message)
        self._refresh_ui()

        if self.game.status != GameStatus.PLAYING:
            messagebox.showinfo("Game Over", self.status_var.get())

    def _decide_swap(self, swap: bool) -> None:
        message = self.game.decide_swap(swap)
        self.message_var.set(message)
        self._refresh_ui()

    def _reset_game(self) -> None:
        if self.game.status == GameStatus.PLAYING and self.game.history:
            proceed = messagebox.askyesno(
                "Reset Game",
                "The current game is not finished. Start a new game anyway?",
            )
            if not proceed:
                return
        ruleset = self._choose_ruleset()
        self.game.reset(ruleset=ruleset)
        self.message_var.set("New game started.")
        self._refresh_ui()

    def _point_to_canvas(self, point: Point) -> tuple[float, float]:
        x = self.margin + point.col * self.cell_size
        y = self.margin + point.row * self.cell_size
        return x, y

    def _canvas_to_point(self, x: float, y: float) -> Point | None:
        grid_x = round((x - self.margin) / self.cell_size)
        grid_y = round((y - self.margin) / self.cell_size)
        if 0 <= grid_x < self.size and 0 <= grid_y < self.size:
            return Point(row=grid_y, col=grid_x)
        return None


def main() -> None:
    root = tk.Tk()
    RenjuGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
