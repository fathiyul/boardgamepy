"""Codenames game state."""

from dataclasses import dataclass
from typing import Literal

from boardgamepy import GameState

Team = Literal["Red", "Blue"]


@dataclass
class CodenamesState(GameState):
    """
    State for a Codenames game.

    Tracks current team, remaining agents, and guesses.
    """

    current_team: Team = "Red"
    red_remaining: int = 9
    blue_remaining: int = 8
    guesses_remaining: int = 0
    is_over: bool = False
    winner: Team | None = None
    consecutive_invalid_actions: int = 0  # Track invalid actions to prevent infinite loops
