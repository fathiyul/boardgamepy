"""Splendor game using boardgamepy framework."""

import time
import logging
from pathlib import Path
import copy

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import SplendorGame
from prompts import SplendorPromptBuilder
from actions import TakeGemsAction, PurchaseCardAction, ReserveCardAction, GameActionOutput
from config import config
import ui

# Suppress HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def setup_ai_agents(game: SplendorGame, logging_config: LoggingConfig) -> None:
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
    prompt_builder = SplendorPromptBuilder()

    for player in game.players:
        base_agent = LLMAgent(
            llm=llm,
            prompt_builder=prompt_builder,
            output_schema=GameActionOutput,
        )
        player.agent = LoggedLLMAgent(base_agent, model_name)


def handle_gem_limit(game: SplendorGame, player_idx: int) -> None:
    """Handle 10 gem limit by returning excess gems."""
    gems_to_return = game.check_gem_limit(player_idx)
    if gems_to_return:
        player_name = f"Player {player_idx + 1}"
        print(f"⚠️  {player_name} has more than 10 gems! Returning excess...")

        # Show what's being returned
        from cards import GemType

        return_str = ", ".join(
            f"{ui._get_gem_icon(gem)}×{count}" for gem, count in gems_to_return.items()
        )
        print(f"  Returning: {return_str}")

        game.board.return_gems(player_idx, gems_to_return)
        time.sleep(1.5)


def run_turn(game: SplendorGame, game_logger) -> None:
    """Run a single player turn."""
    current_player = game.get_current_player()
    player_idx = game.state.current_player_idx

    # Capture state before
    state_before = copy.deepcopy(game.state)

    # Refresh UI
    ui.refresh(game)
    ui.render_player_details(game, player_idx)

    # Get action from AI
    try:
        llm_output = current_player.agent.get_action(game, current_player)
    except Exception as e:
        print(f"⚠️  Error getting action: {e}")
        time.sleep(2)
        # Skip turn
        game.next_turn()
        return

    # Process action based on type
    action_type = llm_output.action_type
    success = False
    action_params = {}

    if action_type == "take_gems":
        action = TakeGemsAction()
        action_params = {
            "gem1": llm_output.gem1,
            "gem2": llm_output.gem2,
            "gem3": llm_output.gem3,
            "take_two": llm_output.take_two,
        }
        if action.validate(game, current_player, **action_params):
            # Show action
            if llm_output.take_two:
                details = f"2×{llm_output.gem1}"
            else:
                details = f"{llm_output.gem1}, {llm_output.gem2}, {llm_output.gem3}"

            ui.render_action("Take Gems", details)

            action.apply(game, current_player, **action_params)

            # Check gem limit
            handle_gem_limit(game, player_idx)

            success = True
        else:
            print(f"⚠️  Invalid gem taking action")

    elif action_type == "purchase":
        action = PurchaseCardAction()
        action_params = {"card_id": llm_output.card_id, "from_reserved": llm_output.from_reserved}
        if action.validate(game, current_player, **action_params):
            # Get card info before purchase
            if llm_output.from_reserved:
                card = None
                for c in game.board.player_reserved[player_idx]:
                    if c.card_id == llm_output.card_id:
                        card = c
                        break
            else:
                result = game.board.get_card_from_display(llm_output.card_id)
                if result:
                    card, tier = result
                    # Put it back temporarily
                    if tier == 1:
                        game.board.tier1_display.append(card)
                    elif tier == 2:
                        game.board.tier2_display.append(card)
                    else:
                        game.board.tier3_display.append(card)

            if card:
                ui.render_action("Purchase Card", str(card))

            action.apply(game, current_player, **action_params)
            success = True
        else:
            print(f"⚠️  Invalid card purchase")

    elif action_type == "reserve":
        action = ReserveCardAction()
        action_params = {"card_id": llm_output.card_id, "tier": llm_output.tier}
        if action.validate(game, current_player, **action_params):
            # Get card info
            result = game.board.get_card_from_display(llm_output.card_id)
            if result:
                card, tier = result
                # Put it back temporarily
                if tier == 1:
                    game.board.tier1_display.append(card)
                elif tier == 2:
                    game.board.tier2_display.append(card)
                else:
                    game.board.tier3_display.append(card)

                ui.render_action("Reserve Card", str(card))

            action.apply(game, current_player, **action_params)

            # Check gem limit (from gold token)
            handle_gem_limit(game, player_idx)

            success = True
        else:
            print(f"⚠️  Invalid card reservation")

    if success:
        # Capture state after
        state_after = copy.deepcopy(game.state)

        # Log turn
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
                action_params={**action_params, "action_type": action_type},
                action_valid=True,
                llm_call_data=llm_call_data
            )
    else:
        print(f"⚠️  Turn failed, skipping...")
        time.sleep(2)

    # Check for nobles
    qualifying_nobles = game.board.check_nobles(player_idx)
    if qualifying_nobles:
        noble = qualifying_nobles[0]
        game.board.claim_noble(player_idx, noble)
        game.state.player_nobles[player_idx].append(noble)
        ui.render_noble_claim(current_player.team, noble)
        time.sleep(2)

    time.sleep(1)


def run_game(num_players: int | None = None) -> None:
    """Run a Splendor game."""
    # Load logging configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)

    # Create game logger
    game_logger = GameLogger(logging_config)

    # Create and setup game
    game = SplendorGame()
    game.setup(num_players=num_players or config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"num_players": num_players or config.num_players})

    # Configure AI agents
    setup_ai_agents(game, logging_config)

    # Initial display
    ui.refresh(game)
    time.sleep(2)

    # Game loop
    while not game.state.is_terminal():
        run_turn(game, game_logger)

        # Check for game end
        game.check_game_end()

        if not game.state.is_over:
            game.next_turn()

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
        # You can customize number of players here (2-4, default 3)
        run_game(num_players=config.num_players)
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
