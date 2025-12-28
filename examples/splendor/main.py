"""Splendor game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from game import SplendorGame
from prompts import SplendorPromptBuilder
from actions import TakeGemsAction, PurchaseCardAction, ReserveCardAction, GameActionOutput
from config import config
import ui


class SplendorRunner(GameRunner):
    """Runner for Splendor with multiple action types."""

    def handle_gem_limit(self, game, player_idx):
        """Handle 10 gem limit by returning excess gems."""
        gems_to_return = game.check_gem_limit(player_idx)
        if gems_to_return:
            print(f"Player {player_idx + 1} has more than 10 gems! Returning excess...")
            return_str = ", ".join(
                f"{ui._get_gem_icon(gem)}x{count}" for gem, count in gems_to_return.items()
            )
            print(f"  Returning: {return_str}")
            game.board.return_gems(player_idx, gems_to_return)
            time.sleep(1.5)

    def run_turn(self, game, player, game_logger):
        """Custom turn handling for multiple action types."""
        player_idx = game.state.current_player_idx
        state_before = copy.deepcopy(game.state)

        if self.ui:
            self.ui.refresh(game)
        ui.render_player_details(game, player_idx)

        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            game.next_turn()
            return False

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
                    details = f"{llm_output.gem1}, {llm_output.gem2}, {llm_output.gem3}"
                ui.render_action("Take Gems", details)
                action.apply(game, player, **action_params)
                self.handle_gem_limit(game, player_idx)
                success = True
            else:
                print("Invalid gem taking action")

        elif action_type == "purchase":
            action = PurchaseCardAction()
            action_params = {"card_id": llm_output.card_id, "from_reserved": llm_output.from_reserved}
            if action.validate(game, player, **action_params):
                card = self._get_card_for_display(game, llm_output, player_idx)
                if card:
                    ui.render_action("Purchase Card", str(card))
                action.apply(game, player, **action_params)
                success = True
            else:
                print("Invalid card purchase")

        elif action_type == "reserve":
            action = ReserveCardAction()
            action_params = {"card_id": llm_output.card_id, "tier": llm_output.tier}
            if action.validate(game, player, **action_params):
                result = game.board.get_card_from_display(llm_output.card_id)
                if result:
                    card, tier = result
                    self._restore_card_to_display(game, card, tier)
                    ui.render_action("Reserve Card", str(card))
                action.apply(game, player, **action_params)
                self.handle_gem_limit(game, player_idx)
                success = True
            else:
                print("Invalid card reservation")

        if success:
            state_after = copy.deepcopy(game.state)

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

        time.sleep(1)
        return success

    def _get_card_for_display(self, game, llm_output, player_idx):
        """Get card info for display purposes."""
        if llm_output.from_reserved:
            for c in game.board.player_reserved[player_idx]:
                if c.card_id == llm_output.card_id:
                    return c
        else:
            result = game.board.get_card_from_display(llm_output.card_id)
            if result:
                card, tier = result
                self._restore_card_to_display(game, card, tier)
                return card
        return None

    def _restore_card_to_display(self, game, card, tier):
        """Temporarily restore card to display."""
        if tier == 1:
            game.board.tier1_display.append(card)
        elif tier == 2:
            game.board.tier2_display.append(card)
        else:
            game.board.tier3_display.append(card)

    def run_loop(self, game, game_logger):
        """Game loop with game end checking."""
        if self.ui:
            self.ui.refresh(game)
        time.sleep(2)

        while not game.state.is_terminal():
            player = game.get_current_player()
            if player is None:
                break

            self.run_turn(game, player, game_logger)
            game.check_game_end()

            if not game.state.is_over:
                game.next_turn()

    def on_game_end(self, game):
        """Show final game screen."""
        ui.render_game_end(game)


if __name__ == "__main__":
    SplendorRunner.main(
        game_class=SplendorGame,
        prompt_builder_class=SplendorPromptBuilder,
        output_schema=GameActionOutput,
        ui_module=ui,
        game_dir=Path(__file__).parent,
        default_num_players=config.num_players,
    )()
