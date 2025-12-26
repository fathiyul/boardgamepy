"""Nim game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import NimGame


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def render_header(game: "NimGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_BLUE}{'=' * 50}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}    NIM GAME{term.RESET}")
    print(f"{term.BOLD}{term.FG_BLUE}{'=' * 50}{term.RESET}\n")


def render_board(game: "NimGame") -> None:
    """Render the board with all piles."""
    print(f"{term.BOLD}Current Board:{term.RESET}\n")

    for i, count in enumerate(game.board.piles, 1):
        # Visual representation
        if count > 0:
            stones = f"{term.FG_YELLOW}{'●' * count}{term.RESET}"
            count_text = f"{term.FG_GREEN}{count}{term.RESET}"
        else:
            stones = f"{term.DIM}(empty){term.RESET}"
            count_text = f"{term.DIM}0{term.RESET}"

        print(f"  {term.BOLD}Pile {i}:{term.RESET} {stones} ({count_text})")

    total = game.board.total_objects()
    print(f"\n{term.BOLD}Total objects remaining: {term.FG_CYAN}{total}{term.RESET}\n")


def render_status(game: "NimGame") -> None:
    """Render current game status."""
    if game.state.is_over:
        print(f"\n{term.BOLD}{term.FG_GREEN}{'=' * 50}{term.RESET}")
        print(f"{term.BOLD}{term.FG_GREEN}Game Over!{term.RESET}")
        print(f"{term.BOLD}{term.FG_YELLOW}Winner: {game.state.winner}{term.RESET}")
        print(f"{term.BOLD}{term.FG_GREEN}{'=' * 50}{term.RESET}\n")
    else:
        current = game.state.current_player
        color = term.FG_BLUE if current == "Player 1" else term.FG_MAGENTA
        print(f"{term.BOLD}{color}Current Player: {current}{term.RESET}\n")


def render_move(
    player: str, pile: int, count: int, reasoning: str | None = None
) -> None:
    """Render a move being made."""
    color = term.FG_BLUE if player == "Player 1" else term.FG_MAGENTA

    print(f"{term.BOLD}{color}[{player}]{term.RESET}")
    print(
        f"  {term.BOLD}Action:{term.RESET} Remove {term.FG_YELLOW}{count}{term.RESET} from Pile {pile}"
    )

    if reasoning:
        print(f"  {term.BOLD}Reasoning:{term.RESET} {term.DIM}{reasoning}{term.RESET}")

    print()


def render_history(game: "NimGame", max_moves: int = 5) -> None:
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
        pile = move["pile"]
        count = move["count"]
        color = term.FG_BLUE if player == "Player 1" else term.FG_MAGENTA

        print(f"  {color}{player}{term.RESET}: Remove {count} from Pile {pile}")

    print()


def refresh(game: "NimGame") -> None:
    """Refresh the entire UI."""
    clear_screen()
    render_header(game)
    render_board(game)
    render_history(game)
    render_status(game)
