"""Subtract-a-Square game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import SubtractASquareBoard
from state import SubtractASquareState
from actions import RemoveAction

if TYPE_CHECKING:
    pass


class SubtractASquareGame(Game):
    """Subtract-a-Square game with a single pile."""

    name = "Subtract-a-Square"
    min_players = 2
    max_players = 2

    def __init__(self):
        """Initialize game."""
        self.board: SubtractASquareBoard
        self.state: SubtractASquareState
        self.history: GameHistory
        self.players: list[Player]

    def setup(self, initial_count: int = 20) -> None:
        """
        Setup Subtract-a-Square game.

        Args:
            initial_count: Starting number of objects in pile (default: 20)
        """
        self.board = SubtractASquareBoard(initial_count)
        self.state = SubtractASquareState()
        self.history = GameHistory()

        # Create players
        self.players = [
            Player(team="Player 1", role="player", agent=None),
            Player(team="Player 2", role="player", agent=None),
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
