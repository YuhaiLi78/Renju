from __future__ import annotations

from renju.board import Point
from renju.game import Game, GameStatus


HELP_TEXT = """
Enter moves as: row col (1-15)
Commands:
  help  Show this message
  quit  Exit the game

Opening rules:
  After the 3rd move, White may swap colors.
  On the 5th move, Black places two candidates and White removes one.
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

        if game.swap_available and not game.swap_decided:
            swap_input = input("White may swap colors. Swap? (y/n) > ").strip().lower()
            swap = swap_input in {"y", "yes"}
            print(game.decide_swap(swap))
            continue

        if game.candidate_removal_required:
            user_input = input("White remove one candidate (row col) > ").strip().lower()
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

            result = game.remove_candidate(point)
            print(result.message)
            if result.status == GameStatus.ILLEGAL_MOVE:
                game.status = GameStatus.PLAYING
            continue

        current_cell = game.current_cell().value
        candidate_note = ""
        if game.should_start_candidate_phase() or game.candidate_points:
            candidate_number = len(game.candidate_points) + 1
            candidate_note = f" (candidate {candidate_number} of 2)"
        prompt = f"{game.current_player.value} [{current_cell}] to move{candidate_note} > "
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
