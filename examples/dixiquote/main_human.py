"""DixiQuote game with human players."""

import logging
import copy
import time
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from boardgamepy.ui import terminal as term
from game import DixiQuoteGame
from data import load_situations
from prompts import (
    StorytellerChoosePromptBuilder,
    StorytellerQuotePromptBuilder,
    SubmitSituationPromptBuilder,
    VotePromptBuilder,
)
from actions import (
    ChooseSituationAction,
    GiveQuoteAction,
    SubmitSituationAction,
    VoteAction,
)
from human_agent import DixiQuoteHumanAgent
from config import config
import ui
import os

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


def setup_players(game: DixiQuoteGame, logging_config: LoggingConfig) -> int:
    """
    Configure players - ask user which player they want to be.
    All other players will be AI.

    Returns:
        int: The player index (0-based) of the human player
    """
    print("\n" + "=" * 60)
    print("PLAYER CONFIGURATION")
    print("=" * 60)

    # Ask for player name
    human_name = input("\nEnter your name: ").strip()
    if not human_name:
        human_name = "Human"

    # Ask for player index
    num_players = len(game.players)
    print(f"\nWhich player do you want to be? (Players take turns as Storyteller)")
    print(f"Available: P-0 to P-{num_players - 1}\n")

    while True:
        choice = input(f"Choose your player index (0-{num_players - 1}): ").strip()
        try:
            human_idx = int(choice)
            if 0 <= human_idx < num_players:
                break
            print(f"Please enter a number between 0 and {num_players - 1}")
        except ValueError:
            print("Please enter a valid number")

    print(f"\n✓ You ({human_name}) will play as P-{human_idx}")
    print(f"✓ All other players will be AI")
    print(f"✓ Players rotate as Storyteller each round\n")

    # Check for API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise ValueError("OPENROUTER_API_KEY is required")

    # Configure human player
    human_player = game.players[human_idx]
    human_player.agent = DixiQuoteHumanAgent()
    human_player.agent_type = "human"
    human_player.name = human_name

    # Configure AI players
    for i, player in enumerate(game.players):
        if i != human_idx:
            model = logging_config.get_model_for_player(i)
            short_name = logging_config.get_short_model_name(model)

            # Create placeholder agent (will be reassigned per phase)
            llm = ChatOpenAI(
                model=model,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
            )
            base_agent = LLMAgent(
                llm=llm,
                prompt_builder=StorytellerChoosePromptBuilder(),
                output_schema=ChooseSituationAction.OutputSchema,
            )
            player.agent = LoggedLLMAgent(base_agent, model)
            player.agent_type = "ai"
            player.name = short_name

    print("=" * 60)
    input("Press Enter to start the game...")
    print("\n")

    return human_idx


