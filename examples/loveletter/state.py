"""Love Letter game state."""

from dataclasses import dataclass, field

from boardgamepy import GameState


@dataclass
class LoveLetterState(GameState):
    """State for Love Letter game."""

    current_player_idx: int = 0  # Index of current player (0-based)
    round_number: int = 1
    scores: dict[int, int] = field(default_factory=dict)  # player_idx -> tokens won
    is_over: bool = False
    winner: int | None = None  # Player index of game winner
    target_tokens: int = 4  # Tokens needed to win (varies by player count)

    # Round state
    round_over: bool = False
    round_winner: int | None = None

    def is_terminal(self) -> bool:
        """Check if game is over."""
        return self.is_over

    def get_winner(self) -> str | None:
        """Get the winner as player name."""
        if self.winner is None:
            return None
        return f"Player {self.winner + 1}"

    def get_current_player_name(self) -> str:
        """Get current player name."""
        return f"Player {self.current_player_idx + 1}"
