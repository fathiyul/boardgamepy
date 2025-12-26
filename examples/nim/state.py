"""Nim game state."""

from dataclasses import dataclass
from typing import Literal

from boardgamepy import GameState

Player = Literal["Player 1", "Player 2"]


@dataclass
class NimState(GameState):
    """State for a Nim game."""

    current_player: Player = "Player 1"
    is_over: bool = False
    winner: Player | None = None

    def is_terminal(self) -> bool:
        """Check if game is over."""
        return self.is_over

    def get_winner(self) -> Player | None:
        """Get the winner."""
        return self.winner
