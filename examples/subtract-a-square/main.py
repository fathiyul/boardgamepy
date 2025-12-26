"""Subtract-a-Square game using boardgamepy framework."""

import time
import logging
from pathlib import Path
import copy

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import SubtractASquareGame
from prompts import SubtractASquarePromptBuilder
from actions import RemoveAction
from config import config
import ui

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def setup_ai_agents(game: SubtractASquareGame, logging_config: LoggingConfig) -> None:
    """Configure AI agents for both players."""
    # Create LLM
    if config.OPENROUTER_API_KEY:
        llm = ChatOpenAI(
            model=logging_config.openrouter_model,
            api_key=config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        model_name = logging_config.openrouter_model
    elif config.OPENAI_API_KEY:
        llm = ChatOpenAI(
            model=logging_config.openai_model,
            api_key=config.OPENAI_API_KEY,
        )
        model_name = logging_config.openai_model
    else:
        raise ValueError("No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY")

    # Configure both players with same prompt builder
    prompt_builder = SubtractASquarePromptBuilder()

    for player in game.players:
        base_agent = LLMAgent(
            llm=llm,
            prompt_builder=prompt_builder,
            output_schema=RemoveAction.OutputSchema,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def run_game(initial_count: int | None = None) -> None:
    """Run a Subtract-a-Square game."""
    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and setup game
    game = SubtractASquareGame()
    game.setup(initial_count=initial_count or config.initial_count)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"initial_count": initial_count or config.initial_count})

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    # Game loop
    while not game.state.is_terminal():
        current_player = game.get_current_player()

        # Capture state before
        state_before = copy.deepcopy(game.state)

        # Refresh UI
        ui.refresh(game)

        # Get move from AI
        llm_output = current_player.agent.get_action(game, current_player)

        # Show the move
        ui.render_move(
            game.state.current_player, llm_output.amount, llm_output.reasoning
        )

        # Create and validate action
        action = RemoveAction()
        amount = llm_output.amount

        if action.validate(game, current_player, amount=amount):
            action.apply(game, current_player, amount=amount)

            # Capture state after
            state_after = copy.deepcopy(game.state)

            # Log turn
            if game_logger.enabled:
                llm_call_data = None
                if hasattr(current_player.agent, '_last_llm_call'):
                    llm_call_data = current_player.agent._last_llm_call
                    current_player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=current_player,
                    state_before=state_before,
                    state_after=state_after,
                    board_before="",
                    board_after="",
                    action=action,
                    action_params={"amount": amount},
                    action_valid=True,
                    llm_call_data=llm_call_data
                )
        else:
            print(f"⚠️  Invalid move: amount {amount}")
            time.sleep(2)
            continue

        # Small delay to see the move
        time.sleep(1.5)

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen
    ui.refresh(game)
    winner = game.state.get_winner()
    print("\n" + "=" * 60)
    print(f"🎉 {winner} wins!")
    print("=" * 60 + "\n")


def main():
    """Main entry point."""

    if not config.OPENAI_API_KEY and not config.OPENROUTER_API_KEY:
        print("❌ Error: No API key found!")
        print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
        return

    try:
        # You can customize the initial count here
        # Default is 20 objects
        run_game(initial_count=config.initial_count)
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
