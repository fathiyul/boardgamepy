"""Wythoff's Game state."""

from dataclasses import dataclass
from typing import Literal

from boardgamepy import GameState

Player = Literal["Player 1", "Player 2"]


@dataclass
class WythoffState(GameState):
    """State for Wythoff's Game."""

    current_player: Player = "Player 1"
    is_over: bool = False
    winner: Player | None = None
