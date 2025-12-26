"""Subtract-a-Square game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import SubtractASquareGame


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def render_header(game: "SubtractASquareGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_BLUE}{'=' * 60}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}    SUBTRACT-A-SQUARE{term.RESET}")
    print(f"{term.BOLD}{term.FG_BLUE}{'=' * 60}{term.RESET}\n")


def render_board(game: "SubtractASquareGame") -> None:
    """Render the pile."""
    count = game.board.count

    print(f"{term.BOLD}Current Pile:{term.RESET}\n")

    # Visual representation
    if count > 0:
        # Show up to 50 stones visually
        display_count = min(count, 50)
        stones = f"{term.FG_YELLOW}{'●' * display_count}{term.RESET}"
        if count > 50:
            stones += f" {term.DIM}(+{count - 50} more){term.RESET}"

        print(f"  {stones}")
        print(f"  {term.BOLD}Count: {term.FG_GREEN}{count}{term.RESET}")
    else:
        print(f"  {term.DIM}(empty){term.RESET}")
        print(f"  {term.BOLD}Count: {term.DIM}0{term.RESET}")

    # Show valid moves
    valid_moves = game.board.get_valid_moves()
    if valid_moves:
        moves_str = ", ".join(f"{term.FG_CYAN}{m}{term.RESET}" for m in valid_moves)
        print(f"\n  {term.BOLD}Valid moves:{term.RESET} {moves_str}")

    print()


def render_status(game: "SubtractASquareGame") -> None:
    """Render current game status."""
    if game.state.is_over:
        print(f"\n{term.BOLD}{term.FG_GREEN}{'=' * 60}{term.RESET}")
        print(f"{term.BOLD}{term.FG_GREEN}Game Over!{term.RESET}")
        print(f"{term.BOLD}{term.FG_YELLOW}Winner: {game.state.winner}{term.RESET}")
        print(f"{term.BOLD}{term.FG_GREEN}{'=' * 60}{term.RESET}\n")
    else:
        current = game.state.current_player
        color = term.FG_BLUE if current == "Player 1" else term.FG_MAGENTA
        print(f"{term.BOLD}{color}Current Player: {current}{term.RESET}\n")


def render_move(player: str, amount: int, reasoning: str | None = None) -> None:
    """Render a move being made."""
    color = term.FG_BLUE if player == "Player 1" else term.FG_MAGENTA

    print(f"{term.BOLD}{color}[{player}]{term.RESET}")
    print(f"  {term.BOLD}Action:{term.RESET} Remove {term.FG_YELLOW}{amount}{term.RESET} objects")

    if reasoning:
        print(f"  {term.BOLD}Reasoning:{term.RESET} {term.DIM}{reasoning}{term.RESET}")

    print()


def render_history(game: "SubtractASquareGame", max_moves: int = 5) -> None:
    """Render recent move history."""
    if not game.history.rounds:
        return

    print(f"{term.BOLD}Recent Moves:{term.RESET}")

    # Collect all actions from recent rounds
    moves = []
    for round_data in reversed(game.history.rounds):
        for action_record in reversed(round_data.actions):
            moves.append(action_record)
            if len(moves) >= max_moves:
                break
        if len(moves) >= max_moves:
            break

    moves = list(reversed(moves))

    for move in moves:
        player = move["player"]
        amount = move["amount"]
        color = term.FG_BLUE if player == "Player 1" else term.FG_MAGENTA

        print(f"  {color}{player}{term.RESET}: Remove {amount}")

    print()


def refresh(game: "SubtractASquareGame") -> None:
    """Refresh the entire UI."""
    clear_screen()
    render_header(game)
    render_board(game)
    render_history(game)
    render_status(game)
