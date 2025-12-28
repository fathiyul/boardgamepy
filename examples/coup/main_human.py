"""Coup game with human player."""

import copy
import time
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import CoupGame
from prompts import CoupPromptBuilder
from actions import TakeTurnAction
from human_agent import CoupHumanAgent
from config import config
import ui

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()


def setup_players(game: CoupGame, logging_config: LoggingConfig) -> tuple[int, str]:
    """
    Configure players - ask user which player they want to be.

    Returns:
        tuple: (player_index, player_name)
    """
    print("\n" + "=" * 60)
    print("COUP")
    print("=" * 60)

    # Get player name
    player_name = input("\nEnter your name: ").strip()
    if not player_name:
        player_name = "You"

    print(f"\nWelcome, {player_name}!")
    print(f"This is a {game.num_players}-player game.")
    print("Which position do you want?\n")

    for i in range(game.num_players):
        print(f"  {i + 1}. Position {i + 1}")

    while True:
        choice = input(f"\nChoose player (1-{game.num_players}): ").strip()
        try:
            player_num = int(choice)
            if 1 <= player_num <= game.num_players:
                human_player_idx = player_num - 1
                break
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {game.num_players}")

    print(f"\nYou will play as Player {human_player_idx + 1} ({player_name})")
    print("All other players will be AI\n")

    # Check for API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise ValueError("OPENROUTER_API_KEY is required")

    # Track model usage for naming with duplicates
    model_counts: dict[str, int] = {}
    model_instances: dict[str, int] = {}

    # First pass: count model occurrences for AI players
    for i in range(len(game.players)):
        if i == human_player_idx:
            continue
        model = logging_config.get_model_for_player(i)
        short_name = logging_config.get_short_model_name(model)
        model_counts[short_name] = model_counts.get(short_name, 0) + 1

    # Configure players
    for i, player in enumerate(game.players):
        if i == human_player_idx:
            player.agent = CoupHumanAgent()
            player.agent_type = "human"
            player.name = player_name
        else:
            model = logging_config.get_model_for_player(i)
            base_llm = ChatOpenAI(
                model=model,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
            )
            base_agent = LLMAgent(
                llm=base_llm,
                prompt_builder=CoupPromptBuilder(),
                output_schema=TakeTurnAction.OutputSchema,
            )
            player.agent = LoggedLLMAgent(base_agent, model)
            player.agent_type = "ai"

            # Set player name to model name
            short_name = logging_config.get_short_model_name(model)
            if model_counts[short_name] > 1:
                model_instances[short_name] = model_instances.get(short_name, 0) + 1
                player.name = f"{short_name} ({model_instances[short_name]})"
            else:
                player.name = short_name

    print("=" * 60)
    input("Press Enter to start the game...")
    print("\n")

    return human_player_idx, player_name


def render_human_view(game: CoupGame, human_player_idx: int):
    """Render the game from the human player's perspective."""
    ui.term.clear()
    ui.render_header(game)

    print(f"{ui.term.BOLD}Players:{ui.term.RESET}")

    for i in range(game.num_players):
        player = game.players[i] if i < len(game.players) else None
        name = player.name if player and player.name else None
        player_label = f"P{i + 1} ({name})" if name else f"Player {i + 1}"
        color = ui.term.get_player_color(i)
        coins = game.board.coins[i]

        # Count influence
        influence = game.board.influence[i]
        active_count = len([c for c in influence if not c.revealed])
        revealed = [c for c in influence if c.revealed]

        info = f"  {color}{player_label}{ui.term.RESET}: "
        info += f"{coins} coins, {active_count} influence"

        if revealed:
            revealed_names = [c.type.char_name for c in revealed]
            info += f" (revealed: {', '.join(revealed_names)})"

        # Show human player's actual cards
        if i == human_player_idx:
            hidden_cards = [c for c in influence if not c.revealed]
            if hidden_cards:
                card_names = [c.type.char_name for c in hidden_cards]
                info += f" | Your cards: {ui.term.FG_CYAN}{', '.join(card_names)}{ui.term.RESET}"
            info += " (YOU)"

        if not game.board.has_influence(i):
            info += f" {ui.term.DIM}[ELIMINATED]{ui.term.RESET}"

        print(info)

    print()


def advance_to_next_active_player(game: CoupGame):
    """Advance to next player with influence."""
    player_idx = game.state.current_player_idx
    next_idx = (player_idx + 1) % game.num_players
    while not game.board.has_influence(next_idx):
        next_idx = (next_idx + 1) % game.num_players
    game.state.current_player_idx = next_idx


def run_game():
    """Run Coup with human and AI players."""

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    game = CoupGame()
    game.setup(num_players=config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    human_player_idx, player_name = setup_players(game, logging_config)

    turn_count = 0

    # Main game loop
    while not game.state.is_terminal():
        turn_count += 1
        player_idx = game.state.current_player_idx

        # Skip eliminated players
        if not game.board.has_influence(player_idx):
            advance_to_next_active_player(game)
            continue

        player = game.players[player_idx]

        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        # Render from human's perspective
        render_human_view(game, human_player_idx)

        # Show whose turn
        if player.agent_type == "human":
            print(f"\n>>> YOUR TURN <<<\n")
        else:
            print(f"\n[AI] Player {player_idx + 1}'s turn...\n")

        # Get action
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            game.board.reveal_random_influence(player_idx)
            game.board.reveal_random_influence(player_idx)
            continue

        # Enforce must-coup rule
        if game.board.coins[player_idx] >= 10 and llm_output.action != "coup":
            print("Invalid: Must coup with 10+ coins! Auto-couping...")
            time.sleep(2)
            targets = [
                i
                for i in range(game.num_players)
                if i != player_idx and game.board.has_influence(i)
            ]
            if targets:
                llm_output.action = "coup"
                llm_output.target_player = targets[0] + 1
            else:
                game.board.reveal_random_influence(player_idx)
                continue

        # Show move
        ui.render_move(
            game.state.get_current_player_name(),
            llm_output.action,
            f"Player {llm_output.target_player}" if llm_output.target_player else None,
            None,
            None,
            llm_output.reasoning if player.agent_type == "ai" else None,
        )

        action = TakeTurnAction()
        params = {
            "action": llm_output.action,
            "target_player": llm_output.target_player,
            "character_to_reveal": llm_output.character_to_reveal,
        }

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
        else:
            print(f"Invalid action! (Strike)")
            time.sleep(2)
            continue

        # Delay
        if player.agent_type == "ai":
            time.sleep(1.5)
        else:
            time.sleep(0.5)

        # Safety limit
        if turn_count > 100:
            print("Turn limit reached!")
            break

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen
    render_human_view(game, human_player_idx)
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
