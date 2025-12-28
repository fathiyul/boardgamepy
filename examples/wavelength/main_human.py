"""Wavelength game with human player."""

import copy
import time
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from boardgamepy.ui import terminal as term
from game import WavelengthGame
from prompts import PsychicPromptBuilder, GuesserPromptBuilder, OpponentPromptBuilder
from actions import GiveClueAction, GuessPositionAction, PredictDirectionAction
from human_agent import (
    WavelengthPsychicHumanAgent,
    WavelengthGuesserHumanAgent,
    WavelengthOpponentHumanAgent,
)
from config import config
import ui

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()


def setup_game(
    game: WavelengthGame, logging_config: LoggingConfig
) -> tuple[str, int, str]:
    """
    Configure game and get player preferences.
    Returns (player_name, human_team_idx, first_role).
    first_role is 'psychic' or 'guesser' - will alternate each round.
    """
    print("\n" + "=" * 70)
    print("WAVELENGTH")
    print("=" * 70)

    # Get player name
    player_name = input("\nEnter your name: ").strip()
    if not player_name:
        player_name = "You"

    print(f"\nWelcome, {player_name}!")
    print("\nWhich team do you want to join?\n")

    team1_size = len(game.teams[0])
    team2_size = len(game.teams[1])
    print(f"  1. Team 1 ({team1_size} players)")
    print(f"  2. Team 2 ({team2_size} players)")

    while True:
        choice = input("\nChoose team (1-2): ").strip()
        if choice in ["1", "2"]:
            human_team_idx = int(choice) - 1
            break
        print("Please enter 1 or 2")

    print(f"\nYou joined Team {human_team_idx + 1}!")
    print("\nWhich role do you want to play FIRST when your team is active?")
    print("(You will alternate between Psychic and Guesser each round)")
    print("  1. Psychic first (give clues, then guess next round)")
    print("  2. Guesser first (guess first, then give clues next round)")

    while True:
        choice = input("\nChoose first role (1-2): ").strip()
        if choice == "1":
            first_role = "psychic"
            break
        elif choice == "2":
            first_role = "guesser"
            break
        print("Please enter 1 or 2")

    print(f"\nYou will start as {'Psychic' if first_role == 'psychic' else 'Guesser'}.")
    print("When the other team plays, you'll predict left/right.\n")

    print("=" * 70)
    input("Press Enter to start the game...")
    print("\n")

    return player_name, human_team_idx, first_role


def get_human_role_this_round(
    game: WavelengthGame, human_team_idx: int, first_role: str
) -> str:
    """
    Determine what role the human should play this round.
    Returns 'psychic', 'guesser', or 'opponent'.
    """
    current_team = game.state.current_team

    if current_team != human_team_idx:
        # Other team is playing, human predicts left/right
        return "opponent"

    # Human's team is playing - alternate between psychic and guesser
    # Count how many times human's team has played
    # Round 1,2 = teams 0,1; Round 3,4 = teams 0,1; etc.
    # Team plays on odd rounds if team_idx=0, even rounds if team_idx=1
    # Actually simpler: just count based on round number and which team started

    # Each team plays every 2 rounds. Count team's rounds:
    team_round = (game.state.round_number + 1) // 2
    if human_team_idx == 1:
        team_round = game.state.round_number // 2

    # Alternate based on team's round count
    if first_role == "psychic":
        return "psychic" if team_round % 2 == 1 else "guesser"
    else:
        return "guesser" if team_round % 2 == 1 else "psychic"


