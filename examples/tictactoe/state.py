"""Tic-Tac-Toe game state."""

from dataclasses import dataclass
from typing import Literal

from boardgamepy import GameState

Player = Literal["X", "O"]


@dataclass
class TicTacToeState(GameState):
    """State for a Tic-Tac-Toe game."""

    current_player: Player = "X"
    is_over: bool = False
    winner: Player | Literal["Draw"] | None = None

    def is_terminal(self) -> bool:
        """Check if game is over."""
        return self.is_over

    def get_winner(self) -> Player | Literal["Draw"] | None:
        """Get the winner or draw."""
        return self.winner
