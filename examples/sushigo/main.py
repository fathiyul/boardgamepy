"""Sushi Go! game using boardgamepy framework."""

import time
import logging
from pathlib import Path
import copy

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import SushiGoGame
from prompts import SushiGoPromptBuilder
from actions import PlayCardAction
from config import config
import ui

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def setup_ai_agents(game: SushiGoGame, logging_config: LoggingConfig) -> None:
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
    prompt_builder = SushiGoPromptBuilder()

    for player in game.players:
        base_agent = LLMAgent(
            llm=llm,
            prompt_builder=prompt_builder,
            output_schema=PlayCardAction.OutputSchema,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def run_game(num_players: int | None = None) -> None:
    """Run a Sushi Go! game."""
    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and setup game
    game = SushiGoGame()
    game.setup(num_players=num_players or config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"num_players": num_players or config.num_players})

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    # Game loop (3 rounds)
    while not game.state.is_terminal():
        # Round loop - each player plays all their cards
        while not game.board.is_round_over():
            # Check if all players have played this turn
            if not game.state.waiting_for_players:
                # All played, pass hands
                game.board.pass_hands()
                game.state.waiting_for_players = set(range(game.num_players))
                continue

            # Get next player who needs to play
            current_player = game.get_current_player()
            player_idx = int(current_player.team.split()[-1]) - 1

            # Capture state before
            state_before = copy.deepcopy(game.state)
            board_before = copy.deepcopy(game.board)

            # Refresh UI
            ui.refresh(game)

            # Show available card options
            ui.render_card_selection(game, player_idx)

            # Get move from AI
            try:
                llm_output = current_player.agent.get_action(game, current_player)
            except Exception as e:
                print(f"⚠️  Error getting action: {e}")
                time.sleep(2)
                # Skip this player's turn (remove from waiting)
                if player_idx in game.state.waiting_for_players:
                    game.state.waiting_for_players.remove(player_idx)
                continue

            # Create and validate action
            action = PlayCardAction()

            if action.validate(game, current_player, card_to_play=llm_output.card_to_play):
                # Show the play
                ui.render_play_action(
                    current_player.team,
                    llm_output.card_to_play,
                    llm_output.reasoning,
                )

                action.apply(game, current_player, card_to_play=llm_output.card_to_play)

                # Capture state after
                state_after = copy.deepcopy(game.state)
                board_after = copy.deepcopy(game.board)

                # Log turn to MongoDB
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
                        action_params={"card_to_play": llm_output.card_to_play},
                        action_valid=True,
                        llm_call_data=llm_call_data
                    )
            else:
                print(f"⚠️  Invalid card: {llm_output.card_to_play}")
                time.sleep(2)
                # Play a random valid card
                hand = game.board.hands[player_idx]
                if hand:
                    fallback_card = hand[0]
                    print(f"  Playing {fallback_card.name} instead...")
                    action.apply(game, current_player, card_to_play=fallback_card.name)
                else:
                    # No cards, skip
                    if player_idx in game.state.waiting_for_players:
                        game.state.waiting_for_players.remove(player_idx)

            time.sleep(0.5)

        # Round ended
        ui.refresh(game)
        game.end_round()
        ui.render_round_end(game)
        time.sleep(3)

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Game ended
    ui.render_game_end(game)


def main():
    """Main entry point."""
    if not config.OPENAI_API_KEY and not config.OPENROUTER_API_KEY:
        print("❌ Error: No API key found!")
        print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
        return

    try:
        # You can customize number of players here (2-5, default 4)
        run_game(num_players=config.num_players)
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
