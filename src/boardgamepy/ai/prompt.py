"""Prompt building for LLM integration."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from boardgamepy.core.game import Game
    from boardgamepy.core.player import Player

TGame = TypeVar("TGame", bound="Game")


class PromptBuilder(ABC, Generic[TGame]):
    """
    Base class for building LLM prompts.

    Constructs messages that provide the LLM with:
    - Game rules
    - Current board state (filtered for player's role)
    - Game history
    - Current game state
    - Instructions for what to do

    The framework handles role-based information hiding by using
    board.get_prompt_view() with the appropriate player context.
    """

    @abstractmethod
    def build_system_prompt(self) -> str:
        """
        Build system message that defines the LLM's role.

        This typically includes:
        - What game is being played
        - What role the LLM is playing
        - General instructions

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    def build_user_prompt(self, game: TGame, player: "Player") -> str:
        """
        Build user message with current game state and context.

        This typically includes:
        - Game rules
        - Current board state (role-filtered)
        - Game history
        - Current state (scores, counts, etc.)
        - Specific instructions for this turn

        Args:
            game: Current game instance
            player: Player for whom to build the prompt

        Returns:
            User prompt string
        """
        pass

    def build_messages(
        self, game: TGame, player: "Player"
    ) -> list[dict[str, str]]:
        """
        Build complete message list for LLM.

        Combines system and user prompts into the standard format
        expected by LLM APIs.

        Args:
            game: Current game instance
            player: Player for whom to build messages

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
