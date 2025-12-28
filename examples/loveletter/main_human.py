"""Love Letter game with human player."""

import copy
import time
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import LoveLetterGame
from prompts import LoveLetterPromptBuilder
from actions import PlayCardAction
from human_agent import LoveLetterHumanAgent
from config import config
import ui

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()


def setup_players(
    game: LoveLetterGame, logging_config: LoggingConfig
) -> tuple[int, str]:
    """
    Configure players - ask user which player they want to be.

    Returns:
        tuple: (player_index, player_name)
    """
    print("\n" + "=" * 60)
    print("LOVE LETTER")
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
            player.agent = LoveLetterHumanAgent()
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
                prompt_builder=LoveLetterPromptBuilder(),
                output_schema=PlayCardAction.OutputSchema,
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


def render_human_view(game: LoveLetterGame, human_player_idx: int):
    """Render the game from the human player's perspective."""
    # Clear and render header
    ui.term.clear()
    ui.render_header(game)
    ui.render_game_status(game)

    # Show board state (but hide other players' actual cards)
    print(f"{ui.term.BOLD}Players:{ui.term.RESET}")

    for i in range(game.num_players):
        player_name = f"Player {i + 1}"
        color = ui.term.get_player_color(i)

        status_parts = [f"{color}{player_name}{ui.term.RESET}"]

        if i in game.board.eliminated:
            status_parts.append(f"{ui.term.DIM}[ELIMINATED]{ui.term.RESET}")
        elif i in game.board.protected:
            status_parts.append(f"{ui.term.FG_YELLOW}[PROTECTED]{ui.term.RESET}")
        else:
            status_parts.append(f"{ui.term.FG_GREEN}[ACTIVE]{ui.term.RESET}")

        # Only show cards for human player
        hand = game.board.hands.get(i, [])
        if i == human_player_idx and hand:
            hand_str = ", ".join([f"{card.name}({card.value})" for card in hand])
            status_parts.append(f"| Hand: {ui.term.FG_CYAN}{hand_str}{ui.term.RESET}")
        elif hand:
            status_parts.append(f"| Hand: {ui.term.DIM}[hidden]{ui.term.RESET}")

        is_you = " (YOU)" if i == human_player_idx else ""
        print(f"  {' '.join(status_parts)}{is_you}")

    print()

    # Discarded cards
    if game.board.discarded:
        discards_by_value = {}
        for card in game.board.discarded:
            name = f"{card.name}({card.value})"
            discards_by_value[name] = discards_by_value.get(name, 0) + 1

        discard_str = ", ".join(
            f"{name}x{count}" for name, count in discards_by_value.items()
        )
        print(
            f"{ui.term.BOLD}Discarded:{ui.term.RESET} {ui.term.DIM}{discard_str}{ui.term.RESET}"
        )
    else:
        print(
            f"{ui.term.BOLD}Discarded:{ui.term.RESET} {ui.term.DIM}(none){ui.term.RESET}"
        )

    print(f"{ui.term.BOLD}Cards in deck:{ui.term.RESET} {len(game.board.deck)}")
    print()

    # Show history
    ui.render_history(game)


def advance_to_next_active_player(game: LoveLetterGame):
    """Advance to next non-eliminated player."""
    player_idx = game.state.current_player_idx
    next_idx = (player_idx + 1) % game.num_players
    while next_idx in game.board.eliminated:
        next_idx = (next_idx + 1) % game.num_players
    game.state.current_player_idx = next_idx


def run_game():
    """Run Love Letter with human and AI players."""

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    game = LoveLetterGame()
    game.setup(num_players=config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    human_player_idx, player_name = setup_players(game, logging_config)

    # Main game loop (multiple rounds)
    while not game.state.is_terminal():
        # Round loop
        while not game.state.round_over:
            player_idx = game.state.current_player_idx

            # Skip eliminated players
            if player_idx in game.board.eliminated:
                advance_to_next_active_player(game)
                continue

            player = game.players[player_idx]

            state_before = copy.deepcopy(game.state)
            board_before = copy.deepcopy(game.board)

            # Draw card for turn
            if game.board.deck:
                drawn_card = game.board.deck[-1]
                game.draw_card_for_turn()

                # Show draw (only if it's the human player)
                if player_idx == human_player_idx:
                    render_human_view(game, human_player_idx)
                    print(
                        f"You drew: {ui.term.FG_CYAN}{drawn_card.name}({drawn_card.value}){ui.term.RESET}"
                    )
                else:
                    render_human_view(game, human_player_idx)
                    print(f"Player {player_idx + 1} draws a card...")

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
                game.board.eliminate_player(player_idx)
                advance_to_next_active_player(game)
                continue

            # Show move
            ui.render_move(
                game.state.get_current_player_name(),
                llm_output.card_to_play,
                llm_output.target_player,
                llm_output.guess_card,
                llm_output.reasoning if player.agent_type == "ai" else None,
            )

            action = PlayCardAction()
            params = {
                "card_to_play": llm_output.card_to_play,
                "target_player": llm_output.target_player,
                "guess_card": llm_output.guess_card,
            }

            if action.validate(game, player, **params):
                result = action.apply(game, player, **params)
                ui.render_action_result(result)

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
                print(f"Invalid move! (Strike)")
                time.sleep(2)
                game.board.eliminate_player(player_idx)
                advance_to_next_active_player(game)
                continue

            # Delay
            if player.agent_type == "ai":
                time.sleep(1.5)
            else:
                time.sleep(0.5)

        # Round ended
        render_human_view(game, human_player_idx)
        ui.render_round_end(game)
        time.sleep(3)

        if game.state.is_over:
            break

        game.start_new_round()

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