def setup_round_agents(
    game: WavelengthGame,
    logging_config: LoggingConfig,
    human_team_idx: int,
    first_role: str,
    player_name: str,
):
    """Setup agents for the current round based on roles."""
    # Check for API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise ValueError("OPENROUTER_API_KEY is required")

    psychic_builder = PsychicPromptBuilder()
    guesser_builder = GuesserPromptBuilder()
    opponent_builder = OpponentPromptBuilder()

    # Determine human's role this round
    human_role = get_human_role_this_round(game, human_team_idx, first_role)

    # Track if human has been assigned (only ONE human per role)
    human_assigned = False

    for i, player in enumerate(game.players):
        player_team_idx = 0 if player.team == "Team 1" else 1

        # Get per-player model
        model = logging_config.get_model_for_player(i)
        short_name = logging_config.get_short_model_name(model)

        # Check if this player should be human-controlled
        # Only assign human to FIRST matching player in the team
        is_human_player = (
            not human_assigned
            and player_team_idx == human_team_idx
            and player.role.lower() == human_role
        )

        if is_human_player:
            human_assigned = True

        if player.role == "Psychic":
            if is_human_player:
                player.agent = WavelengthPsychicHumanAgent()
                player.agent_type = "human"
                player.name = player_name
            else:
                llm = ChatOpenAI(
                    model=model,
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                )
                base_agent = LLMAgent(
                    llm=llm,
                    prompt_builder=psychic_builder,
                    output_schema=GiveClueAction.OutputSchema,
                )
                player.agent = LoggedLLMAgent(base_agent, model)
                player.agent_type = "ai"
                player.name = short_name

        elif player.role == "Guesser":
            if is_human_player:
                player.agent = WavelengthGuesserHumanAgent()
                player.agent_type = "human"
                player.name = player_name
            else:
                llm = ChatOpenAI(
                    model=model,
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                )
                base_agent = LLMAgent(
                    llm=llm,
                    prompt_builder=guesser_builder,
                    output_schema=GuessPositionAction.OutputSchema,
                )
                player.agent = LoggedLLMAgent(base_agent, model)
                player.agent_type = "ai"
                player.name = short_name

        elif player.role == "Opponent":
            if is_human_player:
                player.agent = WavelengthOpponentHumanAgent()
                player.agent_type = "human"
                player.name = player_name
            else:
                llm = ChatOpenAI(
                    model=model,
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                )
                base_agent = LLMAgent(
                    llm=llm,
                    prompt_builder=opponent_builder,
                    output_schema=PredictDirectionAction.OutputSchema,
                )
                player.agent = LoggedLLMAgent(base_agent, model)
                player.agent_type = "ai"
                player.name = short_name


def render_human_view(
    game: WavelengthGame, human_team_idx: int, player_name: str, first_role: str
):
    """Render the game from the human player's perspective."""
    term.clear()
    ui.render_header(game)
    ui.render_scores(game)

    # Show spectrum using shared function
    if game.board.current_spectrum:
        # Determine human's role this round
        human_role = get_human_role_this_round(game, human_team_idx, first_role)

        # Use ui.render_spectrum but add human-specific target visibility
        spectrum = game.board.current_spectrum

        print(f"{term.BOLD}Current Spectrum:{term.RESET}")

        # Calculate arrow length to match scale line below
        scale_width = 86
        fixed_chars = 8  # Brackets, spaces, and arrow ends
        text_length = len(spectrum.left) + len(spectrum.right)
        arrow_dashes_needed = scale_width - fixed_chars - text_length
        arrow_dashes = max(arrow_dashes_needed, 10)
        arrow = "─" * arrow_dashes

        print(f"  {term.FG_CYAN}[{spectrum.left}]{term.RESET} ←{arrow}→ {term.FG_MAGENTA}[{spectrum.right}]{term.RESET}")
        print(f"  {term.DIM}0{'':^40}50{'':^40}100{term.RESET}")

        # Show target ONLY if human is psychic in psychic phase
        if human_role == "psychic" and game.state.phase == "psychic_clue":
            print(
                f"\n  {term.BOLD}{term.FG_YELLOW}TARGET: {game.board.target_center}{term.RESET} (only you see this!)"
            )
        elif game.state.phase == "reveal":
            print(f"\n  {term.BOLD}Target: {game.board.target_center}{term.RESET}")

        # Show clue if given
        if game.board.psychic_clue:
            print(
                f'\n  {term.BOLD}Clue:{term.RESET} "{term.FG_CYAN}{game.board.psychic_clue}{term.RESET}"'
            )

        # Show guess if made
        if game.board.dial_position is not None:
            print(f"  {term.BOLD}Guess:{term.RESET} {game.board.dial_position}")

        print()

    # Show phase info
    phase = game.state.phase
    current_team_name = f"Team {game.state.current_team + 1}"

    if phase == "psychic_clue":
        print(
            f"{term.BOLD}Phase: Psychic giving clue ({current_team_name}){term.RESET}\n"
        )
    elif phase == "team_guess":
        print(f"{term.BOLD}Phase: Team guessing ({current_team_name}){term.RESET}\n")
    elif phase == "opponent_predict":
        opponent_team = f"Team {(1 - game.state.current_team) + 1}"
        print(f"{term.BOLD}Phase: Opponent predicting ({opponent_team}){term.RESET}\n")
    elif phase == "reveal":
        print(f"{term.BOLD}Phase: Reveal{term.RESET}\n")


