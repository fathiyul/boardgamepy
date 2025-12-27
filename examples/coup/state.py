"""Coup game state."""

from dataclasses import dataclass, field
from typing import Literal

from boardgamepy import GameState

ActionType = Literal[
    "income",
    "foreign_aid",
    "coup",
    "tax",
    "assassinate",
    "steal",
    "exchange",
]


@dataclass
class CoupState(GameState):
    """State for Coup game."""

    current_player_idx: int = 0
    is_over: bool = False
    winner: int | None = None
    consecutive_invalid_actions: int = 0  # Track invalid actions to prevent infinite loops

    # Pending action state (for challenge/block resolution)
    pending_action: ActionType | None = None
    pending_target: int | None = None
    pending_claimed_character: str | None = None
    action_resolved: bool = True  # False when waiting for challenges/blocks

    def is_terminal(self) -> bool:
        """Check if game is over."""
        return self.is_over

    def get_winner(self) -> str | None:
        """Get the winner as player name."""
        if self.winner is None:
            return None
        return f"Player {self.winner + 1}"

    def get_current_player_name(self) -> str:
        """Get current player name."""
        return f"Player {self.current_player_idx + 1}"
