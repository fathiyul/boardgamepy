"""Love Letter game using boardgamepy framework."""

import time
import argparse
from pathlib import Path
import copy

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import LoveLetterGame
from prompts import LoveLetterPromptBuilder
from actions import PlayCardAction
from config import config
import ui


def setup_ai_agents(game: LoveLetterGame, logging_config: LoggingConfig) -> None:
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
    prompt_builder = LoveLetterPromptBuilder()

    for player in game.players:
        base_agent = LLMAgent(
            llm=llm,
            prompt_builder=prompt_builder,
            output_schema=PlayCardAction.OutputSchema,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def run_game(num_players: int | None = None, target_tokens: int | None = None) -> None:
    """Run a Love Letter game."""
    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and setup game
    game = LoveLetterGame()
    game.setup(num_players=num_players or config.num_players, target_tokens=target_tokens)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {
            "num_players": num_players or config.num_players,
            "target_tokens": game.state.target_tokens
        })

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    # Game loop (multiple rounds)
    while not game.state.is_terminal():
        # Round loop
        while not game.state.round_over:
            current_player = game.get_current_player()
            player_idx = game.state.current_player_idx

            # Check if player is eliminated
            if player_idx in game.board.eliminated:
                # Advance to next player
                next_idx = (player_idx + 1) % game.num_players
                while next_idx in game.board.eliminated:
                    next_idx = (next_idx + 1) % game.num_players
                game.state.current_player_idx = next_idx
                continue

            # Capture state before
            state_before = copy.deepcopy(game.state)

            # Draw card for turn
            drawn_card = None
            if game.board.deck:
                # Show what card is being drawn
                drawn_card = game.board.deck[-1]  # Peek at top card
                game.draw_card_for_turn()
                ui.render_draw(player_idx, drawn_card)

            # Refresh UI
            ui.refresh(game)

            # Get move from AI
            try:
                llm_output = current_player.agent.get_action(game, current_player)
            except Exception as e:
                print(f"⚠️  Error getting action: {e}")
                time.sleep(2)
                # Skip this player
                game.board.eliminate_player(player_idx)
                continue

            # Show the move
            ui.render_move(
                game.state.get_current_player_name(),
                llm_output.card_to_play,
                llm_output.target_player,
                llm_output.guess_card,
                llm_output.reasoning,
            )

            # Create and validate action
            action = PlayCardAction()

            if action.validate(
                game,
                current_player,
                card_to_play=llm_output.card_to_play,
                target_player=llm_output.target_player,
                guess_card=llm_output.guess_card,
            ):
                result = action.apply(
                    game,
                    current_player,
                    card_to_play=llm_output.card_to_play,
                    target_player=llm_output.target_player,
                    guess_card=llm_output.guess_card,
                )

                # Show action result with emojis
                ui.render_action_result(result)

                # Capture state after
                state_after = copy.deepcopy(game.state)

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
                        board_before="",
                        board_after="",
                        action=action,
                        action_params={
                            "card_to_play": llm_output.card_to_play,
                            "target_player": llm_output.target_player,
                            "guess_card": llm_output.guess_card
                        },
                        action_valid=True,
                        llm_call_data=llm_call_data
                    )
            else:
                print(f"⚠️  Invalid move: {llm_output.card_to_play}")
                time.sleep(2)
                # Eliminate player for invalid move
                game.board.eliminate_player(player_idx)
                continue

            # Small delay
            time.sleep(1.5)

        # Round ended
        ui.refresh(game)
        ui.render_round_end(game)
        time.sleep(3)

        # Check if game is over
        if game.state.is_over:
            break

        # Start new round
        game.start_new_round()

    # Log game end
    if game_logger.enabled:
        game_logger.end_game(game)

    # Game ended
    ui.render_game_end(game)


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Play Love Letter")
    parser.add_argument(
        "--num_players",
        type=int,
        default=None,
        help="Number of players (2-4, default: from config)"
    )
    parser.add_argument(
        "--target_tokens",
        type=int,
        default=None,
        help="Number of tokens to win (default: 7 for 2p, 5 for 3p, 4 for 4p)"
    )
    args = parser.parse_args()

    if not config.OPENAI_API_KEY and not config.OPENROUTER_API_KEY:
        print("❌ Error: No API key found!")
        print("Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
        return

    try:
        run_game(num_players=args.num_players, target_tokens=args.target_tokens)
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
