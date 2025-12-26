"""AI-specific protocols and types."""

from pydantic import BaseModel, Field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from boardgamepy.core.action import Action


class ActionOutput(BaseModel):
    """
    Base schema for LLM action responses.

    All AI output schemas should include reasoning for transparency
    and debugging.

    Subclasses should add action-specific fields.
    """

    reasoning: str | None = Field(
        None, description="Explanation of decision-making process"
    )

    def to_action(self, player: "Player") -> "Action":
        """
        Convert LLM output to game action.

        This method should be implemented by game-specific output schemas
        to convert the structured LLM response into an executable action.

        Args:
            player: Player performing the action

        Returns:
            Action instance

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            "ActionOutput.to_action() must be implemented by subclass"
        )
