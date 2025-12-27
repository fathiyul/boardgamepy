"""Nim game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import NimBoard
from state import NimState
from actions import RemoveAction

if TYPE_CHECKING:
    pass


class NimGame(Game):
    """Nim game with multiple piles."""

    name = "Nim"
    min_players = 2
    max_players = 2

    def __init__(self):
        """Initialize game."""
        self.board: NimBoard
        self.state: NimState
        self.history: GameHistory
        self.players: list[Player]

    def setup(self, piles: list[int] | None = None) -> None:
        """
        Setup Nim game.

        Args:
            piles: List of pile sizes. Defaults to [3, 5, 7] (classic Nim)
        """
        if piles is None:
            piles = [3, 5, 7]

        self.board = NimBoard(piles)
        self.state = NimState()
        self.history = GameHistory()

        # Create players
        self.players = [
            Player(name="Player 1", team="Player 1", role="player", agent=None),
            Player(name="Player 2", team="Player 2", role="player", agent=None),
        ]

        # Register actions
        self.actions = [RemoveAction()]

    def get_current_player(self) -> Player:
        """Get current player."""
        if self.state.current_player == "Player 1":
            return self.players[0]
        return self.players[1]

    def next_turn(self) -> None:
        """Advance to next turn (handled by RemoveAction.apply)."""
        pass
