"""Incan Gold game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import IncanGoldBoard
from state import IncanGoldState
from actions import MakeDecisionAction

if TYPE_CHECKING:
    pass


class IncanGoldGame(Game):
    """Incan Gold push-your-luck game."""

    name = "Incan Gold"
    min_players = 3
    max_players = 8

    def __init__(self):
        """Initialize game."""
        self.board: IncanGoldBoard
        self.state: IncanGoldState
        self.history: GameHistory
        self.players: list[Player]
        self.num_players: int = 0

    def setup(self, num_players: int = 4) -> None:
        """
        Setup Incan Gold game.

        Args:
            num_players: Number of players (3-8, default 4)
        """
        if num_players < 3 or num_players > 8:
            raise ValueError("Incan Gold requires 3-8 players")

        self.num_players = num_players
        self.board = IncanGoldBoard(num_players)
        self.state = IncanGoldState()
        self.history = GameHistory()

        # Create players
        self.players = [
            Player(name=f"Player {i + 1}", team=f"Player {i + 1}", role="player", agent=None, player_idx=i)
            for i in range(num_players)
        ]

        # Register actions
        self.actions = [MakeDecisionAction()]

        # Setup first round
        self.board.setup_round()

    def get_current_player(self) -> Player:
        """Get next player who needs to decide."""
        # Find first player in temple who hasn't decided
        for player_idx in self.board.in_temple:
            if player_idx not in self.state.decisions:
                return self.players[player_idx]

        # Default to first player
        return self.players[0]

    def process_decisions(self) -> None:
        """Process all player decisions after everyone has decided."""
        # Separate returners from continuers
        returners = []
        continuers = []

        for player_idx, decision in self.state.decisions.items():
            if decision == "return":
                returners.append(player_idx)
            else:
                continuers.append(player_idx)

        # Update board state
        self.board.returned_this_turn = set(returners)

        # Remove returners from temple
        for player_idx in returners:
            if player_idx in self.board.in_temple:
                self.board.in_temple.remove(player_idx)

        # Clear decisions for next turn
        self.state.decisions = {}

    def end_round(self) -> None:
        """End current round and check for game over."""
        # Check if game is over
        if self.state.current_round >= self.state.total_rounds:
            # Determine winner
            max_score = max(self.board.get_total_score(i) for i in range(self.num_players))
            winners = [i for i in range(self.num_players) if self.board.get_total_score(i) == max_score]

            self.state.is_over = True
            self.state.winner = winners[0] if len(winners) == 1 else None
        else:
            # Start next round
            self.state.current_round += 1
            self.board.setup_round()
            self.state.phase = "decide"
            self.history = GameHistory()

    def next_turn(self) -> None:
        """Advance to next turn (handled by game loop)."""
        pass
