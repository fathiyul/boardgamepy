"""Splendor game with human player."""

import copy
import time
from pathlib import Path

from langchain_openai import ChatOpenAI
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger
from game import SplendorGame
from prompts import SplendorPromptBuilder
from actions import (
    TakeGemsAction,
    PurchaseCardAction,
    ReserveCardAction,
    GameActionOutput,
)
from human_agent import SplendorHumanAgent
from config import config
from cards import GemType
import ui

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()


def setup_players(game: SplendorGame, logging_config: LoggingConfig) -> tuple[int, str]:
    """Configure players - ask user which player they want to be."""
    print("\n" + "=" * 70)
    print("SPLENDOR")
    print("=" * 70)

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
        choice = input(f"\nChoose position (1-{game.num_players}): ").strip()
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

    # Create LLM for AI players
    if os.getenv("OPENROUTER_API_KEY"):
        base_llm = ChatOpenAI(
            model=logging_config.openrouter_model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        model_name = logging_config.openrouter_model
    else:
        base_llm = ChatOpenAI(
            model=logging_config.openai_model,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        model_name = logging_config.openai_model

    # Configure players
    for i, player in enumerate(game.players):
        if i == human_player_idx:
            player.agent = SplendorHumanAgent()
            player.agent_type = "human"
            player.name = player_name
        else:
            base_agent = LLMAgent(
                llm=base_llm,
                prompt_builder=SplendorPromptBuilder(),
                output_schema=GameActionOutput,
            )
            player.agent = LoggedLLMAgent(base_agent, model_name)
            player.agent_type = "ai"
            player.name = f"AI {i + 1}"

    print("=" * 70)
    input("Press Enter to start the game...")
    print("\n")

    return human_player_idx, player_name


def render_human_view(game: SplendorGame, human_player_idx: int):
    """Render the game from the human player's perspective."""
    ui.term.clear()
    ui.render_header(game)
    ui.render_turn_info(game)
    ui.render_gem_bank(game)
    ui.render_nobles(game)
    ui.render_card_display(game)

    # Player status with human's perspective
    print(f"{ui.term.BOLD}Players:{ui.term.RESET}")

    for i in range(game.num_players):
        player_name = f"Player {i + 1}"
        color = ui.term.get_player_color(i)

        # Calculate score
        card_points = game.board.get_player_points(i)
        nobles = game.state.player_nobles.get(i, [])
        noble_points = len(nobles) * 3
        total = card_points + noble_points

        # Gems
        gem_count = game.board.get_total_gems(i)

        # Bonuses
        bonuses = game.board.get_player_bonuses(i)
        bonus_str = ", ".join(
            f"{ui._get_gem_icon(gem)}×{count}"
            for gem, count in bonuses.items()
            if count > 0
        )

        # Cards
        num_cards = len(game.board.player_cards[i])
        num_reserved = len(game.board.player_reserved[i])

        info = f"  {color}{player_name:10}{ui.term.RESET} "
        info += f"Score: {ui.term.FG_YELLOW}{total}{ui.term.RESET} "
        info += f"({card_points}+{noble_points}) "
        info += f"| Gems: {gem_count}/10 "
        info += f"| Cards: {num_cards} "

        if num_reserved > 0:
            info += f"| Reserved: {num_reserved} "

        if bonus_str:
            info += f"| Bonus: {bonus_str}"

        if i == human_player_idx:
            info += " (YOU)"

        print(info)

    print()


def handle_gem_limit(game: SplendorGame, player_idx: int):
    """Handle 10 gem limit - for human, let them choose which to return."""
    total = game.board.get_total_gems(player_idx)
    if total <= 10:
        return

    gems_to_return = total - 10
    print(f"\nYou have {total} gems! You must return {gems_to_return} gem(s).")

    returned = {}
    remaining = gems_to_return

    while remaining > 0:
        # Show current gems
        gems = game.board.player_gems[player_idx]
        print(f"\nYour gems (must return {remaining} more):")
        available = []
        for gem in [
            GemType.DIAMOND,
            GemType.SAPPHIRE,
            GemType.EMERALD,
            GemType.RUBY,
            GemType.ONYX,
            GemType.GOLD,
        ]:
            count = gems[gem] - returned.get(gem, 0)
            if count > 0:
                available.append(gem.value)
                print(f"  {ui._get_gem_icon(gem)} {gem.value}: {count}")

        choice = input("\nWhich gem to return? ").strip().capitalize()

        if choice not in available:
            print(f"  Please choose from: {', '.join(available)}")
            continue

        gem_type = GemType[choice.upper()]
        returned[gem_type] = returned.get(gem_type, 0) + 1
        remaining -= 1

    # Return the gems
    game.board.return_gems(player_idx, returned)
    return_str = ", ".join(
        f"{ui._get_gem_icon(gem)}x{count}" for gem, count in returned.items()
    )
    print(f"\nReturned: {return_str}")
    time.sleep(1)


def run_game():
    """Run Splendor with human and AI players."""

    # Load configuration
    logging_config = LoggingConfig.load(Path(__file__).parent)
    game_logger = GameLogger(logging_config)

    # Create game
    game = SplendorGame()
    game.setup(num_players=config.num_players)

    # Log game start
    if game_logger.enabled:
        game_logger.start_game(game, {"mode": "human_playable"})

    # Configure players
    human_player_idx, player_name = setup_players(game, logging_config)

    # Initial view
    render_human_view(game, human_player_idx)
    time.sleep(2)

    # Main game loop
    while not game.state.is_terminal():
        player_idx = game.state.current_player_idx
        player = game.players[player_idx]

        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        render_human_view(game, human_player_idx)

        if player.agent_type == "human":
            print(f"\n>>> YOUR TURN <<<\n")
        else:
            ui.render_player_details(game, player_idx)
            print(f"\n[AI] Player {player_idx + 1} is thinking...\n")

        # Get action
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            game.next_turn()
            continue

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
            if action.validate(game, player, **action_params):
                if llm_output.take_two:
                    details = f"2x{llm_output.gem1}"
                else:
                    gems = [
                        g
                        for g in [llm_output.gem1, llm_output.gem2, llm_output.gem3]
                        if g
                    ]
                    details = ", ".join(gems)
                ui.render_action("Take Gems", details)
                action.apply(game, player, **action_params)
                handle_gem_limit(game, player_idx)
                success = True
            else:
                print("Invalid gem taking action")

        elif action_type == "purchase":
            action = PurchaseCardAction()
            action_params = {
                "card_id": llm_output.card_id,
                "from_reserved": llm_output.from_reserved,
            }
            if action.validate(game, player, **action_params):
                # Get card for display
                card_str = f"Card {llm_output.card_id}"
                if llm_output.from_reserved:
                    for c in game.board.player_reserved[player_idx]:
                        if c.card_id == llm_output.card_id:
                            card_str = str(c)
                            break
                else:
                    for c in (
                        game.board.tier1_display
                        + game.board.tier2_display
                        + game.board.tier3_display
                    ):
                        if c.card_id == llm_output.card_id:
                            card_str = str(c)
                            break

                ui.render_action("Purchase Card", card_str)
                action.apply(game, player, **action_params)
                success = True
            else:
                print("Invalid card purchase")

        elif action_type == "reserve":
            action = ReserveCardAction()
            action_params = {"card_id": llm_output.card_id, "tier": llm_output.tier}
            if action.validate(game, player, **action_params):
                # Get card for display
                card_str = f"Card {llm_output.card_id}"
                for c in (
                    game.board.tier1_display
                    + game.board.tier2_display
                    + game.board.tier3_display
                ):
                    if c.card_id == llm_output.card_id:
                        card_str = str(c)
                        break

                ui.render_action("Reserve Card", card_str)
                action.apply(game, player, **action_params)
                handle_gem_limit(game, player_idx)
                success = True
            else:
                print("Invalid card reservation")

        if success:
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
                    action_params={**action_params, "action_type": action_type},
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )
        else:
            print("Turn failed, skipping...")
            time.sleep(2)

        # Check for nobles
        qualifying_nobles = game.board.check_nobles(player_idx)
        if qualifying_nobles:
            noble = qualifying_nobles[0]
            game.board.claim_noble(player_idx, noble)
            game.state.player_nobles[player_idx].append(noble)
            ui.render_noble_claim(player.team, noble)
            time.sleep(2)

        # Check game end
        game.check_game_end()

        if not game.state.is_over:
            game.next_turn()

        time.sleep(1 if player.agent_type == "ai" else 0.5)

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
