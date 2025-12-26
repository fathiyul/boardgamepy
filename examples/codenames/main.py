"""Codenames game using boardgamepy framework - demonstration."""

import logging
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import CodenamesGame
from data import load_codenames
from prompts import SpymasterPromptBuilder, OperativesPromptBuilder
from actions import ClueAction, GuessAction, PassAction
from config import config
import ui
import copy

# Setup logging for invalid actions
log_file = Path(__file__).parent / "game_errors.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also print to console
    ]
)

# Suppress HTTP request logging from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def setup_ai_agents(game: CodenamesGame, logging_config: LoggingConfig) -> None:
    """
    Configure AI agents for all players.

    This demonstrates how to use the framework's LLMAgent with
    game-specific prompt builders.
    """
    # Create base LLM
    base_llm = ChatOpenAI(
        model=logging_config.openrouter_model,
        api_key=config.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    model_name = logging_config.openrouter_model

    # Configure Spymaster agents
    for player in game.players:
        if player.role == "Spymaster":
            base_agent = LLMAgent(
                llm=base_llm,
                prompt_builder=SpymasterPromptBuilder(),
                output_schema=ClueAction.OutputSchema,
            )
            player.agent = LoggedLLMAgent(base_agent, model_name)
        elif player.role == "Operatives":
            base_agent = LLMAgent(
                llm=base_llm,
                prompt_builder=OperativesPromptBuilder(),
                output_schema=GuessAction.OutputSchema,
            )
            player.agent = LoggedLLMAgent(base_agent, model_name)


def run_game_with_custom_loop() -> None:
    """
    Run a Codenames game with UI like the original.

    This demonstrates the framework with rich terminal UI.
    """
    # Show log file location
    print(f"📝 Logging errors to: {log_file.absolute()}\n")

    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Load codenames and create game
    codenames = load_codenames()
    game = CodenamesGame()
    game.setup(codenames=codenames)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"codenames_version": "demo"})

    # Configure AI agents with logging
    setup_ai_agents(game, logging_config)

    turn_count = 0

    # Custom game loop with UI
    while not game.state.is_terminal():
        turn_count += 1
        current_player = game.get_current_player()

        # Capture state before action
        state_before = copy.deepcopy(game.state)

        # Determine view mode
        mode = "spymaster" if current_player.role == "Spymaster" else "operatives"

        # Refresh UI to show current state
        ui.refresh(game, mode, show_history=True)

        # Get action from agent
        if current_player.role == "Spymaster":
            # Spymaster gives clue
            action_class = ClueAction
            llm_output = current_player.agent.get_action(game, current_player)
            params = {"clue": llm_output.clue, "count": llm_output.count}

            # Show clue with color
            clue_colored = ui.term.colorize(
                f"{llm_output.clue} (Count: {llm_output.count})",
                fg=ui._team_fg(current_player.team)
            )
            ui.render_message(current_player.team, "Spymaster", clue_colored)
            ui.render_reasoning(llm_output.reasoning)

        else:  # Operatives
            # Operatives guess or pass
            llm_output = current_player.agent.get_action(game, current_player)

            if llm_output.action == "pass":
                action_class = PassAction
                params = {}
                ui.render_message(current_player.team, "Operatives", "PASS")
            else:
                action_class = GuessAction
                params = {"codename": llm_output.codename}

            ui.render_reasoning(llm_output.reasoning)

        # Create action instance and validate
        action = action_class()

        if action.validate(game, current_player, **params):
            # VALID ACTION - apply it
            result = action.apply(game, current_player, **params)

            # Capture state after action
            state_after = copy.deepcopy(game.state)

            # Log turn to MongoDB
            if game_logger.enabled:
                llm_call_data = None
                if hasattr(current_player.agent, '_last_llm_call'):
                    llm_call_data = current_player.agent._last_llm_call
                    current_player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=current_player,
                    state_before=state_before,
                    state_after=state_after,
                    board_before="",  # Codenames has complex board visualization
                    board_after="",
                    action=action,
                    action_params=params,
                    action_valid=True,
                    llm_call_data=llm_call_data
                )

            # Reset invalid action counter on success
            game.state.consecutive_invalid_actions = 0

            # Show result for guesses
            if action_class == GuessAction and result:
                ui.render_guess_result(current_player.team, params["codename"], result)

        else:
            # INVALID ACTION - log and track it
            game.state.consecutive_invalid_actions += 1

            # Create detailed error message
            error_details = (
                f"Team: {current_player.team}, "
                f"Role: {current_player.role}, "
                f"Action: {action.name}, "
                f"Params: {params}, "
                f"Consecutive invalid: {game.state.consecutive_invalid_actions}"
            )

            # Log to file and console
            logger.error(f"INVALID ACTION - {error_details}")

            # Show persistent error message (won't be cleared immediately)
            ui.render_message(
                current_player.team,
                current_player.role,
                f"⚠ Invalid action! (Strike {game.state.consecutive_invalid_actions}/3)",
                kind="warn"
            )
            print(f"  Details: {params}")  # Extra detail line

            # Check for 3-strikes rule
            if game.state.consecutive_invalid_actions >= 3:
                logger.error(f"3 CONSECUTIVE INVALID ACTIONS - {current_player.team} LOSES")
                game.state.is_over = True
                game.state.winner = "Blue" if current_player.team == "Red" else "Red"
                ui.render_message(
                    None,
                    "PENALTY",
                    f"{current_player.team} made 3 consecutive invalid actions and loses!",
                    kind="error"
                )
                break

            # Longer delay for invalid actions so user can see the error
            import time
            time.sleep(2.0)

        # Small delay to see actions
        import time
        time.sleep(0.3)

        # Safety limit
        if turn_count > 100:
            ui.render_message(None, "GAME", "Turn limit reached, ending game", kind="warn")
            break

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen and summary
    ui.refresh(game, "operatives", show_history=True)
    if game.state.get_winner():
        ui.render_message(
            None,
            "GAME OVER",
            f"Winner: {game.state.get_winner()}",
            kind="success"
        )
    else:
        ui.render_message(None, "GAME OVER", "No winner", kind="info")


def main():
    """Main entry point."""
    try:
        run_game_with_custom_loop()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
