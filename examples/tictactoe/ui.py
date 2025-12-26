"""Tic-Tac-Toe UI - simple terminal rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import TicTacToeGame


def render_board(game: "TicTacToeGame") -> None:
    """Render the game board with colors."""
    g = game.board.grid

    # Helper to colorize marks
    def colorize_mark(mark: str) -> str:
        if mark == "X":
            return term.colorize(mark, fg=term.FG_BRIGHT_CYAN, bold=True)
        elif mark == "O":
            return term.colorize(mark, fg=term.FG_BRIGHT_MAGENTA, bold=True)
        return mark

    print()
    print(f" {colorize_mark(g[1])} | {colorize_mark(g[2])} | {colorize_mark(g[3])} ")
    print("-----------")
    print(f" {colorize_mark(g[4])} | {colorize_mark(g[5])} | {colorize_mark(g[6])} ")
    print("-----------")
    print(f" {colorize_mark(g[7])} | {colorize_mark(g[8])} | {colorize_mark(g[9])} ")
    print()


def render_status(game: "TicTacToeGame") -> None:
    """Render game status."""
    if game.state.is_over:
        if game.state.winner == "Draw":
            print(f"{term.BOLD}Game Over: DRAW!{term.RESET}")
        else:
            winner_color = (
                term.FG_BRIGHT_CYAN
                if game.state.winner == "X"
                else term.FG_BRIGHT_MAGENTA
            )
            winner_text = term.colorize(
                f"{game.state.winner} WINS!", fg=winner_color, bold=True
            )
            print(f"{term.BOLD}Game Over: {winner_text}{term.RESET}")
    else:
        player = game.state.current_player
        player_color = (
            term.FG_BRIGHT_CYAN if player == "X" else term.FG_BRIGHT_MAGENTA
        )
        player_text = term.colorize(player, fg=player_color, bold=True)
        print(f"Current Player: {player_text}")


def render_move(player: str, position: int, reasoning: str | None = None) -> None:
    """Render a move."""
    player_color = term.FG_BRIGHT_CYAN if player == "X" else term.FG_BRIGHT_MAGENTA
    player_text = term.colorize(player, fg=player_color, bold=True)
    print(f"\n{player_text} → Position {position}")
    if reasoning:
        print(f"{term.DIM}Reasoning: {reasoning}{term.RESET}")


def refresh(game: "TicTacToeGame") -> None:
    """Full UI refresh."""
    term.clear()
    term.render_header("TIC-TAC-TOE")
    print()
    render_status(game)
    render_board(game)
