"""Codenames game with human players."""

import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import CodenamesGame
from data import load_codenames
from prompts import SpymasterPromptBuilder, OperativesPromptBuilder
from actions import ClueAction, GuessAction, PassAction
from human_agent import CodenamesHumanAgent
import ui
import os
import copy

# Setup logging for invalid actions
log_file = Path(__file__).parent / "game_errors.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def setup_players(
    game: CodenamesGame, logging_config: LoggingConfig
) -> tuple[str, str]:
    """
    Configure players - ask user which role they want to play.
    All other roles will be AI.

    Returns:
        tuple[str, str]: (team, role) of the human player
    """
    print("\n" + "=" * 60)
    print("PLAYER CONFIGURATION")
    print("=" * 60)

    # Ask for player name
    human_name = input("\nEnter your name: ").strip()
    if not human_name:
        human_name = "Human"

    print("\nWhich player do you want to be?\n")

    # Ask for team
    while True:
        team_choice = input("Choose your team - (r)ed or (b)lue? ").strip().lower()
        if team_choice in ["r", "red"]:
            human_team = "Red"
            break
        elif team_choice in ["b", "blue"]:
            human_team = "Blue"
            break
        print("Please enter 'r' for Red or 'b' for Blue")

    # Ask for role
    while True:
        role_choice = (
            input("Choose your role - (s)pymaster or (o)peratives? ").strip().lower()
        )
        if role_choice in ["s", "spymaster"]:
            human_role = "Spymaster"
            break
        elif role_choice in ["o", "operatives"]:
            human_role = "Operatives"
            break
        print("Please enter 's' for Spymaster or 'o' for Operatives")

    print(f"\n✓ You ({human_name}) will play as {human_team} {human_role}")
    print(f"✓ All other players will be AI\n")

    # Check for API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise ValueError("OPENROUTER_API_KEY is required")

    # Configure each player with per-player models
    for i, player in enumerate(game.players):
        if player.team == human_team and player.role == human_role:
            # This is the human player
            player.agent = CodenamesHumanAgent()
            player.agent_type = "human"
            player.name = human_name
        else:
            # AI player - use per-player model
            model = logging_config.get_model_for_player(i)
            short_name = logging_config.get_short_model_name(model)
            llm = ChatOpenAI(
                model=model,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
            )

            if player.role == "Spymaster":
                base_agent = LLMAgent(
                    llm=llm,
                    prompt_builder=SpymasterPromptBuilder(),
                    output_schema=ClueAction.OutputSchema,
                )
            else:  # Operatives
                base_agent = LLMAgent(
                    llm=llm,
                    prompt_builder=OperativesPromptBuilder(),
                    output_schema=GuessAction.OutputSchema,
                )
            player.agent = LoggedLLMAgent(base_agent, model)
            player.agent_type = "ai"
            player.name = short_name

    print("=" * 60)
    input("Press Enter to start the game...")
    print("\n")

    return human_team, human_role


def run_game():
    """Run a Codenames game with human and/or AI players."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "CODENAMES - HUMAN PLAYABLE" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print(f"\n📝 Logging errors to: {log_file.absolute()}\n")

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    codenames = load_codenames()
    game = CodenamesGame()
    game.setup(codenames=codenames)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    human_team, human_role = setup_players(game, logging_config)

    turn_count = 0

    # Main game loop
    while not game.state.is_terminal():
        turn_count += 1
        current_player = game.get_current_player()

        # Capture state before action
        state_before = copy.deepcopy(game.state)

        # Determine view mode based on human player's role
        # If human is playing operatives, they should never see card colors
        if human_role == "Operatives":
            # Human operative should always see operatives view (no colors)
            mode = "operatives"
        else:
            # Human is spymaster, show appropriate view for current turn
            mode = "spymaster" if current_player.role == "Spymaster" else "operatives"

        # Refresh UI to show current state
        ui.refresh(game, mode, show_history=True)

        # Show player type indicator
        player_type = "HUMAN" if current_player.agent_type == "human" else "AI"
        ui.render_message(
            current_player.team,
            current_player.role,
            f"[{player_type} PLAYER]",
            kind="info",
        )

        # Get action from agent (human or AI)
        if current_player.role == "Spymaster":
            # Spymaster gives clue
            action_class = ClueAction
            llm_output = current_player.agent.get_action(game, current_player)
            params = {"clue": llm_output.clue, "count": llm_output.count}

            # Show clue with color
            clue_colored = ui.term.colorize(
                f"{llm_output.clue} (Count: {llm_output.count})",
                fg=ui._team_fg(current_player.team),
            )
            ui.render_message(current_player.team, "Spymaster", clue_colored)
            if llm_output.reasoning:
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

            if llm_output.reasoning:
                ui.render_reasoning(llm_output.reasoning)

        # Create action instance and validate
        action = action_class()

        if action.validate(game, current_player, **params):
            # VALID ACTION - apply it
            result = action.apply(game, current_player, **params)

            # Capture state after action
            state_after = copy.deepcopy(game.state)

            # Log turn to MongoDB
            # Note: Codenames is deterministic - initial_board + actions = full replay
            if game_logger.enabled:
                llm_call_data = None
                if hasattr(current_player.agent, "_last_llm_call"):
                    llm_call_data = current_player.agent._last_llm_call
                    current_player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=current_player,
                    state_before=state_before,
                    state_after=state_after,
                    board_before=None,
                    board_after=None,
                    action=action,
                    action_params=params,
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )

            # Reset invalid action counter
            game.state.consecutive_invalid_actions = 0

            # Show result for guesses
            if action_class == GuessAction and result:
                ui.render_guess_result(current_player.team, params["codename"], result)

        else:
            # INVALID ACTION
            game.state.consecutive_invalid_actions += 1

            error_details = (
                f"Team: {current_player.team}, "
                f"Role: {current_player.role}, "
                f"Action: {action.name}, "
                f"Params: {params}, "
                f"Consecutive invalid: {game.state.consecutive_invalid_actions}"
            )

            logger.error(f"INVALID ACTION - {error_details}")

            # Show persistent error message
            ui.render_message(
                current_player.team,
                current_player.role,
                f"⚠ Invalid action! (Strike {game.state.consecutive_invalid_actions}/3)",
                kind="warn",
            )
            print(f"  Details: {params}")

            # 3-strikes rule
            if game.state.consecutive_invalid_actions >= 3:
                logger.error(
                    f"3 CONSECUTIVE INVALID ACTIONS - {current_player.team} LOSES"
                )
                game.state.is_over = True
                game.state.winner = "Blue" if current_player.team == "Red" else "Red"
                ui.render_message(
                    None,
                    "PENALTY",
                    f"{current_player.team} made 3 consecutive invalid actions and loses!",
                    kind="error",
                )
                break

            import time

            time.sleep(2.0)

        # Small delay to see actions (shorter for human players)
        import time

        if current_player.agent_type == "ai":
            time.sleep(0.3)
        else:
            time.sleep(0.1)

        # Safety limit
        if turn_count > 100:
            ui.render_message(
                None, "GAME", "Turn limit reached, ending game", kind="warn"
            )
            break

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen and summary - show all cards revealed (spymaster view)
    ui.refresh(game, "spymaster", show_history=True)
    if game.state.get_winner():
        ui.render_message(
            None, "GAME OVER", f"Winner: {game.state.get_winner()}", kind="success"
        )
    else:
        ui.render_message(None, "GAME OVER", "No winner", kind="info")


def main():
    """Main entry point."""
    try:
        run_game()
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
