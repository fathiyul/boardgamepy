"""Strategic Rock Paper Scissors with human player."""

import copy
import os
import time
from pathlib import Path

import ui
from actions import StrategyChooseAction
from dotenv import load_dotenv
from human_agent import RPSHumanAgent
from langchain_openai import ChatOpenAI
from prompts_strategy import StrategyRPSPromptBuilder
from strategy_game import StrategyRPSGame

from boardgamepy.ai import LLMAgent
from boardgamepy.logging import GameLogger, LoggedLLMAgent, LoggingConfig

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()


def setup_game(game: StrategyRPSGame, logging_config: LoggingConfig) -> str:
    """Configure game and get player name."""
    print("\n" + "=" * 60)
    print("STRATEGIC ROCK PAPER SCISSORS")
    print("=" * 60)

    # Get player name
    player_name = input("\nEnter your name: ").strip()
    if not player_name:
        player_name = "You"

    print(f"\nWelcome, {player_name}!")
    print("You will play against an AI opponent.\n")

    # Create LLM for AI player
    if os.getenv("OPENROUTER_API_KEY"):
        base_llm = ChatOpenAI(
            model=logging_config.openrouter_model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        model_name = logging_config.openrouter_model
    else:
        base_llm = ChatOpenAI(
            model=logging_config.openai_model,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        model_name = logging_config.openai_model

    # Player 1 = Human, Player 2 = AI
    game.players[0].agent = RPSHumanAgent()
    game.players[0].agent_type = "human"
    game.players[0].name = player_name

    base_agent = LLMAgent(
        llm=base_llm,
        prompt_builder=StrategyRPSPromptBuilder(),
        output_schema=StrategyChooseAction.OutputSchema,
    )
    game.players[1].agent = LoggedLLMAgent(base_agent, model_name)
    game.players[1].agent_type = "ai"
    game.players[1].name = "AI"

    print("=" * 60)
    input("Press Enter to start the game...")
    print("\n")

    return player_name


def run_game():
    """Run Strategic RPS with human and AI players."""

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    game = StrategyRPSGame()
    game.setup()

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    player_name = setup_game(game, logging_config)

    turn_count = 0

    # Main game loop
    while not game.state.is_terminal():
        turn_count += 1
        player = game.get_current_player()

        if player is None:
            continue

        # Refresh UI (show scores, history)
        ui.refresh(game)

        # Get action
        action = StrategyChooseAction()
        board_before = copy.deepcopy(game.board)

        if player.agent_type == "human":
            print(f"\n>>> YOUR TURN ({player_name}) <<<\n")
        else:
            print(f"\n[AI] AI is thinking...\n")

        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            continue

        # Show choice (for AI, show after the fact)
        if player.agent_type == "ai":
            ui.render_ai_choice(llm_output.choice, llm_output.reasoning)

        if action.validate(game, player, choice=llm_output.choice):
            action.apply(game, player, choice=llm_output.choice)

            board_after = copy.deepcopy(game.board)

            if game_logger.enabled:
                llm_call_data = None
                if hasattr(player.agent, "_last_llm_call"):
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
                    llm_call_data=llm_call_data,
                )
        else:
            print("Invalid choice!")
            time.sleep(2)
            continue

        # Delay between turns
        if player.agent_type == "ai":
            time.sleep(1.0)
        else:
            time.sleep(0.3)

        # Safety limit
        if turn_count > 100:
            print("Turn limit reached!")
            break

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen
    ui.refresh(game)
    ui.render_game_over(game)


def main():
    """Main entry point."""
    try:
        run_game()
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
