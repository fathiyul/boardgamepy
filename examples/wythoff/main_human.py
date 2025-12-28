"""Wythoff's Game with human player."""

import copy
import time
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import WythoffGame
from prompts import WythoffPromptBuilder
from actions import RemoveFromAAction, RemoveFromBAction, RemoveFromBothAction
from human_agent import WythoffHumanAgent
import ui

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()


def setup_players(game: WythoffGame, logging_config: LoggingConfig) -> tuple[str, str]:
    """
    Configure players - ask user which player they want to be.

    Returns:
        tuple: (player_team, player_name)
    """
    print("\n" + "=" * 60)
    print("WYTHOFF'S GAME")
    print("=" * 60)

    # Get player name
    player_name = input("\nEnter your name: ").strip()
    if not player_name:
        player_name = "You"

    print(f"\nWelcome, {player_name}!")
    print("Do you want to go first or second?\n")

    while True:
        choice = input("Choose: (1) Go first or (2) Go second? ").strip()
        if choice in ["1"]:
            human_player = "Player 1"
            break
        elif choice in ["2"]:
            human_player = "Player 2"
            break
        print("Please enter '1' to go first or '2' to go second")

    print(f"\nYou will play as {human_player} ({player_name})")
    print("The other player will be AI\n")

    # Check for API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise ValueError("OPENROUTER_API_KEY is required")

    # AI player uses per-player model config
    model = logging_config.default_model
    base_llm = ChatOpenAI(
        model=model,
        api_key=openrouter_key,
        base_url="https://openrouter.ai/api/v1",
    )

    # Configure players
    for player in game.players:
        if player.team == human_player:
            player.agent = WythoffHumanAgent()
            player.agent_type = "human"
            player.name = player_name
        else:
            base_agent = LLMAgent(
                llm=base_llm,
                prompt_builder=WythoffPromptBuilder(),
                output_schema=RemoveFromAAction.OutputSchema,
            )
            player.agent = LoggedLLMAgent(base_agent, model)
            player.agent_type = "ai"
            player.name = logging_config.get_short_model_name(model)

    print("=" * 60)
    input("Press Enter to start the game...")
    print("\n")

    return human_player, player_name


def run_game():
    """Run Wythoff's Game with human and AI players."""

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    game = WythoffGame()
    game.setup()

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    human_player, player_name = setup_players(game, logging_config)

    turn_count = 0

    # Main game loop
    while not game.state.is_terminal():
        turn_count += 1
        current_player = game.get_current_player()

        # Capture state before
        state_before = copy.deepcopy(game.state)

        # Refresh UI
        ui.refresh(game)

        # Show player type
        player_type = (
            "YOUR TURN" if current_player.agent_type == "human" else "AI THINKING..."
        )
        print(f"\n[{player_type}]\n")

        # Get action
        try:
            llm_output = current_player.agent.get_action(game, current_player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            continue

        # Render move
        ui.render_move(
            game.state.current_player,
            llm_output.move_type,
            llm_output.count,
            llm_output.reasoning,
        )

        # Select action class
        if llm_output.move_type == "pile_a":
            action = RemoveFromAAction()
        elif llm_output.move_type == "pile_b":
            action = RemoveFromBAction()
        else:
            action = RemoveFromBothAction()

        if action.validate(game, current_player, count=llm_output.count):
            action.apply(game, current_player, count=llm_output.count)

            state_after = copy.deepcopy(game.state)

            if game_logger.enabled:
                llm_call_data = None
                if hasattr(current_player.agent, "_last_llm_call"):
                    llm_call_data = current_player.agent._last_llm_call
                    current_player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=current_player,
                    state_before=state_before,
                    state_after=state_after,
                    board_before="",
                    board_after="",
                    action=action,
                    action_params={
                        "move_type": llm_output.move_type,
                        "count": llm_output.count,
                    },
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )
        else:
            print(f"Invalid move: {llm_output.move_type} with count {llm_output.count}")
            time.sleep(2)
            continue

        # Delay between turns
        if current_player.agent_type == "ai":
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
    ui.render_status(game)


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
