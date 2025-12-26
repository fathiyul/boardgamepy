"""Core game abstraction and loop."""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from boardgamepy.core.state import GameState
    from boardgamepy.core.history import GameHistory
    from boardgamepy.core.action import Action
    from boardgamepy.components.board import Board


class Game(ABC):
    """
    Base class for all board games.

    This is the central class that coordinates all game components.
    Subclasses define game-specific rules and logic.

    Attributes:
        name: Game name for display
        min_players: Minimum number of players
        max_players: Maximum number of players
        state: Current game state
        board: Game board
        history: Action history
        players: List of players
        actions: List of available action types
    """

    # Declarative metadata (set by subclasses)
    name: str = ""
    min_players: int = 2
    max_players: int = 2

    # Game components (initialized in setup)
    state: "GameState"
    board: "Board"
    history: "GameHistory"
    players: list["Player"]
    actions: list[type["Action"]] = []

    @abstractmethod
    def setup(self, **config: Any) -> None:
        """
        Initialize game state, board, and players.

        This method should:
        1. Create and configure the board
        2. Initialize game state
        3. Create players
        4. Initialize history

        Args:
            **config: Game-specific configuration
        """
        pass

    @abstractmethod
    def get_current_player(self) -> "Player":
        """
        Return the player whose turn it is.

        Returns:
            Current player
        """
        pass

    @abstractmethod
    def next_turn(self) -> None:
        """
        Advance to the next turn/phase.

        This should update game state to reflect whose turn it is next.
        May also start a new round if appropriate.
        """
        pass

    def get_valid_actions(self, player: "Player") -> list[type["Action"]]:
        """
        Get all valid action types for player in current state.

        This default implementation filters by player role.
        Override for more complex logic.

        Args:
            player: Player to get actions for

        Returns:
            List of action classes this player can perform
        """
        if not player.role:
            return self.actions

        return [
            action
            for action in self.actions
            if not action.roles or player.role in action.roles
        ]

    def get_player(self, **criteria: Any) -> "Player | None":
        """
        Find a player matching the given criteria.

        Args:
            **criteria: Player attributes to match (e.g., team="Red", role="Spymaster")

        Returns:
            Matching player or None
        """
        for player in self.players:
            if all(
                getattr(player, key, None) == value
                for key, value in criteria.items()
            ):
                return player
        return None

    def run(self) -> Any:
        """
        Main game loop.

        This default implementation:
        1. Runs turns until game is terminal
        2. Each turn: get current player, get their action, apply it
        3. Returns the winner

        Override for custom game loop logic.

        Returns:
            Winner of the game
        """
        while not self.state.is_terminal():
            player = self.get_current_player()

            # Get action from player's agent
            if player.agent is None:
                raise RuntimeError(f"Player {player} has no agent configured")

            action, params = player.agent.decide(self, player)

            # Validate and apply action
            if action.validate(self, player, **params):
                action.apply(self, player, **params)
            else:
                # Handle invalid action - default is to raise error
                # Override this method for different error handling
                raise ValueError(
                    f"Invalid action {action.name} with params {params}"
                )

        return self.state.get_winner()
