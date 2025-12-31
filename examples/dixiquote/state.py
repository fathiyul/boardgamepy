"""DixiQuote game state."""

from dataclasses import dataclass, field
from typing import Literal

from boardgamepy import GameState

Phase = Literal["choose_situation", "give_quote", "submit_situations", "vote", "scoring", "round_end"]


@dataclass
class DixiQuoteState(GameState):
    """
    State for a DixiQuote game.

    Tracks the current phase, storyteller, submissions, votes, and scores.
    """

    # Phase tracking
    phase: Phase = "choose_situation"

    # Current round
    round_number: int = 1
    storyteller_idx: int = 0

    # Storyteller's choice
    storyteller_situation: str | None = None
    storyteller_quote: str | None = None

    # Submissions from other players
    # Dict mapping player_idx to situation card text
    submitted_situations: dict[int, str] = field(default_factory=dict)

    # Votes
    # Dict mapping player_idx to the situation they voted for
    votes: dict[int, str] = field(default_factory=dict)

    # Scores
    # Dict mapping player_idx to their total score
    scores: dict[int, int] = field(default_factory=dict)

    # Game end settings
    target_score: int = 20  # Score to win
    max_rounds: int = 15  # Maximum rounds

    # Game end state
    is_over: bool = False
    winner_idx: int | None = None

    # Invalid action tracking (resets each phase)
    consecutive_invalid_actions: int = 0
    skipped_players: set[int] = field(default_factory=set)  # Players who got penalized this round

    def reset_round(self) -> None:
        """Reset state for a new round."""
        self.phase = "choose_situation"
        self.storyteller_situation = None
        self.storyteller_quote = None
        self.submitted_situations.clear()
        self.votes.clear()
        self.skipped_players.clear()
        self.consecutive_invalid_actions = 0

    def get_all_submitted_situations(self) -> list[str]:
        """
        Get all submitted situations including the storyteller's, shuffled.

        Returns:
            List of situation strings in random order.
        """
        import random

        all_situations = list(self.submitted_situations.values())
        if self.storyteller_situation:
            all_situations.append(self.storyteller_situation)

        # Shuffle to hide which is the storyteller's
        random.shuffle(all_situations)
        return all_situations

    def is_terminal(self) -> bool:
        """
        Check if game is over.

        Game ends if:
        - A player reaches target_score, OR
        - max_rounds is reached
        """
        return self.is_over

    def get_winner(self) -> int | None:
        """Get the winner's player index."""
        return self.winner_idx

    def check_win_conditions(self) -> bool:
        """
        Check if win conditions are met.

        Returns True if game should end.
        """
        # Check if any player reached target score
        if self.scores:
            max_score = max(self.scores.values())
            if max_score >= self.target_score:
                return True

        # Check if max rounds reached
        if self.round_number > self.max_rounds:
            return True

        return False
