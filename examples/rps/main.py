"""Run Strategic Rock Paper Scissors with AI players."""

import logging
from pathlib import Path
import time

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger

from strategy_game import StrategyRPSGame
from prompts_strategy import StrategyRPSPromptBuilder
from actions import StrategyChooseAction
from config import config
import ui

# Setup logging
log_file = Path(__file__).parent / "game_errors.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def setup_ai_agents(game: StrategyRPSGame, logging_config: LoggingConfig) -> None:
    """Configure AI agents for both players."""
    # Create base LLM
    base_llm = ChatOpenAI(
        model=logging_config.openrouter_model,
        api_key=config.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    model_name = logging_config.openrouter_model

    # Configure AI agents for both players
    for player in game.players:
        base_agent = LLMAgent(
            llm=base_llm,
            prompt_builder=StrategyRPSPromptBuilder(),
            output_schema=StrategyChooseAction.OutputSchema,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def main():
    """Main game loop for AI vs AI Strategic Rock Paper Scissors."""
    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and initialize the game
    game = StrategyRPSGame()
    game.setup()

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "ai_vs_ai_strategic"})

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    turn_count = 0

    # Main game loop
    while not game.state.is_terminal():
        turn_count += 1
        player = game.get_current_player()

        # If no current player, both have chosen, move to next round
        if player is None:
            continue

        # Refresh UI
        ui.refresh(game)

        # Show player's turn
        player_num = 1 if player == game.players[0] else 2
        ui.render_turn_prompt(player.name, player_num)

        # Get action from AI agent
        action = game.actions[0]  # StrategyChooseAction
        llm_output = player.agent.get_action(game, player)

        # Show AI choice and reasoning
        ui.render_ai_choice(llm_output.choice, llm_output.reasoning)

        # Validate and apply
        if action.validate(game, player, llm_output.choice):
            # Capture board before applying action (to log round effects)
            import copy
            board_before = copy.deepcopy(game.board)

            action.apply(game, player, llm_output.choice)

            # Capture board after action
            board_after = copy.deepcopy(game.board)

            # Log to MongoDB if enabled
            if game_logger.enabled:
                llm_call_data = None
                if hasattr(player.agent, '_last_llm_call'):
                    llm_call_data = player.agent._last_llm_call
                    player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=player,
                    state_before=game.state,
                    state_after=game.state,
                    board_before=board_before,
                    board_after=board_after,
                    action=action,
                    action_params={"choice": llm_output.choice},
                    action_valid=True,
                    llm_call_data=llm_call_data
                )
        else:
            print(f"   ⚠ Invalid choice!")
            logger.error(f"Invalid action from {player.name}: {llm_output.choice}")

        # Small delay for readability
        time.sleep(1)

        # Safety limit
        if turn_count > 100:
            print("\n⚠ Turn limit reached!")
            break

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final refresh and game over screen
    ui.refresh(game)
    ui.render_game_over(game)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
