"""Sushi Go! game state."""

from dataclasses import dataclass, field

from boardgamepy import GameState


@dataclass
class SushiGoState(GameState):
    """State for Sushi Go! game."""

    current_round: int = 1
    total_rounds: int = 3  # Standard game is 3 rounds

    # Scores
    round_scores: dict[int, list[int]] = field(default_factory=dict)  # player_idx -> scores per round
    total_scores: dict[int, int] = field(default_factory=dict)  # player_idx -> total score

    is_over: bool = False
    winner: int | None = None

    # Turn tracking within round
    waiting_for_players: set[int] = field(default_factory=set)  # Players who haven't picked yet

    def get_winner(self) -> str | None:
        """Get the winner as player name."""
        if self.winner is None:
            return None
        return f"Player {self.winner + 1}"
