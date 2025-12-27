"""Wavelength game using boardgamepy framework."""

import time
import logging
from pathlib import Path
import copy

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import WavelengthGame
from prompts import PsychicPromptBuilder, GuesserPromptBuilder, OpponentPromptBuilder
from actions import GiveClueAction, GuessPositionAction, PredictDirectionAction
from config import config
import ui

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def setup_ai_agents(game: WavelengthGame, logging_config: LoggingConfig) -> None:
    """Configure AI agents for all players with role-specific prompts."""
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

    # Create prompt builders
    psychic_builder = PsychicPromptBuilder()
    guesser_builder = GuesserPromptBuilder()
    opponent_builder = OpponentPromptBuilder()

    # Configure all players based on their roles
    for player in game.players:
        if player.role == "Psychic":
            base_agent = LLMAgent(
                llm=llm,
                prompt_builder=psychic_builder,
                output_schema=GiveClueAction.OutputSchema,
            )
            player.agent = LoggedLLMAgent(base_agent, model_name)
        elif player.role == "Guesser":
            base_agent = LLMAgent(
                llm=llm,
                prompt_builder=guesser_builder,
                output_schema=GuessPositionAction.OutputSchema,
            )
            player.agent = LoggedLLMAgent(base_agent, model_name)
        elif player.role == "Opponent":
            base_agent = LLMAgent(
                llm=llm,
                prompt_builder=opponent_builder,
                output_schema=PredictDirectionAction.OutputSchema,
            )
            player.agent = LoggedLLMAgent(base_agent, model_name)


def run_game(num_players: int | None = None, target_score: int | None = None) -> None:
    """Run a Wavelength game."""
    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and setup game
    game = WavelengthGame()
    game.setup(num_players=num_players or config.num_players, target_score=target_score)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {
            "num_players": num_players or config.num_players,
            "target_score": game.state.target_score
        })

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    # Game loop
    while not game.state.is_terminal():
        # Re-assign agents when roles change
        setup_ai_agents(game, logging_config)

        current_player = game.get_current_player()
        phase = game.state.phase

        # Capture state and board before
        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        # Refresh UI
        ui.refresh(game)

        # Handle different phases
        if phase == "psychic_clue":
            # Psychic gives clue
            try:
                llm_output = current_player.agent.get_action(game, current_player)
                action = GiveClueAction()

                print(f"{term.BOLD}{term.FG_CYAN}[Psychic]{term.RESET} Giving clue...")
                print(f"  Clue: \"{term.FG_YELLOW}{llm_output.clue}{term.RESET}\"")
                if llm_output.reasoning:
                    print(f"  {term.DIM}Reasoning: {llm_output.reasoning}{term.RESET}")
                print()

                if action.validate(game, current_player, clue=llm_output.clue):
                    action.apply(game, current_player, clue=llm_output.clue)

                    # Capture state and board after
                    state_after = copy.deepcopy(game.state)
                    board_after = copy.deepcopy(game.board)

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
                            board_before=board_before,
                            board_after=board_after,
                            action=action,
                            action_params={"clue": llm_output.clue},
                            action_valid=True,
                            llm_call_data=llm_call_data
                        )
                else:
                    print("⚠️  Invalid clue!")
                    time.sleep(2)
                    continue

            except Exception as e:
                print(f"⚠️  Error: {e}")
                time.sleep(2)
                continue

        elif phase == "team_guess":
            # Team guesses position
            try:
                llm_output = current_player.agent.get_action(game, current_player)
                action = GuessPositionAction()

                print(f"{term.BOLD}{term.FG_CYAN}[Team]{term.RESET} Making guess...")
                print(f"  Position: {term.FG_YELLOW}{llm_output.position}{term.RESET}")
                if llm_output.reasoning:
                    print(f"  {term.DIM}Reasoning: {llm_output.reasoning}{term.RESET}")
                print()

                if action.validate(game, current_player, position=llm_output.position):
                    action.apply(game, current_player, position=llm_output.position)

                    # Capture state and board after
                    state_after = copy.deepcopy(game.state)
                    board_after = copy.deepcopy(game.board)

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
                            board_before=board_before,
                            board_after=board_after,
                            action=action,
                            action_params={"position": llm_output.position},
                            action_valid=True,
                            llm_call_data=llm_call_data
                        )
                else:
                    print("⚠️  Invalid position!")
                    time.sleep(2)
                    continue

            except Exception as e:
                print(f"⚠️  Error: {e}")
                time.sleep(2)
                continue

        elif phase == "opponent_predict":
            # Opponent predicts direction
            try:
                llm_output = current_player.agent.get_action(game, current_player)
                action = PredictDirectionAction()

                print(f"{term.BOLD}{term.FG_CYAN}[Opponent]{term.RESET} Predicting...")
                print(f"  Prediction: {term.FG_YELLOW}{llm_output.prediction.upper()}{term.RESET}")
                if llm_output.reasoning:
                    print(f"  {term.DIM}Reasoning: {llm_output.reasoning}{term.RESET}")
                print()

                if action.validate(game, current_player, prediction=llm_output.prediction):
                    action.apply(game, current_player, prediction=llm_output.prediction)

                    # Capture state and board after
                    state_after = copy.deepcopy(game.state)
                    board_after = copy.deepcopy(game.board)

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
                            board_before=board_before,
                            board_after=board_after,
                            action=action,
                            action_params={"prediction": llm_output.prediction},
                            action_valid=True,
                            llm_call_data=llm_call_data
                        )
                else:
                    print("⚠️  Invalid prediction!")
                    time.sleep(2)
                    continue

            except Exception as e:
                print(f"⚠️  Error: {e}")
                time.sleep(2)
                continue

        elif phase == "reveal":
            # Show result
            ui.refresh(game)
            ui.render_result(game)
            time.sleep(5)

            # Check if game over
            if game.state.is_over:
                break

            # Start new round
            game.start_new_round()

        time.sleep(1.5)

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Game ended
    ui.render_game_end(game)


def main():
    """Main entry point."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Play Wavelength")
    parser.add_argument(
        "--num_players",
        type=int,
        default=None,
        help="Number of players (must be even, 4-12, default: from config)"
    )
    parser.add_argument(
        "--target_score",
        type=int,
        default=None,
        help="Points needed to win (default: 10)"
    )
    args = parser.parse_args()

    if not config.OPENAI_API_KEY and not config.OPENROUTER_API_KEY:
        print("❌ Error: No API key found!")
        print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
        return

    try:
        run_game(num_players=args.num_players, target_score=args.target_score)
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


# Import term for UI
from boardgamepy.ui import terminal as term

if __name__ == "__main__":
    main()
