"""Incan Gold game state."""

from dataclasses import dataclass, field
from typing import Literal

from boardgamepy import GameState

Phase = Literal["decide", "reveal", "resolve"]


@dataclass
class IncanGoldState(GameState):
    """State for Incan Gold game."""

    current_round: int = 1
    total_rounds: int = 5

    phase: Phase = "decide"  # decide (continue/return), reveal (card), resolve (distribute)

    # Decisions
    decisions: dict[int, str] = field(default_factory=dict)  # player_idx -> "continue" or "return"

    is_over: bool = False
    winner: int | None = None

    def is_terminal(self) -> bool:
        """Check if game is over."""
        return self.is_over

    def get_winner(self) -> str | None:
        """Get the winner as player name."""
        if self.winner is None:
            return None
        return f"Player {self.winner + 1}"
