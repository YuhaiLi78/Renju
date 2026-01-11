from __future__ import annotations

from renju.board import Point
from renju.game import Game, GameStatus


HELP_TEXT = """
Enter moves as: row col (1-15)
Commands:
  help  Show this message
  quit  Exit the game
""".strip()


def parse_move(text: str) -> Point | None:
    parts = text.strip().split()
    if len(parts) != 2:
        return None
    if not all(part.isdigit() for part in parts):
        return None
    row, col = (int(part) - 1 for part in parts)
    return Point(row=row, col=col)


def main() -> None:
    game = Game()
    print("Renju")
    print(HELP_TEXT)

    while True:
        print("\n" + game.board.render())
        if game.status != GameStatus.PLAYING:
            print(f"\nGame over: {game.status.value}.")
            if game.winning_points:
                coords = ", ".join(
                    f"({pt.row + 1},{pt.col + 1})" for pt in game.winning_points
                )
                print(f"Winning line: {coords}")
            game.save_history()
            print(f"Game history saved to {game.history_path}.")
            break

        prompt = f"{game.current_player.value} to move > "
        user_input = input(prompt).strip().lower()
        if user_input in {"quit", "exit"}:
            print("Goodbye!")
            break
        if user_input in {"help", "?"}:
            print(HELP_TEXT)
            continue

        point = parse_move(user_input)
        if point is None:
            print("Invalid input. Type 'help' for instructions.")
            continue

        result = game.place_move(point)
        print(result.message)
        if result.status == GameStatus.ILLEGAL_MOVE:
            game.status = GameStatus.PLAYING


if __name__ == "__main__":
    main()
