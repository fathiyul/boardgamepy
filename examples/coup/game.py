"""Coup game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import CoupBoard
from state import CoupState
from actions import TakeTurnAction

if TYPE_CHECKING:
    pass


class CoupGame(Game):
    """Coup bluffing card game."""

    name = "Coup"
    min_players = 2
    max_players = 6

    def __init__(self):
        """Initialize game."""
        self.board: CoupBoard
        self.state: CoupState
        self.history: GameHistory
        self.players: list[Player]
        self.num_players: int = 0

    def setup(self, num_players: int = 2) -> None:
        """
        Setup Coup game.

        Args:
            num_players: Number of players (2-6)
        """
        if num_players < 2 or num_players > 6:
            raise ValueError("Coup requires 2-6 players")

        self.num_players = num_players
        self.board = CoupBoard(num_players)
        self.state = CoupState()
        self.history = GameHistory()

        # Create players
        self.players = [
            Player(name=f"Player {i + 1}", team=f"Player {i + 1}", role="player", agent=None)
            for i in range(num_players)
        ]

        # Register actions
        self.actions = [TakeTurnAction()]

        # Setup game board
        self.board.setup_game()

    def get_current_player(self) -> Player:
        """Get current player."""
        return self.players[self.state.current_player_idx]

    def next_turn(self) -> None:
        """Advance to next turn (handled by action.apply)."""
        pass
