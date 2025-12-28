"""Incan Gold game with human player."""

import copy
import os
import time
from pathlib import Path

import ui
from actions import MakeDecisionAction
from config import config
from dotenv import load_dotenv
from game import IncanGoldGame
from human_agent import IncanGoldHumanAgent
from langchain_openai import ChatOpenAI
from prompts import IncanGoldPromptBuilder

from boardgamepy.ai import LLMAgent
from boardgamepy.logging import GameLogger, LoggedLLMAgent, LoggingConfig

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()


def setup_game(game: IncanGoldGame, logging_config: LoggingConfig) -> tuple[str, int]:
    """Configure game and get player name. Returns (player_name, human_idx)."""
    print("\n" + "=" * 70)
    print("INCAN GOLD")
    print("=" * 70)

    # Get player name
    player_name = input("\nEnter your name: ").strip()
    if not player_name:
        player_name = "You"

    print(f"\nWelcome, {player_name}!")
    print(f"You will explore the temple with {game.num_players - 1} AI opponent(s).\n")

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
            player.agent = IncanGoldHumanAgent()
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
                prompt_builder=IncanGoldPromptBuilder(),
                output_schema=MakeDecisionAction.OutputSchema,
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


def collect_decisions(
    game: IncanGoldGame, human_idx: int, player_name: str, game_logger
):
    """Collect decisions from all players still in temple simultaneously."""
    action = MakeDecisionAction()
    decisions = {}

    # Human decides first (without seeing AI decisions)
    if human_idx in game.board.in_temple and human_idx not in game.state.decisions:
        player = game.players[human_idx]
        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        ui.refresh(game)
        print(f"\n>>> YOUR DECISION ({player_name}) <<<")

        try:
            llm_output = player.agent.get_action(game, player)
            decisions[human_idx] = (llm_output, state_before, board_before)
        except Exception as e:
            print(f"Error getting decision: {e}")
            time.sleep(2)
            decisions[human_idx] = (
                MakeDecisionAction.OutputSchema(
                    decision="return", reasoning="Error occurred"
                ),
                state_before,
                board_before,
            )

    # AI players decide (they don't see human's choice in prompt)
    for player_idx in sorted(game.board.in_temple):
        if player_idx == human_idx:
            continue
        if player_idx in game.state.decisions:
            continue

        player = game.players[player_idx]
        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        print(f"\n[AI] {player.name} is deciding...")

        try:
            llm_output = player.agent.get_action(game, player)
            decisions[player_idx] = (llm_output, state_before, board_before)
        except Exception as e:
            print(f"Error: {e}")
            decisions[player_idx] = (
                MakeDecisionAction.OutputSchema(
                    decision="return", reasoning="Error occurred"
                ),
                state_before,
                board_before,
            )

    # Apply all decisions
    print("\n--- Decisions Revealed ---")
    for player_idx, (llm_output, state_before, board_before) in decisions.items():
        player = game.players[player_idx]

        if action.validate(game, player, decision=llm_output.decision):
            # Use display name but pass player.team for UI (expects "Player X" format)
            display_name = player_name if player_idx == human_idx else player.name
            ui.render_decision(
                player.team,
                llm_output.decision,
                llm_output.reasoning if player.agent_type == "ai" else None,
                display_name=display_name,
            )
            action.apply(game, player, decision=llm_output.decision)

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
                    action_params={"decision": llm_output.decision},
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )
        else:
            print(f"Invalid decision from {player.name}, defaulting to return")
            action.apply(game, player, decision="return")

    time.sleep(1)


def reveal_and_resolve_card(game: IncanGoldGame) -> bool:
    """Reveal next card and resolve effects. Returns True if round continues."""
    card = game.board.reveal_card()

    if not card:
        print("The deck is empty! All explorers must return!")
        return False

    ui.refresh(game)
    ui.render_card_reveal(card, game)
    time.sleep(2)

    if game.board.did_temple_collapse():
        print(f"\n{card.hazard.value} appeared twice! Temple has collapsed!")
        print("All explorers lose their carried gems!")
        game.board.players_lose_temp_gems(game.board.in_temple)
        time.sleep(2)
        return False

    if card.is_treasure:
        game.board.distribute_treasure_to_explorers(card.value)

    return True


def distribute_to_returners(game: IncanGoldGame):
    """Distribute gems and artifacts to players returning."""
    if not game.board.returned_this_turn:
        return

    artifacts_on_path = [c for c in game.board.revealed_path if c.is_artifact]

    if artifacts_on_path and len(game.board.returned_this_turn) == 1:
        for artifact in artifacts_on_path:
            player_idx = game.board.give_artifact_to_sole_returner(artifact)
            if player_idx is not None:
                print(
                    f"\nPlayer {player_idx + 1} is the SOLE RETURNER and claims {artifact}!"
                )
                time.sleep(1.5)
        game.board.revealed_path = [
            c for c in game.board.revealed_path if not c.is_artifact
        ]

    ui.render_distribution(game, game.board.returned_this_turn)
    game.board.distribute_gems_to_returners()


def run_round(game: IncanGoldGame, human_idx: int, player_name: str, game_logger):
    """Run a single round of Incan Gold."""
    print(f"\n{'=' * 70}")
    print(
        f"ROUND {game.state.current_round}/{game.state.total_rounds} - Temple Exploration Begins!"
    )
    print(f"{'=' * 70}\n")
    time.sleep(2)

    while not game.board.is_round_over():
        game.state.phase = "decide"
        game.state.decisions = {}

        if not game.board.in_temple:
            break

        collect_decisions(game, human_idx, player_name, game_logger)
        game.process_decisions()
        distribute_to_returners(game)
        game.board.returned_this_turn = set()

        if not game.board.in_temple:
            break

        game.state.phase = "reveal"
        if not reveal_and_resolve_card(game):
            break

        time.sleep(1)

    ui.refresh(game)
    ui.render_round_end(game)
    time.sleep(3)


def run_game():
    """Run Incan Gold with human and AI players."""

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    game = IncanGoldGame()
    game.setup(num_players=config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    player_name, human_idx = setup_game(game, logging_config)

    # Initial view
    ui.refresh(game)
    time.sleep(2)

    # Main game loop
    while not game.state.is_terminal():
        run_round(game, human_idx, player_name, game_logger)
        game.end_round()

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Final screen
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