def run_phase(
    game: WavelengthGame,
    player,
    phase: str,
    game_logger,
    human_team_idx: int,
    player_name: str,
):
    """Handle a single phase of the game."""
    state_before = copy.deepcopy(game.state)
    board_before = copy.deepcopy(game.board)

    is_human = player.agent_type == "human"

    if is_human:
        print(f"\n>>> YOUR TURN ({player.role}) <<<\n")
    else:
        print(f"\n[AI] {player.role} is thinking...\n")

    try:
        llm_output = player.agent.get_action(game, player)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
        return False

    if phase == "psychic_clue":
        action = GiveClueAction()
        params = {"clue": llm_output.clue}
        if not is_human:
            print(f'  Clue: "{term.FG_YELLOW}{llm_output.clue}{term.RESET}"')
        else:
            print(f'\nYou gave the clue: "{llm_output.clue}"')

    elif phase == "team_guess":
        action = GuessPositionAction()
        params = {"position": llm_output.position}
        if not is_human:
            print(f"  Position: {term.FG_YELLOW}{llm_output.position}{term.RESET}")
        else:
            print(f"\nYou guessed: {llm_output.position}")

    elif phase == "opponent_predict":
        action = PredictDirectionAction()
        params = {"prediction": llm_output.prediction}
        if not is_human:
            print(
                f"  Prediction: {term.FG_YELLOW}{llm_output.prediction.upper()}{term.RESET}"
            )
        else:
            print(f"\nYou predicted: {llm_output.prediction.upper()}")
    else:
        return False

    if not is_human and llm_output.reasoning:
        print(f"  {term.DIM}Reasoning: {llm_output.reasoning}{term.RESET}")
    print()

    if action.validate(game, player, **params):
        action.apply(game, player, **params)

        state_after = copy.deepcopy(game.state)
        board_after = copy.deepcopy(game.board)

        if game_logger.enabled:
            llm_call_data = None
            if hasattr(player.agent, "_last_llm_call"):
                llm_call_data = player.agent._last_llm_call
                player.agent._last_llm_call = None

            game_logger.log_turn(
                player=player,
                state_before=state_before,
                state_after=state_after,
                board_before=board_before,
                board_after=board_after,
                action=action,
                action_params=params,
                action_valid=True,
                llm_call_data=llm_call_data,
            )
        return True
    else:
        print("Invalid action!")
        time.sleep(2)
        return False


def run_game():
    """Run Wavelength with human and AI players."""

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    game = WavelengthGame()
    game.setup(num_players=config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    player_name, human_team_idx, first_role = setup_game(game, logging_config)

    # Main game loop
    while not game.state.is_terminal():
        # Re-assign agents when roles change
        setup_round_agents(
            game, logging_config, human_team_idx, first_role, player_name
        )

        player = game.get_current_player()
        phase = game.state.phase

        if phase == "reveal":
            render_human_view(game, human_team_idx, player_name, first_role)
            ui.render_result(game)
            time.sleep(5)

            if game.state.is_over:
                break

            print("\nStarting next round...")
            time.sleep(2)
            game.start_new_round()
        else:
            render_human_view(game, human_team_idx, player_name, first_role)
            if player:
                run_phase(game, player, phase, game_logger, human_team_idx, player_name)

        time.sleep(1.5)

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen
    render_human_view(game, human_team_idx, player_name, first_role)
    ui.render_game_end(game)


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
