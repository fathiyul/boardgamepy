"""Wythoff's Game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import WythoffBoard
from state import WythoffState
from actions import RemoveFromAAction, RemoveFromBAction, RemoveFromBothAction

if TYPE_CHECKING:
    pass


class WythoffGame(Game):
    """Wythoff's Game with two piles."""

    name = "Wythoff's Game"
    min_players = 2
    max_players = 2

    def __init__(self):
        """Initialize game."""
        self.board: WythoffBoard
        self.state: WythoffState
        self.history: GameHistory
        self.players: list[Player]

    def setup(self, pile_a: int = 8, pile_b: int = 13) -> None:
        """
        Setup Wythoff's Game.

        Args:
            pile_a: Initial count for pile A (default: 8)
            pile_b: Initial count for pile B (default: 13)
        """
        self.board = WythoffBoard(pile_a, pile_b)
        self.state = WythoffState()
        self.history = GameHistory()

        # Create players
        self.players = [
            Player(name="Player 1", team="Player 1", role="player", agent=None),
            Player(name="Player 2", team="Player 2", role="player", agent=None),
        ]

        # Register actions
        self.actions = [RemoveFromAAction(), RemoveFromBAction(), RemoveFromBothAction()]

    def get_current_player(self) -> Player:
        """Get current player."""
        if self.state.current_player == "Player 1":
            return self.players[0]
        return self.players[1]

    def next_turn(self) -> None:
        """Advance to next turn (handled by action.apply)."""
        pass
