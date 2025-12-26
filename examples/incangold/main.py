"""Incan Gold game using boardgamepy framework."""

import time
import logging
from pathlib import Path
import copy

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import IncanGoldGame
from prompts import IncanGoldPromptBuilder
from actions import MakeDecisionAction
from config import config
import ui

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def setup_ai_agents(game: IncanGoldGame, logging_config: LoggingConfig) -> None:
    """Configure AI agents for all players."""
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

    # Configure all players
    prompt_builder = IncanGoldPromptBuilder()

    for player in game.players:
        base_agent = LLMAgent(
            llm=llm,
            prompt_builder=prompt_builder,
            output_schema=MakeDecisionAction.OutputSchema,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def collect_decisions(game: IncanGoldGame, game_logger) -> None:
    """Collect decisions from all players still in temple."""
    action = MakeDecisionAction()

    for player_idx in sorted(game.board.in_temple):
        if player_idx in game.state.decisions:
            continue  # Already decided

        player = game.players[player_idx]

        # Capture state before
        state_before = copy.deepcopy(game.state)

        # Refresh UI for current player
        ui.refresh(game)
        ui.render_decision_prompt(game, player_idx)

        # Get decision from AI
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"⚠️  Error getting decision: {e}")
            time.sleep(2)
            # Default to return (safe choice)
            llm_output = MakeDecisionAction.OutputSchema(
                decision="return", reasoning="Error occurred, playing safe"
            )

        # Validate and apply
        if action.validate(game, player, decision=llm_output.decision):
            ui.render_decision(player.team, llm_output.decision, llm_output.reasoning)
            action.apply(game, player, decision=llm_output.decision)

            # Capture state after
            state_after = copy.deepcopy(game.state)

            # Log turn
            if game_logger.enabled:
                llm_call_data = None
                if hasattr(player.agent, '_last_llm_call'):
                    llm_call_data = player.agent._last_llm_call
                    player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=player,
                    state_before=state_before,
                    state_after=state_after,
                    board_before="",
                    board_after="",
                    action=action,
                    action_params={"decision": llm_output.decision},
                    action_valid=True,
                    llm_call_data=llm_call_data
                )
        else:
            print(f"⚠️  Invalid decision from {player.team}, defaulting to return")
            # Force return
            action.apply(game, player, decision="return")

        time.sleep(0.5)


def reveal_and_resolve_card(game: IncanGoldGame) -> bool:
    """
    Reveal next card and resolve its effects.

    Returns:
        True if round should continue, False if round ended
    """
    # Reveal card
    card = game.board.reveal_card()

    if not card:
        # No more cards - round ends
        print("📦 The deck is empty! All explorers must return!")
        return False

    # Show card
    ui.refresh(game)
    ui.render_card_reveal(card, game)
    time.sleep(2)

    # Check for temple collapse
    if game.board.did_temple_collapse():
        # Everyone in temple loses their temp gems
        print(f"\n💀 {card.hazard.value} appeared twice! Temple has collapsed!")
        print("All explorers lose their carried gems!")
        game.board.players_lose_temp_gems(game.board.in_temple)
        time.sleep(2)
        return False  # Round ends

    # Handle card effects
    if card.is_treasure:
        # Distribute gems to explorers
        game.board.distribute_treasure_to_explorers(card.value)
    elif card.is_artifact:
        # Artifact goes on path (will be distributed to returners later)
        pass  # Artifact is already on revealed_path

    return True  # Round continues


def distribute_to_returners(game: IncanGoldGame) -> None:
    """Distribute gems and artifacts to players returning this turn."""
    if not game.board.returned_this_turn:
        return

    # First, check for artifacts on the path
    artifacts_on_path = [c for c in game.board.revealed_path if c.is_artifact]

    if artifacts_on_path and len(game.board.returned_this_turn) == 1:
        # Sole returner gets all artifacts
        for artifact in artifacts_on_path:
            player_idx = game.board.give_artifact_to_sole_returner(artifact)
            if player_idx is not None:
                player_name = f"Player {player_idx + 1}"
                print(
                    f"\n🏺 {player_name} is the SOLE RETURNER and claims {artifact}!"
                )
                time.sleep(1.5)

        # Remove artifacts from path
        game.board.revealed_path = [c for c in game.board.revealed_path if not c.is_artifact]

    # Distribute gems from path
    ui.render_distribution(game, game.board.returned_this_turn)
    game.board.distribute_gems_to_returners()


def run_round(game: IncanGoldGame, game_logger) -> None:
    """Run a single round of Incan Gold."""
    print(f"\n{'=' * 70}")
    print(f"ROUND {game.state.current_round}/{game.state.total_rounds} - Temple Exploration Begins!")
    print(f"{'=' * 70}\n")
    time.sleep(2)

    # Round loop
    while not game.board.is_round_over():
        # Phase 1: Decide (continue or return)
        game.state.phase = "decide"
        game.state.decisions = {}  # Clear previous decisions

        if not game.board.in_temple:
            # Everyone has returned
            break

        collect_decisions(game, game_logger)

        # Process decisions
        game.process_decisions()
        distribute_to_returners(game)

        # Clear returners for next turn
        game.board.returned_this_turn = set()

        if not game.board.in_temple:
            # Everyone returned
            break

        # Phase 2: Reveal card
        game.state.phase = "reveal"
        should_continue = reveal_and_resolve_card(game)

        if not should_continue:
            break

        # Brief pause before next decision
        time.sleep(1)

    # Round ended
    ui.refresh(game)
    ui.render_round_end(game)
    time.sleep(3)


def run_game(num_players: int | None = None) -> None:
    """Run an Incan Gold game."""
    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and setup game
    game = IncanGoldGame()
    game.setup(num_players=num_players or config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"num_players": num_players or config.num_players})

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    # Initial display
    ui.refresh(game)
    time.sleep(2)

    # Game loop (5 rounds)
    while not game.state.is_terminal():
        run_round(game, game_logger)
        game.end_round()

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Game ended
    ui.render_game_end(game)


def main():
    """Main entry point."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Play Incan Gold")
    parser.add_argument(
        "--num_players",
        type=int,
        default=None,
        help="Number of players (3-8, default: from config)"
    )
    args = parser.parse_args()

    if not config.OPENAI_API_KEY and not config.OPENROUTER_API_KEY:
        print("❌ Error: No API key found!")
        print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
        return

    try:
        run_game(num_players=args.num_players)
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
