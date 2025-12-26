"""Game state abstractions."""

from abc import ABC, abstractmethod
from typing import Any


class GameState(ABC):
    """
    Base class for game state.

    Tracks the current state of the game including whose turn it is,
    whether the game is over, and who won.

    Subclasses should add game-specific state fields (e.g., pieces remaining,
    resources, scores, etc.).
    """

    is_over: bool = False
    winner: Any | None = None

    @abstractmethod
    def is_terminal(self) -> bool:
        """
        Check if the game has reached a terminal state.

        Returns:
            True if game is over, False otherwise
        """
        pass

    @abstractmethod
    def get_winner(self) -> Any | None:
        """
        Get the winner of the game.

        Returns:
            Winner identifier (e.g., team name, player),
            None if no winner yet or game is a draw
        """
        pass
