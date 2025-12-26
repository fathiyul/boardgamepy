"""Wavelength game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import WavelengthBoard
from state import WavelengthState
from actions import GiveClueAction, GuessPositionAction, PredictDirectionAction

if TYPE_CHECKING:
    pass


class WavelengthGame(Game):
    """Wavelength party game."""

    name = "Wavelength"
    min_players = 4  # 2 teams of 2
    max_players = 12  # 2 teams of 6

    def __init__(self):
        """Initialize game."""
        self.board: WavelengthBoard
        self.state: WavelengthState
        self.history: GameHistory
        self.players: list[Player]
        self.teams: dict[int, list[Player]]  # team_idx -> list of players
        self.num_players: int = 0

    def setup(self, num_players: int = 4, target_score: int | None = None) -> None:
        """
        Setup Wavelength game.

        Args:
            num_players: Number of players (must be even, 4-12)
            target_score: Points needed to win (default: 10)
        """
        if num_players < 4 or num_players > 12 or num_players % 2 != 0:
            raise ValueError("Wavelength requires even number of players (4-12)")

        self.num_players = num_players
        self.board = WavelengthBoard()
        self.state = WavelengthState()
        self.history = GameHistory()

        # Set target score if provided
        if target_score is not None:
            self.state.target_score = target_score

        # Create players and divide into teams
        self.players = [
            Player(team=f"Team {(i % 2) + 1}", role="player", agent=None)
            for i in range(num_players)
        ]

        # Organize teams
        self.teams = {
            0: [p for p in self.players if p.team == "Team 1"],
            1: [p for p in self.players if p.team == "Team 2"],
        }

        # Register actions
        self.actions = [GiveClueAction(), GuessPositionAction(), PredictDirectionAction()]

        # Setup first round
        self.board.setup_round()
        self._assign_roles()

    def _assign_roles(self) -> None:
        """Assign roles for current round."""
        current_team = self.state.current_team
        opponent_team = 1 - current_team

        # Reset all roles
        for player in self.players:
            player.role = "player"

        # Assign Psychic to current team
        psychic = self.teams[current_team][self.state.psychic_idx]
        psychic.role = "Psychic"

        # Assign Guessers to rest of current team
        for i, player in enumerate(self.teams[current_team]):
            if i != self.state.psychic_idx:
                player.role = "Guesser"

        # Assign Opponents to other team
        for player in self.teams[opponent_team]:
            player.role = "Opponent"

    def get_current_player(self) -> Player:
        """Get current player based on phase."""
        if self.state.phase == "psychic_clue":
            # Psychic's turn
            return self.teams[self.state.current_team][self.state.psychic_idx]

        elif self.state.phase == "team_guess":
            # Any guesser from current team (we'll pick first)
            guessers = [p for p in self.teams[self.state.current_team] if p.role == "Guesser"]
            return guessers[0] if guessers else self.teams[self.state.current_team][0]

        elif self.state.phase == "opponent_predict":
            # Any opponent (we'll pick first from other team)
            opponent_team = 1 - self.state.current_team
            return self.teams[opponent_team][0]

        # Default to first player
        return self.players[0]

    def start_new_round(self) -> None:
        """Start a new round."""
        # Switch teams
        self.state.current_team = 1 - self.state.current_team

        # Rotate psychic within new team
        team_size = len(self.teams[self.state.current_team])
        self.state.psychic_idx = (self.state.psychic_idx + 1) % team_size

        # Setup new round
        self.state.round_number += 1
        self.state.phase = "psychic_clue"
        self.board.setup_round()
        self._assign_roles()
        self.history = GameHistory()  # Clear round history

    def next_turn(self) -> None:
        """Advance to next turn (handled by actions)."""
        pass