def setup_ai_agents_for_phase(game: DixiQuoteGame, human_idx: int, logging_config: LoggingConfig):
    """Configure AI agents based on current phase."""
    phase = game.state.phase
    storyteller_idx = game.state.storyteller_idx

    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    for i, player in enumerate(game.players):
        if i == human_idx:
            # Human player keeps their agent
            continue

        # AI player - reassign agent based on phase
        model = logging_config.get_model_for_player(i)
        llm = ChatOpenAI(
            model=model,
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # Choose prompt builder based on phase and role
        if i == storyteller_idx:
            if phase == "choose_situation":
                prompt_builder = StorytellerChoosePromptBuilder()
                output_schema = ChooseSituationAction.OutputSchema
            elif phase == "give_quote":
                prompt_builder = StorytellerQuotePromptBuilder()
                output_schema = GiveQuoteAction.OutputSchema
            else:
                # Storyteller doesn't act in other phases
                continue
        else:
            if phase == "submit_situations":
                prompt_builder = SubmitSituationPromptBuilder()
                output_schema = SubmitSituationAction.OutputSchema
            elif phase == "vote":
                prompt_builder = VotePromptBuilder()
                output_schema = VoteAction.OutputSchema
            else:
                # Other players don't act in storyteller phases
                continue

        base_agent = LLMAgent(
            llm=llm, prompt_builder=prompt_builder, output_schema=output_schema
        )
        player.agent = LoggedLLMAgent(base_agent, model)


def run_phase_action(
    game: DixiQuoteGame,
    player,
    phase: str,
    game_logger: GameLogger,
    human_idx: int
) -> bool:
    """
    Run action for a single phase.

    Returns:
        bool: True if action was executed successfully or penalty applied, False to retry
    """
    state_before = copy.deepcopy(game.state)

    # Don't show hand during voting phase
    # Also don't show hand for human player - they'll see it in the prompt
    is_human = player.agent_type == "human"
    show_hand = not is_human and phase != "vote"

    # Refresh UI before action (always show human player's hand only)
    ui.refresh(game, show_hand=show_hand, player_idx=human_idx)

    # Show player type indicator
    player_type = "HUMAN" if player.agent_type == "human" else "AI"

    try:
        llm_output = player.agent.get_action(game, player)
    except Exception as e:
        print(f"{term.FG_RED}Error: {e}{term.RESET}")
        time.sleep(2)
        return False

    # Execute action based on phase
    if phase == "choose_situation":
        action = ChooseSituationAction()
        params = {"situation": llm_output.situation}
        print(
            f"{term.BOLD}{term.FG_YELLOW}[{player_type}] P-{player.player_idx}: {player.name} - Storyteller{term.RESET} Choosing situation..."
        )
        print(f"  {term.DIM}(Hidden from other players){term.RESET}")

    elif phase == "give_quote":
        action = GiveQuoteAction()
        params = {"quote": llm_output.quote}
        print(f"{term.BOLD}{term.FG_YELLOW}[{player_type}] P-{player.player_idx}: {player.name} - Storyteller{term.RESET} Giving quote...")
        print(f'  Quote: {term.FG_BRIGHT_YELLOW}"{llm_output.quote}"{term.RESET}')

    elif phase == "submit_situations":
        action = SubmitSituationAction()
        params = {"situation": llm_output.situation}
        print(f"{term.BOLD}{term.FG_CYAN}[{player_type}] P-{player.player_idx}: {player.name}{term.RESET} Submitting situation...")
        print(f"  {term.DIM}(Hidden until voting){term.RESET}")

    elif phase == "vote":
        action = VoteAction()
        params = {"situation": llm_output.situation}
        print(f"{term.BOLD}{term.FG_CYAN}[{player_type}] P-{player.player_idx}: {player.name}{term.RESET} Voting...")
        print(f"  {term.DIM}(Hidden until scoring){term.RESET}")

    else:
        return False

    # Only show reasoning for human players
    if player.agent_type == "human" and llm_output.reasoning:
        ui.render_reasoning(llm_output.reasoning)

    # Validate and apply action
    if action.validate(game, player, **params):
        # VALID ACTION
        action.apply(game, player, **params)
        state_after = copy.deepcopy(game.state)

        # Reset consecutive invalid actions on success
        game.state.consecutive_invalid_actions = 0

        # Log turn
        if game_logger.enabled:
            llm_call_data = None
            if hasattr(player.agent, "_last_llm_call"):
                llm_call_data = player.agent._last_llm_call
                player.agent._last_llm_call = None

            game_logger.log_turn(
                player=player,
                state_before=state_before,
                state_after=state_after,
                board_before=None,
                board_after=None,
                action=action,
                action_params=params,
                action_valid=True,
                llm_call_data=llm_call_data,
            )

        return True

    else:
        # INVALID ACTION
        game.state.consecutive_invalid_actions += 1

        error_details = (
            f"Player: P-{player.player_idx}, "
            f"Phase: {phase}, "
            f"Action: {action.name}, "
            f"Params: {params}, "
            f"Consecutive invalid: {game.state.consecutive_invalid_actions}"
        )

        logger.error(f"INVALID ACTION - {error_details}")

        print(
            f"{term.FG_RED}⚠ Invalid action! "
            f"(Strike {game.state.consecutive_invalid_actions}/3){term.RESET}"
        )
        print(f"  Details: {params}")

        # 3-strikes rule
        if game.state.consecutive_invalid_actions >= 3:
            logger.error(f"3 CONSECUTIVE INVALID ACTIONS - P-{player.player_idx} PENALIZED")

            print(
                f"{term.FG_YELLOW}Player P-{player.player_idx} penalized: "
                f"-1 point and turn skipped{term.RESET}"
            )

            # Apply -1 point penalty (minimum 0)
            current_score = game.state.scores.get(player.player_idx, 0)
            game.state.scores[player.player_idx] = max(0, current_score - 1)

            # Mark as skipped
            game.state.skipped_players.add(player.player_idx)

            # Reset counter and skip turn
            game.state.consecutive_invalid_actions = 0
            time.sleep(3)
            return True  # Return True to move to next player

        else:
            time.sleep(2)
            return False  # Retry


def run_game():
    """Run a DixiQuote game with human and/or AI players."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 13 + "DIXIQUOTE - HUMAN PLAYABLE" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print(f"\n📝 Logging errors to: {log_file.absolute()}\n")

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Load situations
    situations = load_situations()
    print(f"Loaded {len(situations)} situation cards")

    # Get game settings from CLI or config
    import argparse
    parser = argparse.ArgumentParser(description="Play DixiQuote (Human)")
    parser.add_argument("--target", type=int, default=None, help="Target score to win")
    parser.add_argument("--target-score", type=int, default=None, help="Target score to win")
    parser.add_argument("--max-rounds", type=int, default=None, help="Maximum number of rounds")
    parser.add_argument("--num-players", type=int, default=4, help="Number of players (3-8)")
    args = parser.parse_args()

    # Determine target score (--target takes precedence over --target-score)
    target_score = args.target if args.target is not None else args.target_score
    if target_score is None:
        target_score = config.target_score

    # Determine max rounds
    max_rounds = args.max_rounds if args.max_rounds is not None else config.max_rounds

    print(f"Game settings: {args.num_players} players, target score: {target_score}, max rounds: {max_rounds}\n")

    # Create game
    game = DixiQuoteGame()
    game.setup(
        situations=situations,
        num_players=args.num_players,
        target_score=target_score,
        max_rounds=max_rounds,
    )

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    human_idx = setup_players(game, logging_config)

    turn_count = 0

    # Main game loop
    while not game.state.is_terminal():
        turn_count += 1

        # Handle scoring phase
        if game.state.phase == "scoring":
            ui.refresh(game)

            # Calculate scores
            situation_scores = game.calculate_scores()

            # Show scoring results
            ui.render_scoring_results(game, situation_scores)
            time.sleep(5)

            # Start new round
            game.start_new_round()
            continue

        # Re-assign AI agents for current phase
        setup_ai_agents_for_phase(game, human_idx, logging_config)

        # Get current player
        player = game.get_current_player()
        if player is None:
            # No player for this phase, should not happen
            print(f"{term.FG_RED}Error: No current player for phase {game.state.phase}{term.RESET}")
            break

        # Run the phase action
        run_phase_action(game, player, game.state.phase, game_logger, human_idx)

        # Small delay (shorter for human players)
        if player.agent_type == "ai":
            time.sleep(1.0)
        else:
            time.sleep(0.3)

        # Safety limit
        if turn_count > 500:
            print(f"{term.FG_RED}Turn limit reached, ending game{term.RESET}")
            break

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen
    ui.refresh(game)
    print()
    print(f"{term.BOLD}{term.FG_GREEN}GAME OVER!{term.RESET}")
    print()

    # Show reason for game end
    if game.state.scores and max(game.state.scores.values()) >= game.state.target_score:
        print(f"{term.FG_CYAN}Game ended: Target score reached!{term.RESET}")
    elif game.state.round_number > game.state.max_rounds:
        print(f"{term.FG_CYAN}Game ended: Max rounds reached!{term.RESET}")
    elif not game.deck:
        print(f"{term.FG_CYAN}Game ended: Deck exhausted!{term.RESET}")

    print()

    # Find all winners (highest score, possibly multiple players tied)
    if game.state.scores:
        max_score = max(game.state.scores.values())
        winners = [idx for idx, score in game.state.scores.items() if score == max_score]

        if len(winners) == 1:
            winner_idx = winners[0]
            winner = game.players[winner_idx]
            print(f"{term.FG_YELLOW}Winner: {winner.name} (P-{winner_idx}) with {max_score} points!{term.RESET}")
        else:
            print(f"{term.FG_YELLOW}Tied Winners ({max_score} points):{term.RESET}")
            for winner_idx in winners:
                winner = game.players[winner_idx]
                print(f"  {term.FG_CYAN}{winner.name} (P-{winner_idx}){term.RESET}")
    else:
        print("No winner")

    print()


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
