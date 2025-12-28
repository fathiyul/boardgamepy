"""Wavelength game state."""

from dataclasses import dataclass
from typing import Literal

from boardgamepy import GameState

Phase = Literal["psychic_clue", "team_guess", "opponent_predict", "reveal"]


@dataclass
class WavelengthState(GameState):
    """State for Wavelength game."""

    current_team: int = 0  # 0 or 1
    psychic_idx: int = 0  # Index within team
    round_number: int = 1
    phase: Phase = "psychic_clue"

    team_scores: dict[int, int] = None  # team_idx -> score
    is_over: bool = False
    winner: int | None = None

    target_score: int = 10  # Points needed to win

    def __post_init__(self):
        if self.team_scores is None:
            self.team_scores = {0: 0, 1: 0}

    def get_winner(self) -> str | None:
        """Get the winner as team name."""
        if self.winner is None:
            return None
        return f"Team {self.winner + 1}"

    def get_current_team_name(self) -> str:
        """Get current team name."""
        return f"Team {self.current_team + 1}"
