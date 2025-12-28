"""Sushi Go! game with human player."""

import copy
import time
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import SushiGoGame
from prompts import SushiGoPromptBuilder
from actions import PlayCardAction
from human_agent import SushiGoHumanAgent
from config import config
import ui

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()


def setup_game(game: SushiGoGame, logging_config: LoggingConfig) -> tuple[str, int]:
    """Configure game and get player name. Returns (player_name, human_idx)."""
    print("\n" + "=" * 70)
    print("SUSHI GO!")
    print("=" * 70)

    # Get player name
    player_name = input("\nEnter your name: ").strip()
    if not player_name:
        player_name = "You"

    print(f"\nWelcome, {player_name}!")
    print(f"You will play against {game.num_players - 1} AI opponent(s).\n")

    # Check for API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise ValueError("OPENROUTER_API_KEY is required")

    # Human is always Player 1
    human_idx = 0

    # Track model usage for naming with duplicates
    model_counts: dict[str, int] = {}
    model_instances: dict[str, int] = {}

    # First pass: count model occurrences for AI players
    for i in range(len(game.players)):
        if i == human_idx:
            continue
        model = logging_config.get_model_for_player(i)
        short_name = logging_config.get_short_model_name(model)
        model_counts[short_name] = model_counts.get(short_name, 0) + 1

    # Configure players
    for i, player in enumerate(game.players):
        if i == human_idx:
            player.agent = SushiGoHumanAgent()
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
                prompt_builder=SushiGoPromptBuilder(),
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

    print("=" * 70)
    input("Press Enter to start the game...")
    print("\n")

    return player_name, human_idx


def render_human_view(game: SushiGoGame, human_idx: int, player_name: str):
    """Render the game from the human player's perspective."""
    ui.term.clear()
    ui.render_header(game)
    ui.render_round_info(game)

    # Show all collections (public info)
    ui.render_all_collections(game)


def run_game():
    """Run Sushi Go! with human and AI players."""

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    game = SushiGoGame()
    game.setup(num_players=config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    player_name, human_idx = setup_game(game, logging_config)

    # Main game loop
    while not game.state.is_terminal():
        # Round loop
        while not game.board.is_round_over():
            if not game.state.waiting_for_players:
                game.board.pass_hands()
                game.state.waiting_for_players = set(range(game.num_players))
                continue

            # Show current state
            render_human_view(game, human_idx, player_name)

            # Collect all players' choices simultaneously
            # Human goes first, then AI (AI doesn't see human's choice)
            choices = {}

            # Human's turn first
            if human_idx in game.state.waiting_for_players:
                player = game.players[human_idx]
                state_before = copy.deepcopy(game.state)
                board_before = copy.deepcopy(game.board)

                print(f"\n>>> YOUR TURN ({player_name}) <<<")

                try:
                    llm_output = player.agent.get_action(game, player)
                    choices[human_idx] = (llm_output, state_before, board_before)
                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(2)
                    game.state.waiting_for_players.discard(human_idx)

            # AI players decide (they don't see human's choice yet)
            for player_idx in list(game.state.waiting_for_players):
                if player_idx == human_idx:
                    continue

                player = game.players[player_idx]
                state_before = copy.deepcopy(game.state)
                board_before = copy.deepcopy(game.board)

                print(f"\n[AI] {player.name} is choosing...")

                try:
                    llm_output = player.agent.get_action(game, player)
                    choices[player_idx] = (llm_output, state_before, board_before)
                except Exception as e:
                    print(f"Error: {e}")
                    game.state.waiting_for_players.discard(player_idx)

            # Apply all choices
            for player_idx, (llm_output, state_before, board_before) in choices.items():
                player = game.players[player_idx]
                action = PlayCardAction()

                # Get second card if provided
                second_card = getattr(llm_output, 'second_card', None)

                if action.validate(game, player, card_to_play=llm_output.card_to_play, second_card=second_card):
                    # Show what was played
                    if player_idx == human_idx:
                        if second_card:
                            print(f"\n{player_name} played: {llm_output.card_to_play} + {second_card} (using Chopsticks)")
                        else:
                            print(f"\n{player_name} played: {llm_output.card_to_play}")
                    else:
                        if second_card:
                            print(f"{player.name} played: {llm_output.card_to_play} + {second_card} (using Chopsticks)")
                        else:
                            print(f"{player.name} played: {llm_output.card_to_play}")

                    action.apply(game, player, card_to_play=llm_output.card_to_play, second_card=second_card)

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
                            action_params={"card_to_play": llm_output.card_to_play, "second_card": second_card},
                            action_valid=True,
                            llm_call_data=llm_call_data,
                        )
                else:
                    print(f"Invalid card from {player.name}: {llm_output.card_to_play}")
                    hand = game.board.hands[player_idx]
                    if hand:
                        action.apply(game, player, card_to_play=hand[0].name)

            time.sleep(1)

        # Round ended
        render_human_view(game, human_idx, player_name)
        game.end_round()
        ui.render_round_end(game)
        time.sleep(3)

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen
    render_human_view(game, human_idx, player_name)
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
