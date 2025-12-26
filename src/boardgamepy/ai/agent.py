"""AI agent implementations."""

from typing import TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from boardgamepy.core.game import Game
    from boardgamepy.core.player import Player
    from boardgamepy.ai.prompt import PromptBuilder


class LLMAgent:
    """
    Agent that uses a Large Language Model for decision making.

    This agent:
    1. Uses a PromptBuilder to construct context-aware prompts
    2. Calls an LLM with structured output
    3. Returns the LLM's decision

    Designed to work with langchain's ChatOpenAI and structured output.
    """

    def __init__(
        self,
        llm: any,  # ChatOpenAI instance
        prompt_builder: "PromptBuilder",
        output_schema: type[BaseModel],
    ):
        """
        Initialize LLM agent.

        Args:
            llm: Language model instance (e.g., ChatOpenAI)
            prompt_builder: Prompt builder for constructing messages
            output_schema: Pydantic model for structured output
        """
        self.llm = llm
        self.prompt_builder = prompt_builder
        self.output_schema = output_schema
        self._structured_llm = llm.with_structured_output(output_schema, strict=True)

    def get_action(self, game: "Game", player: "Player") -> BaseModel:
        """
        Get action decision from LLM.

        Args:
            game: Current game instance
            player: Player making the decision

        Returns:
            Structured output from LLM matching output_schema
        """
        messages = self.prompt_builder.build_messages(game, player)
        return self._structured_llm.invoke(messages)

    def decide(self, game: "Game", player: "Player") -> tuple:
        """
        Decide which action to take (PlayerAgent protocol).

        This is a convenience method that can be used when LLMAgent
        is used directly as a PlayerAgent. For more complex scenarios,
        wrap LLMAgent in a game-specific agent class.

        Args:
            game: Current game instance
            player: Player making the decision

        Returns:
            Tuple of (action, params) - implementation depends on game

        Raises:
            NotImplementedError: This is a simple implementation
        """
        raise NotImplementedError(
            "LLMAgent.decide() is a placeholder. "
            "Use get_action() directly or wrap in game-specific agent."
        )
