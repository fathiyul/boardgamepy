"""Game runner for eliminating main.py boilerplate."""

import copy
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from pydantic import BaseModel

from boardgamepy.core.game import Game
from boardgamepy.core.player import Player
from boardgamepy.ai.prompt import PromptBuilder
from boardgamepy.ai.agent import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class GameRunner:
    """
    Runs a board game with AI agents, handling common boilerplate.

    Eliminates repetitive main.py code for:
    - LLM configuration (OpenAI/OpenRouter)
    - AI agent setup for all players
    - Game logging setup
    - Standard game loop
    - Error handling

    Usage for simple games:
        runner = GameRunner(
            game_class=TicTacToeGame,
            prompt_builder_class=TicTacToePromptBuilder,
            output_schema=MoveAction.OutputSchema,
            action_class=MoveAction,
        )
        runner.run()

    For games with custom turn logic, subclass and override run_turn():
        class SplendorRunner(GameRunner):
            def run_turn(self, game, player, game_logger):
                # Custom turn logic
                pass
    """

    def __init__(
        self,
        game_class: type[Game],
        prompt_builder_class: type[PromptBuilder],
        output_schema: type[BaseModel],
        action_class: type | None = None,
        ui_module: Any = None,
        game_dir: Path | None = None,
        turn_delay: float = 1.5,
    ):
        """
        Initialize the game runner.

        Args:
            game_class: The game class to instantiate
            prompt_builder_class: PromptBuilder class for AI prompts
            output_schema: Pydantic model for LLM structured output
            action_class: Action class for simple games (optional)
            ui_module: Module with refresh(), render_move(), etc. (optional)
            game_dir: Directory containing game files (for logging config)
            turn_delay: Delay between turns in seconds
        """
        self.game_class = game_class
        self.prompt_builder_class = prompt_builder_class
        self.output_schema = output_schema
        self.action_class = action_class
        self.ui = ui_module
        self.game_dir = game_dir or Path.cwd()
        self.turn_delay = turn_delay

        # Will be set during run()
        self.game: Game | None = None
        self.game_logger: GameLogger | None = None
        self.logging_config: LoggingConfig | None = None

    def create_llm(self):
        """Create LLM instance based on available API keys."""
        from langchain_openai import ChatOpenAI

        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if openrouter_key:
            return ChatOpenAI(
                model=self.logging_config.openrouter_model,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
            ), self.logging_config.openrouter_model
        elif openai_key:
            return ChatOpenAI(
                model=self.logging_config.openai_model,
                api_key=openai_key,
            ), self.logging_config.openai_model
        else:
            raise ValueError(
                "No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY"
            )

    def setup_ai_agents(self, game: Game) -> None:
        """Configure AI agents for all players."""
        llm, model_name = self.create_llm()
        prompt_builder = self.prompt_builder_class()

        for player in game.players:
            base_agent = LLMAgent(
                llm=llm,
                prompt_builder=prompt_builder,
                output_schema=self.output_schema,
            )
            player.agent = LoggedLLMAgent(base_agent, model_name)

    def get_action_params(self, llm_output: BaseModel) -> dict:
        """
        Extract action parameters from LLM output.

        Override this for custom parameter extraction.
        Default extracts all fields except 'reasoning'.
        """
        params = {}
        for field_name in llm_output.model_fields:
            if field_name != "reasoning":
                params[field_name] = getattr(llm_output, field_name)
        return params

    def render_move_ui(self, game: Game, player: Player, llm_output: BaseModel) -> None:
        """
        Render the move in the UI.

        Override this for custom move rendering.
        Default does nothing - games should override for their specific UI needs.
        """
        pass

    def run_turn(self, game: Game, player: Player, game_logger: GameLogger) -> bool:
        """
        Run a single turn for the given player.

        Override this for custom turn logic.

        Args:
            game: The game instance
            player: Current player
            game_logger: Logger for recording turns

        Returns:
            True if turn was successful, False otherwise
        """
        if self.action_class is None:
            raise ValueError(
                "action_class is required for default run_turn(). "
                "Either provide action_class or override run_turn()."
            )

        # Capture state before
        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board) if hasattr(game, 'board') else None

        # Refresh UI
        if self.ui:
            self.ui.refresh(game)

        # Get action from AI
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            return False

        # Extract parameters
        params = self.get_action_params(llm_output)

        # Render move - games can override render_move_ui() for custom rendering
        self.render_move_ui(game, player, llm_output)

        # Create and validate action
        action = self.action_class()

        if action.validate(game, player, **params):
            action.apply(game, player, **params)

            # Capture state after
            state_after = copy.deepcopy(game.state)
            board_after = copy.deepcopy(game.board) if hasattr(game, 'board') else None

            # Log turn
            if game_logger.enabled:
                llm_call_data = None
                if hasattr(player.agent, '_last_llm_call'):
                    llm_call_data = player.agent._last_llm_call
                    player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=player,
                    state_before=state_before,
                    state_after=state_after,
                    board_before=board_before or "",
                    board_after=board_after or "",
                    action=action,
                    action_params=params,
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )

            return True
        else:
            print(f"Invalid action: {params}")
            time.sleep(2)
            return False

    def run_loop(self, game: Game, game_logger: GameLogger) -> None:
        """
        Run the main game loop.

        Override this for completely custom game loops (e.g., multi-phase games).
        """
        while not game.state.is_terminal():
            current_player = game.get_current_player()
            if current_player is None:
                break

            success = self.run_turn(game, current_player, game_logger)

            if success:
                time.sleep(self.turn_delay)

    def on_game_start(self, game: Game) -> None:
        """Called after game setup, before the loop. Override for custom behavior."""
        pass

    def on_game_end(self, game: Game) -> None:
        """Called after game loop ends. Override for custom end screen."""
        if self.ui and hasattr(self.ui, 'render_game_end'):
            self.ui.render_game_end(game)
        else:
            # Default end message
            if self.ui:
                self.ui.refresh(game)
            print("\n" + "=" * 40)
            winner = game.state.get_winner()
            if winner:
                print(f"Winner: {winner}")
            else:
                print("Game ended in a draw!")
            print("=" * 40 + "\n")

    def run(self, num_players: int | None = None, **game_config) -> None:
        """
        Run the game.

        Args:
            num_players: Number of players (optional)
            **game_config: Additional game configuration
        """
        # Load environment variables from .env file
        load_dotenv(self.game_dir / ".env")
        load_dotenv()  # Also check current directory and parents

        # Load logging configuration
        self.logging_config = LoggingConfig.load(self.game_dir)

        # Create game logger
        self.game_logger = GameLogger(self.logging_config)

        # Create and setup game
        self.game = self.game_class()
        setup_kwargs = game_config.copy()
        if num_players is not None:
            setup_kwargs['num_players'] = num_players
        self.game.setup(**setup_kwargs)

        # Log game start
        if self.game_logger.enabled:
            self.game_logger.start_game(self.game, setup_kwargs)

        # Configure AI agents
        self.setup_ai_agents(self.game)

        # Hook for custom initialization
        self.on_game_start(self.game)

        # Run game loop
        self.run_loop(self.game, self.game_logger)

        # Log game end
        if self.game_logger.enabled:
            self.game_logger.end_game(self.game)

        # End game display
        self.on_game_end(self.game)

    @classmethod
    def main(
        cls,
        game_class: type[Game],
        prompt_builder_class: type[PromptBuilder],
        output_schema: type[BaseModel],
        action_class: type | None = None,
        ui_module: Any = None,
        game_dir: Path | None = None,
        default_num_players: int | None = None,
    ) -> Callable[[], None]:
        """
        Create a main() function for a game.

        Usage in main.py:
            if __name__ == "__main__":
                GameRunner.main(
                    TicTacToeGame,
                    TicTacToePromptBuilder,
                    MoveAction.OutputSchema,
                    MoveAction,
                    ui,
                )()

        Or more simply:
            main = GameRunner.main(TicTacToeGame, TicTacToePromptBuilder, ...)
            if __name__ == "__main__":
                main()
        """
        def main_func():
            # Load environment variables from .env file
            load_dotenv(game_dir / ".env" if game_dir else None)
            load_dotenv()  # Also check current directory and parents

            # Check for API key
            if not os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"):
                print("Error: No API key found!")
                print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
                return

            try:
                runner = cls(
                    game_class=game_class,
                    prompt_builder_class=prompt_builder_class,
                    output_schema=output_schema,
                    action_class=action_class,
                    ui_module=ui_module,
                    game_dir=game_dir or Path.cwd(),
                )
                runner.run(num_players=default_num_players)
            except KeyboardInterrupt:
                print("\n\nGame interrupted by user")
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()

        return main_func
