"""Game state abstractions."""

from typing import Any


class GameState:
    """
    Base class for game state.

    Tracks the current state of the game including whose turn it is,
    whether the game is over, and who won.

    Subclasses should add game-specific state fields (e.g., pieces remaining,
    resources, scores, etc.).

    Provides default implementations of is_terminal() and get_winner() that
    simply return the is_over and winner fields. Override these methods if
    you need custom logic (e.g., formatting winner names).
    """

    is_over: bool = False
    winner: Any | None = None

    def is_terminal(self) -> bool:
        """
        Check if the game has reached a terminal state.

        Default implementation returns self.is_over.
        Override if you need custom terminal detection logic.

        Returns:
            True if game is over, False otherwise
        """
        return self.is_over

    def get_winner(self) -> Any | None:
        """
        Get the winner of the game.

        Default implementation returns self.winner.
        Override if you need custom formatting (e.g., "Player 1" instead of 0).

        Returns:
            Winner identifier (e.g., team name, player),
            None if no winner yet or game is a draw
        """
        return self.winner
