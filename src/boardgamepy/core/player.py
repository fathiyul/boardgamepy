"""Player and agent implementations."""

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from boardgamepy.core.game import Game
    from boardgamepy.core.action import Action
    from boardgamepy.protocols import PlayerAgent


@dataclass
class Player:
    """
    Represents a player in the game.

    Attributes:
        team: Team identifier (game-specific, e.g., "Red"/"Blue", "White"/"Black")
        role: Role identifier (game-specific, e.g., "Spymaster"/"Operatives", "Player")
        agent: Agent controlling this player (human or AI)
        agent_type: Type of agent ("human" or "ai")
        name: Optional player name for display
        player_idx: Zero-based player index for direct access
    """

    team: str | None = None
    role: str | None = None
    agent: "PlayerAgent | None" = None
    agent_type: str = "ai"
    name: str | None = None
    player_idx: int | None = None

    def __post_init__(self):
        """Initialize agent if not provided."""
        if self.agent is None:
            if self.agent_type == "human":
                self.agent = HumanAgent()
            else:
                self.agent = AIAgent()


class HumanAgent:
    """
    Base agent for human players.

    This is a simple implementation that should be extended
    or replaced with game-specific human input handling.
    """

    def decide(self, game: "Game", player: Player) -> tuple["Action", dict[str, Any]]:
        """
        Get action decision from human player.

        This base implementation raises NotImplementedError.
        Games should provide their own human input handling.

        Args:
            game: Current game instance
            player: Player making the decision

        Returns:
            Tuple of (action instance, parameters dict)

        Raises:
            NotImplementedError: This base implementation must be overridden
        """
        raise NotImplementedError(
            "HumanAgent.decide() must be implemented by game-specific agent or UI"
        )


class AIAgent:
    """
    Base agent for AI players.

    This is a simple placeholder that should be extended
    with actual AI logic (e.g., using LLMAgent from boardgamepy.ai).
    """

    def decide(self, game: "Game", player: Player) -> tuple["Action", dict[str, Any]]:
        """
        Get action decision from AI player.

        This base implementation raises NotImplementedError.
        Games should configure actual AI agents (e.g., LLMAgent).

        Args:
            game: Current game instance
            player: Player making the decision

        Returns:
            Tuple of (action instance, parameters dict)

        Raises:
            NotImplementedError: This base implementation must be overridden
        """
        raise NotImplementedError(
            "AIAgent.decide() must be implemented or replaced with LLMAgent"
        )
