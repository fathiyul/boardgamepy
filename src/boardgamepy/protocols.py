"""Core protocols for boardgamepy framework."""

from typing import Protocol, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from boardgamepy.core.state import GameState
    from boardgamepy.core.action import Action
    from boardgamepy.core.game import Game


class ViewContext(Protocol):
    """Protocol for view context - defines the interface."""
    player: "Player"
    game_state: "GameState"


@dataclass
class SimpleViewContext:
    """
    Concrete implementation of ViewContext.

    Use this to create view contexts for board rendering.
    """
    player: "Player"
    game_state: "GameState"


class PlayerAgent(Protocol):
    """Protocol for player agents (human or AI)."""

    def decide(self, game: "Game", player: "Player") -> tuple["Action", dict[str, Any]]:
        """
        Decide which action to take and with what parameters.

        Args:
            game: Current game instance
            player: Player making the decision

        Returns:
            Tuple of (action instance, parameters dict)
        """
        ...
