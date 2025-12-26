"""Board abstraction with role-based views."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class Board(ABC):
    """
    Base class for game boards with role-based information hiding.

    The board maintains the game pieces/state and provides different
    views to different players based on their role (e.g., spymasters
    see hidden information, operatives don't).

    This implements the core information hiding mechanism of the framework.
    """

    @abstractmethod
    def get_view(self, context: "ViewContext") -> str:
        """
        Get text representation of board filtered for specific player/role.

        This method should return different information depending on
        the observer's role. For example:
        - Codenames: Spymasters see card types, Operatives don't
        - Poker: Players see their own cards but not opponents'
        - Chess: Everyone sees the same board (no hidden information)

        Args:
            context: View context containing player and game state

        Returns:
            String representation of board for this observer
        """
        pass

    def get_prompt_view(self, context: "ViewContext") -> str:
        """
        Get board representation optimized for LLM prompts.

        Similar to get_view() but may format information differently
        for better LLM comprehension. Defaults to get_view() if not
        overridden.

        Subclasses can override this to provide LLM-optimized formatting,
        but the default implementation just calls get_view().

        Args:
            context: View context containing player and game state

        Returns:
            String representation optimized for AI consumption
        """
        # Default implementation uses get_view
        return self.get_view(context)
