"""Wythoff's Game using boardgamepy framework."""

import time
import logging
from pathlib import Path
import copy

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import WythoffGame
from prompts import WythoffPromptBuilder
from actions import RemoveFromAAction, RemoveFromBAction, RemoveFromBothAction
from config import config
import ui

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def setup_ai_agents(game: WythoffGame, logging_config: LoggingConfig) -> None:
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
    prompt_builder = WythoffPromptBuilder()

    for player in game.players:
        base_agent = LLMAgent(
            llm=llm,
            prompt_builder=prompt_builder,
            output_schema=RemoveFromAAction.OutputSchema,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def run_game(pile_a: int | None = None, pile_b: int | None = None) -> None:
    """Run a Wythoff's Game."""
    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and setup game
    game = WythoffGame()
    game.setup(
        pile_a=pile_a or config.pile_a,
        pile_b=pile_b or config.pile_b,
    )

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"pile_a": pile_a or config.pile_a, "pile_b": pile_b or config.pile_b})

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
            game.state.current_player,
            llm_output.move_type,
            llm_output.count,
            llm_output.reasoning,
        )

        # Select and execute appropriate action
        move_type = llm_output.move_type
        count = llm_output.count

        if move_type == "pile_a":
            action = RemoveFromAAction()
        elif move_type == "pile_b":
            action = RemoveFromBAction()
        elif move_type == "both":
            action = RemoveFromBothAction()
        else:
            print(f"⚠️  Invalid move type: {move_type}")
            time.sleep(2)
            continue

        if action.validate(game, current_player, count=count):
            action.apply(game, current_player, count=count)

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
                    action_params={"move_type": move_type, "count": count},
                    action_valid=True,
                    llm_call_data=llm_call_data
                )
        else:
            print(f"⚠️  Invalid move: {move_type} with count {count}")
            time.sleep(2)
            continue

        # Small delay to see the move
        time.sleep(1.5)

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen
    ui.refresh(game)
    print("\n" + "=" * 60)
    print(f"🎉 {game.state.winner} wins!")
    print("=" * 60 + "\n")


def main():
    """Main entry point."""

    if not config.OPENAI_API_KEY and not config.OPENROUTER_API_KEY:
        print("❌ Error: No API key found!")
        print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
        return

    try:
        # You can customize the pile sizes here
        # Default is (8, 13) which is a P-position (losing position)
        # Try (5, 8), (10, 16), or (7, 12) for different scenarios
        run_game(pile_a=config.pile_a, pile_b=config.pile_b)
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
