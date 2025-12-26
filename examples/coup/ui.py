"""Coup game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import CoupGame


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def render_header(game: "CoupGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_RED}{'=' * 60}{term.RESET}")
    print(f"{term.BOLD}{term.FG_YELLOW}    COUP{term.RESET}")
    print(f"{term.BOLD}{term.FG_RED}{'=' * 60}{term.RESET}\n")


def render_board(game: "CoupGame") -> None:
    """Render the game board state."""
    print(f"{term.BOLD}Players:{term.RESET}\n")

    for i in range(game.num_players):
        player_name = f"Player {i + 1}"
        color = _get_player_color(i)

        influence_count = game.board.get_influence_count(i)
        coins = game.board.coins[i]

        # Status
        if influence_count == 0:
            status = f"{term.DIM}[ELIMINATED]{term.RESET}"
        elif influence_count == 1:
            status = f"{term.FG_YELLOW}[1 INFLUENCE]{term.RESET}"
        else:
            status = f"{term.FG_GREEN}[2 INFLUENCE]{term.RESET}"

        # Coins display
        coin_display = "💰" * min(coins, 10)
        if coins > 10:
            coin_display += f"... ({coins})"
        elif coins > 0:
            coin_display += f" ({coins})"
        else:
            coin_display = f"{term.DIM}(no coins){term.RESET}"

        print(f"  {color}{player_name:10}{term.RESET} {status:30} {coin_display}")

        # Revealed cards
        revealed = [card for card in game.board.influence[i] if card.revealed]
        if revealed:
            revealed_str = ", ".join(str(c) for c in revealed)
            print(f"    {term.DIM}Revealed: {revealed_str}{term.RESET}")

    print()


def render_current_turn(game: "CoupGame") -> None:
    """Render current turn information."""
    if game.state.is_over:
        return

    player_idx = game.state.current_player_idx
    color = _get_player_color(player_idx)
    player_name = f"Player {player_idx + 1}"
    coins = game.board.coins[player_idx]

    print(f"{term.BOLD}{color}>>> {player_name}'s Turn{term.RESET}")

    # Show player's influence
    your_cards = game.board.influence[player_idx]
    unrevealed = [card for card in your_cards if not card.revealed]
    if unrevealed:
        cards_str = ", ".join(str(c) for c in unrevealed)
        print(f"{term.BOLD}Your Cards:{term.RESET} {term.FG_CYAN}{cards_str}{term.RESET}")

    print(f"{term.BOLD}Your Coins:{term.RESET} {coins}")

    # Warning if must coup
    if coins >= 10:
        print(f"\n{term.BOLD}{term.FG_RED}⚠️  You MUST Coup (10+ coins)!{term.RESET}")

    print()


def render_move(
    player_name: str,
    action: str,
    target: str | None = None,
    claimed: str | None = None,
    amount: int | None = None,
    reasoning: str | None = None,
) -> None:
    """Render a move being made."""
    player_idx = int(player_name.split()[-1]) - 1
    color = _get_player_color(player_idx)

    print(f"{term.BOLD}{color}[{player_name}]{term.RESET}")

    # Action description
    action_desc = action.upper()
    if claimed:
        action_desc += f" (claims {claimed})"

    print(f"  {term.BOLD}Action:{term.RESET} {term.FG_YELLOW}{action_desc}{term.RESET}")

    if target:
        print(f"  {term.BOLD}Target:{term.RESET} {target}")

    if amount is not None:
        print(f"  {term.BOLD}Amount:{term.RESET} {amount} coins")

    if reasoning:
        print(f"  {term.BOLD}Reasoning:{term.RESET} {term.DIM}{reasoning}{term.RESET}")

    print()


def render_game_end(game: "CoupGame") -> None:
    """Render game end screen."""
    if not game.state.is_over:
        return

    print(f"\n{term.BOLD}{term.FG_GREEN}{'=' * 60}{term.RESET}")
    print(f"{term.BOLD}{term.FG_GREEN}GAME OVER!{term.RESET}")

    if game.state.winner is not None:
        winner_name = f"Player {game.state.winner + 1}"
        winner_cards = [
            card for card in game.board.influence[game.state.winner] if not card.revealed
        ]
        cards_str = ", ".join(str(c) for c in winner_cards)

        print(f"{term.BOLD}{term.FG_YELLOW}🏆 {winner_name} WINS! 🏆{term.RESET}")
        print(f"{term.BOLD}Winning Cards:{term.RESET} {term.FG_CYAN}{cards_str}{term.RESET}")

    print(f"{term.BOLD}{term.FG_GREEN}{'=' * 60}{term.RESET}\n")


def render_history(game: "CoupGame", max_moves: int = 5) -> None:
    """Render recent move history."""
    if not game.history.rounds:
        return

    print(f"{term.BOLD}Recent Actions:{term.RESET}")

    # Collect actions
    moves = []
    for round_data in game.history.rounds:
        for action_record in round_data.actions:
            moves.append(action_record)

    # Show last N moves
    for move in moves[-max_moves:]:
        player = move["player"]
        action_type = move["type"]

        parts = [f"{player}: {action_type}"]

        if "claimed" in move:
            parts.append(f"({move['claimed']})")
        if "target" in move:
            parts.append(f"→ {move['target']}")
        if "amount" in move:
            parts.append(f"({move['amount']} coins)")

        print(f"  {term.DIM}{' '.join(parts)}{term.RESET}")

    print()


def refresh(game: "CoupGame") -> None:
    """Refresh the entire UI."""
    clear_screen()
    render_header(game)
    render_board(game)
    render_history(game)
    render_current_turn(game)


def _get_player_color(player_idx: int) -> str:
    """Get color for player."""
    colors = [
        term.FG_BLUE,
        term.FG_MAGENTA,
        term.FG_GREEN,
        term.FG_CYAN,
        term.FG_YELLOW,
        term.FG_RED,
    ]
    return colors[player_idx % len(colors)]
