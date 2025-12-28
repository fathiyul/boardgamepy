"""Splendor game state."""

from dataclasses import dataclass, field
from cards import Noble

from boardgamepy import GameState


@dataclass
class SplendorState(GameState):
    """State for Splendor game."""

    current_player_idx: int = 0
    round_number: int = 0  # Track rounds for debugging

    # Track nobles claimed by each player
    player_nobles: dict[int, list[Noble]] = field(default_factory=dict)

    # Game end tracking
    is_over: bool = False
    winner: int | None = None
    final_round_triggered: bool = False  # Someone reached 15 points
    turns_in_final_round: int = 0

    def get_winner(self) -> str | None:
        """Get the winner as player name."""
        if self.winner is None:
            return None
        return f"Player {self.winner + 1}"
