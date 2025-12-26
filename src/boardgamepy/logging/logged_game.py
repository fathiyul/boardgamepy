"""Wrapper that adds logging to any Game instance."""

from typing import Any, Optional
from pathlib import Path
import copy

from ..core.game import Game
from ..protocols import SimpleViewContext
from .game_logger import GameLogger
from .config import LoggingConfig


class LoggedGame:
    """
    Wrapper that adds logging to any Game instance.

    Uses composition pattern to avoid modifying Game base class.
    Intercepts setup() and run() to capture complete game lifecycle.
    """

    def __init__(self, game: Game, game_dir: Optional[Path] = None):
        """
        Wrap a game with logging.

        Args:
            game: Game instance to wrap
            game_dir: Optional game directory for loading local .env
        """
        self.game = game
        self.config = LoggingConfig.load(game_dir)
        self.logger = GameLogger(self.config)

    def setup(self, **config: Any) -> None:
        """
        Setup game with logging.

        Args:
            **config: Configuration parameters for game setup
        """
        # Call original setup
        self.game.setup(**config)

        # Log game start
        if self.logger.enabled:
            self.logger.start_game(self.game, config)

    def run(self) -> Any:
        """
        Run game loop with logging at each turn.

        Returns:
            Winner of the game

        Raises:
            RuntimeError: If player has no agent configured
            ValueError: If invalid action is attempted
        """
        try:
            while not self.game.state.is_terminal():
                player = self.game.get_current_player()

                # Capture state before
                state_before = copy.deepcopy(self.game.state)
                context = SimpleViewContext(player=player, game_state=self.game.state)
                board_before = self.game.board.get_view(context) if hasattr(self.game, 'board') else "N/A"

                # Get action from agent
                if player.agent is None:
                    raise RuntimeError(f"Player {player} has no agent configured")

                # Track LLM call if using LoggedLLMAgent
                llm_call_data = None
                action, params = player.agent.decide(self.game, player)

                # Check if agent has captured LLM data
                if hasattr(player.agent, '_last_llm_call'):
                    llm_call_data = player.agent._last_llm_call
                    player.agent._last_llm_call = None  # Clear for next turn

                # Validate action
                action_valid = action.validate(self.game, player, **params)

                if action_valid:
                    # Apply action
                    action.apply(self.game, player, **params)
                else:
                    raise ValueError(f"Invalid action {action.name} with params {params}")

                # Capture state after
                state_after = copy.deepcopy(self.game.state)
                context_after = SimpleViewContext(player=player, game_state=self.game.state)
                board_after = self.game.board.get_view(context_after) if hasattr(self.game, 'board') else "N/A"

                # Log turn
                if self.logger.enabled:
                    self.logger.log_turn(
                        player=player,
                        state_before=state_before,
                        state_after=state_after,
                        board_before=board_before,
                        board_after=board_after,
                        action=action,
                        action_params=params,
                        action_valid=action_valid,
                        llm_call_data=llm_call_data
                    )

            # Game ended
            winner = self.game.state.get_winner()

            if self.logger.enabled:
                self.logger.end_game(self.game)

            return winner

        except Exception as e:
            # Log error and re-raise
            if self.logger.enabled:
                self.logger.end_game(self.game)
            raise

    def __getattr__(self, name):
        """Delegate all other attributes to wrapped game."""
        return getattr(self.game, name)
