"""Action system for game moves."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from boardgamepy.core.game import Game
    from boardgamepy.core.player import Player

TGame = TypeVar("TGame", bound="Game")


class Action(ABC, Generic[TGame]):
    """
    Base class for all game actions.

    Actions represent things players can do (e.g., move a piece,
    play a card, give a clue). Each action type should:
    1. Define validation rules
    2. Implement state changes when applied
    3. Provide history tracking

    Attributes:
        name: Unique identifier for this action type
        display_name: Human-readable name for UI
        roles: List of player roles that can perform this action
        OutputSchema: Optional Pydantic model for AI structured output
    """

    name: str = ""
    display_name: str = ""
    roles: list[str] = []
    OutputSchema: type[BaseModel] | None = None

    @abstractmethod
    def validate(self, game: TGame, player: "Player", **params: Any) -> bool:
        """
        Validate if this action can be performed in the current state.

        Args:
            game: Current game instance
            player: Player attempting the action
            **params: Action-specific parameters

        Returns:
            True if action is legal, False otherwise
        """
        pass

    @abstractmethod
    def apply(self, game: TGame, player: "Player", **params: Any) -> Any:
        """
        Apply this action to the game state.

        This should:
        1. Modify game state/board
        2. Add to game history
        3. Check win conditions
        4. Advance turn/round if needed

        Args:
            game: Current game instance
            player: Player performing the action
            **params: Action-specific parameters

        Returns:
            Result of the action (game-specific)
        """
        pass

    @abstractmethod
    def to_history_record(self, player: "Player", **params: Any) -> dict[str, Any]:
        """
        Convert action to history record for tracking and prompts.

        Args:
            player: Player who performed the action
            **params: Action-specific parameters

        Returns:
            Dictionary representing this action in history
        """
        pass
