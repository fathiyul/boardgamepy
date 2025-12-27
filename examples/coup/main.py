"""Coup game using boardgamepy framework."""

import time
import logging
from pathlib import Path
import copy

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import CoupGame
from prompts import CoupPromptBuilder
from actions import TakeTurnAction
from config import config
import ui

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def setup_ai_agents(game: CoupGame, logging_config: LoggingConfig) -> None:
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
    prompt_builder = CoupPromptBuilder()

    for player in game.players:
        base_agent = LLMAgent(
            llm=llm,
            prompt_builder=prompt_builder,
            output_schema=TakeTurnAction.OutputSchema,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def run_game(num_players: int | None = None) -> None:
    """Run a Coup game."""
    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and setup game
    game = CoupGame()
    game.setup(num_players=num_players or config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"num_players": num_players or config.num_players})

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    # Game loop
    turn_count = 0
    max_turns = 100  # Prevent infinite loops

    while not game.state.is_terminal() and turn_count < max_turns:
        turn_count += 1
        current_player = game.get_current_player()
        player_idx = game.state.current_player_idx

        # Check if player has influence
        if not game.board.has_influence(player_idx):
            # Advance to next player
            next_idx = (player_idx + 1) % game.num_players
            while not game.board.has_influence(next_idx):
                next_idx = (next_idx + 1) % game.num_players
            game.state.current_player_idx = next_idx
            continue

        # Capture state and board before
        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        # Refresh UI
        ui.refresh(game)

        # Get move from AI
        try:
            llm_output = current_player.agent.get_action(game, current_player)
        except Exception as e:
            print(f"⚠️  Error getting action: {e}")
            time.sleep(2)
            # Eliminate player
            game.board.reveal_random_influence(player_idx)
            game.board.reveal_random_influence(player_idx)
            continue

        # Create and validate action
        action = TakeTurnAction()

        # Enforce must-coup rule
        if game.board.coins[player_idx] >= 10 and llm_output.action != "coup":
            print(f"⚠️  Invalid: Must coup with 10+ coins! Auto-couping...")
            time.sleep(2)
            # Find a target
            targets = [
                i for i in range(game.num_players) if i != player_idx and game.board.has_influence(i)
            ]
            if targets:
                llm_output.action = "coup"
                llm_output.target_player = targets[0] + 1
            else:
                # No valid targets, eliminate self
                game.board.reveal_random_influence(player_idx)
                continue

        if action.validate(
            game,
            current_player,
            action=llm_output.action,
            target_player=llm_output.target_player,
            character_to_reveal=llm_output.character_to_reveal,
        ):
            # Show the move
            ui.render_move(
                game.state.get_current_player_name(),
                llm_output.action,
                f"Player {llm_output.target_player}" if llm_output.target_player else None,
                None,  # claimed character
                None,  # amount
                llm_output.reasoning,
            )

            action.apply(
                game,
                current_player,
                action=llm_output.action,
                target_player=llm_output.target_player,
                character_to_reveal=llm_output.character_to_reveal,
            )

            # Capture state and board after
            state_after = copy.deepcopy(game.state)
            board_after = copy.deepcopy(game.board)

            # Log turn to MongoDB (Coup is non-deterministic - random card reveals)
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
                    action_params={
                        "action": llm_output.action,
                        "target_player": llm_output.target_player,
                        "character_to_reveal": llm_output.character_to_reveal
                    },
                    action_valid=True,
                    llm_call_data=llm_call_data
                )

            # Reset invalid counter on success
            game.state.consecutive_invalid_actions = 0
        else:
            # Track consecutive invalid actions
            game.state.consecutive_invalid_actions += 1
            print(f"⚠️  Invalid action: {llm_output.action} (Strike {game.state.consecutive_invalid_actions}/3)")
            time.sleep(2)

            # Check for 3-strikes rule - player loses all influence
            if game.state.consecutive_invalid_actions >= 3:
                print(f"❌ Player {player_idx + 1} made 3 consecutive invalid moves - LOSES ALL INFLUENCE")
                # Reveal all influence
                for card in game.board.influence[player_idx]:
                    card.revealed = True
                game.state.consecutive_invalid_actions = 0  # Reset

            continue

        # Small delay
        time.sleep(1.5)

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Game ended
    ui.refresh(game)
    ui.render_game_end(game)


def main():
    """Main entry point."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Play Coup")
    parser.add_argument(
        "--num_players",
        type=int,
        default=None,
        help="Number of players (2-6, default: from config)"
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
