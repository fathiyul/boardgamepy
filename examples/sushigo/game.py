"""Sushi Go! game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import SushiGoBoard
from state import SushiGoState
from actions import PlayCardAction

if TYPE_CHECKING:
    pass


class SushiGoGame(Game):
    """Sushi Go! card drafting game."""

    name = "Sushi Go!"
    min_players = 2
    max_players = 5

    def __init__(self):
        """Initialize game."""
        self.board: SushiGoBoard
        self.state: SushiGoState
        self.history: GameHistory
        self.players: list[Player]
        self.num_players: int = 0

    def setup(self, num_players: int = 4) -> None:
        """
        Setup Sushi Go! game.

        Args:
            num_players: Number of players (2-5, default 4)
        """
        if num_players < 2 or num_players > 5:
            raise ValueError("Sushi Go! requires 2-5 players")

        self.num_players = num_players
        self.board = SushiGoBoard(num_players)
        self.state = SushiGoState()
        self.history = GameHistory()

        # Initialize scores
        self.state.round_scores = {i: [] for i in range(num_players)}
        self.state.total_scores = {i: 0 for i in range(num_players)}

        # Create players
        self.players = [
            Player(name=f"Player {i + 1}", team=f"Player {i + 1}", role="player", agent=None, player_idx=i)
            for i in range(num_players)
        ]

        # Register actions
        self.actions = [PlayCardAction()]

        # Setup first round
        self.board.setup_round()
        self.state.waiting_for_players = set(range(num_players))

    def get_current_player(self) -> Player:
        """Get next player who needs to play (for simultaneous play simulation)."""
        # In real Sushi Go, players play simultaneously
        # For AI simulation, we'll go in order
        if self.state.waiting_for_players:
            player_idx = min(self.state.waiting_for_players)
            return self.players[player_idx]
        return self.players[0]

    def end_round(self) -> None:
        """End current round and calculate scores."""
        # Calculate round scores
        round_scores = self.board.calculate_round_scores()

        # Update scores
        for player_idx, score in round_scores.items():
            self.state.round_scores[player_idx].append(score)
            self.state.total_scores[player_idx] += score

        # Check if game is over
        if self.state.current_round >= self.state.total_rounds:
            # Add pudding scores
            pudding_scores = self.board.calculate_pudding_scores()
            for player_idx, score in pudding_scores.items():
                self.state.total_scores[player_idx] += score

            # Determine winner
            max_score = max(self.state.total_scores.values())
            winners = [p for p, s in self.state.total_scores.items() if s == max_score]

            self.state.is_over = True
            self.state.winner = winners[0] if len(winners) == 1 else None
        else:
            # Start next round
            self.state.current_round += 1
            self.board.setup_round()
            self.state.waiting_for_players = set(range(self.num_players))
            self.history = GameHistory()  # Clear round history

    def next_turn(self) -> None:
        """Advance to next turn (handled by actions)."""
        pass
