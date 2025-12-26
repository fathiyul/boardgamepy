"""UI rendering base class."""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from boardgamepy.core.game import Game
    from boardgamepy.core.player import Player
    from boardgamepy.core.action import Action


class UIRenderer(ABC):
    """
    Base class for game UI rendering.

    Provides methods for rendering game state, actions, and results.
    Subclasses implement specific rendering (terminal, web, etc.).
    """

    @abstractmethod
    def render_board(
        self, game: "Game", observer: "Player", **options: Any
    ) -> None:
        """
        Render the game board.

        Should respect information hiding by using board.get_view()
        with the observer's context.

        Args:
            game: Current game instance
            observer: Player viewing the board
            **options: Renderer-specific options
        """
        pass

    @abstractmethod
    def render_state(self, game: "Game", observer: "Player") -> None:
        """
        Render current game state (scores, turn info, etc.).

        Args:
            game: Current game instance
            observer: Player viewing the state
        """
        pass

    @abstractmethod
    def render_action(
        self,
        game: "Game",
        player: "Player",
        action: "Action",
        result: Any,
    ) -> None:
        """
        Render an action and its result.

        Args:
            game: Current game instance
            player: Player who performed the action
            action: Action that was performed
            result: Result of the action
        """
        pass

    @abstractmethod
    def render_game_over(self, game: "Game", winner: Any) -> None:
        """
        Render game over screen.

        Args:
            game: Completed game instance
            winner: Winner of the game
        """
        pass

    def refresh(
        self,
        game: "Game",
        observer: "Player",
        show_history: bool = False,
    ) -> None:
        """
        Full UI refresh (clear and re-render everything).

        Default implementation calls render_state and render_board.
        Override for custom refresh logic.

        Args:
            game: Current game instance
            observer: Player viewing the game
            show_history: Whether to show action history
        """
        self.render_state(game, observer)
        self.render_board(game, observer)
