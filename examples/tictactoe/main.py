"""Tic-Tac-Toe game using boardgamepy framework."""

import time
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import TicTacToeGame
from prompts import TicTacToePromptBuilder
from actions import MoveAction
from config import Config
import ui
import copy

# Use environment variable or default
API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")


def setup_ai_agents(game: TicTacToeGame, config: LoggingConfig) -> None:
    """Configure AI agents for both players."""
    # Create LLM
    if os.getenv("OPENROUTER_API_KEY"):
        llm = ChatOpenAI(
            model=config.openrouter_model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        model_name = config.openrouter_model
    else:
        llm = ChatOpenAI(
            model=config.openai_model,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        model_name = config.openai_model

    # Configure both players with same prompt builder
    prompt_builder = TicTacToePromptBuilder()

    for player in game.players:
        base_agent = LLMAgent(
            llm=llm,
            prompt_builder=prompt_builder,
            output_schema=MoveAction.OutputSchema,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def run_game() -> None:
    """Run a Tic-Tac-Toe game."""
    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    logger = GameLogger(logging_config)

    # Create and setup game
    game = TicTacToeGame()
    game.setup()

    # Log game start
    if logger.enabled:
        logger.start_game(game, {})

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    # Game loop with logging
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
            game.state.current_player, llm_output.position, llm_output.reasoning
        )

        # Create and validate action
        action = MoveAction()
        position = llm_output.position

        if action.validate(game, current_player, position=position):
            action.apply(game, current_player, position=position)

            # Capture state after
            state_after = copy.deepcopy(game.state)

            # Log turn
            if logger.enabled:
                llm_call_data = None
                if hasattr(current_player.agent, '_last_llm_call'):
                    llm_call_data = current_player.agent._last_llm_call
                    current_player.agent._last_llm_call = None

                logger.log_turn(
                    player=current_player,
                    state_before=state_before,
                    state_after=state_after,
                    board_before="",  # TicTacToe renders board via UI
                    board_after="",
                    action=action,
                    action_params={"position": position},
                    action_valid=True,
                    llm_call_data=llm_call_data
                )
        else:
            print(f"⚠️  Invalid move: position {position}")
            time.sleep(2)
            continue

        # Small delay to see the move
        time.sleep(1.5)

    # Log game end
    if logger.enabled:
        logger.end_game(game)

    # Final screen
    ui.refresh(game)
    print("\n" + "=" * 40)
    if game.state.winner == "Draw":
        print("Game ended in a DRAW!")
    else:
        print(f"Winner: {game.state.winner}")
    print("=" * 40 + "\n")


def main():
    """Main entry point."""
    if not API_KEY:
        print("❌ Error: No API key found!")
        print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
        return

    try:
        run_game()
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
