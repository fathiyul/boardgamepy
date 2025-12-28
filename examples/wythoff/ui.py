"""Wythoff's Game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import WythoffGame



def render_header(game: "WythoffGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_BLUE}{'=' * 60}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}    WYTHOFF'S GAME{term.RESET}")
    print(f"{term.BOLD}{term.FG_BLUE}{'=' * 60}{term.RESET}\n")


def render_board(game: "WythoffGame") -> None:
    """Render both piles."""
    print(f"{term.BOLD}Current Board:{term.RESET}\n")

    # Pile A
    count_a = game.board.pile_a
    if count_a > 0:
        display_a = min(count_a, 40)
        stones_a = f"{term.FG_YELLOW}{'●' * display_a}{term.RESET}"
        if count_a > 40:
            stones_a += f" {term.DIM}(+{count_a - 40} more){term.RESET}"
        count_text_a = f"{term.FG_GREEN}{count_a}{term.RESET}"
    else:
        stones_a = f"{term.DIM}(empty){term.RESET}"
        count_text_a = f"{term.DIM}0{term.RESET}"

    print(f"  {term.BOLD}Pile A:{term.RESET} {stones_a} ({count_text_a})")

    # Pile B
    count_b = game.board.pile_b
    if count_b > 0:
        display_b = min(count_b, 40)
        stones_b = f"{term.FG_CYAN}{'●' * display_b}{term.RESET}"
        if count_b > 40:
            stones_b += f" {term.DIM}(+{count_b - 40} more){term.RESET}"
        count_text_b = f"{term.FG_GREEN}{count_b}{term.RESET}"
    else:
        stones_b = f"{term.DIM}(empty){term.RESET}"
        count_text_b = f"{term.DIM}0{term.RESET}"

    print(f"  {term.BOLD}Pile B:{term.RESET} {stones_b} ({count_text_b})")

    # Total and position hint
    total = game.board.total_objects()
    print(f"\n  {term.BOLD}Total objects: {term.FG_CYAN}{total}{term.RESET}")

    hint = game.board.get_move_type_hint()
    if "losing" in hint:
        print(f"  {term.DIM}💡 {hint}{term.RESET}")
    else:
        print(f"  {term.DIM}💡 {hint}{term.RESET}")

    print()


def render_status(game: "WythoffGame") -> None:
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


def render_move(
    player: str, move_type: str, count: int, reasoning: str | None = None
) -> None:
    """Render a move being made."""
    color = term.FG_BLUE if player == "Player 1" else term.FG_MAGENTA

    # Format move description
    if move_type == "pile_a":
        move_desc = f"Remove {term.FG_YELLOW}{count}{term.RESET} from {term.BOLD}Pile A{term.RESET}"
    elif move_type == "pile_b":
        move_desc = f"Remove {term.FG_CYAN}{count}{term.RESET} from {term.BOLD}Pile B{term.RESET}"
    elif move_type == "both":
        move_desc = f"Remove {term.FG_GREEN}{count}{term.RESET} from {term.BOLD}BOTH piles{term.RESET}"
    else:
        move_desc = f"Remove {count} (unknown move type)"

    print(f"{term.BOLD}{color}[{player}]{term.RESET}")
    print(f"  {term.BOLD}Action:{term.RESET} {move_desc}")

    if reasoning:
        print(f"  {term.BOLD}Reasoning:{term.RESET} {term.DIM}{reasoning}{term.RESET}")

    print()


def render_history(game: "WythoffGame", max_moves: int = 5) -> None:
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
        move_type = move["type"]
        count = move["count"]
        color = term.FG_BLUE if player == "Player 1" else term.FG_MAGENTA

        # Format move description
        if move_type == "remove_a":
            desc = f"A:{count}"
        elif move_type == "remove_b":
            desc = f"B:{count}"
        else:  # remove_both
            desc = f"Both:{count}"

        print(f"  {color}{player}{term.RESET}: {desc}")

    print()


def refresh(game: "WythoffGame") -> None:
    """Refresh the entire UI."""
    term.clear()
    render_header(game)
    render_board(game)
    render_history(game)
    render_status(game)
