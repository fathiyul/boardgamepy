"""Sushi Go! game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from game import SushiGoGame
from prompts import SushiGoPromptBuilder
from actions import PlayCardAction
from config import config
import ui


class SushiGoRunner(GameRunner):
    """Runner for Sushi Go with simultaneous play and rounds."""

    def run_turn(self, game, player, game_logger):
        """Handle a single player's card selection."""
        player_idx = player.player_idx

        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        if self.ui:
            self.ui.refresh(game)
        ui.render_card_selection(game, player_idx)

        # Get action from AI
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            if player_idx in game.state.waiting_for_players:
                game.state.waiting_for_players.remove(player_idx)
            return False

        action = PlayCardAction()

        # Get second card if provided (for chopsticks)
        second_card = getattr(llm_output, 'second_card', None)

        if action.validate(game, player, card_to_play=llm_output.card_to_play, second_card=second_card):
            if second_card:
                ui.render_play_action(player.team, f"{llm_output.card_to_play} + {second_card} (Chopsticks)", llm_output.reasoning)
            else:
                ui.render_play_action(player.team, llm_output.card_to_play, llm_output.reasoning)
            action.apply(game, player, card_to_play=llm_output.card_to_play, second_card=second_card)

            state_after = copy.deepcopy(game.state)
            board_after = copy.deepcopy(game.board)

            if game_logger.enabled:
                llm_call_data = None
                if hasattr(player.agent, '_last_llm_call'):
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
            return True
        else:
            print(f"Invalid card: {llm_output.card_to_play}")
            time.sleep(2)
            # Play a fallback card
            hand = game.board.hands[player_idx]
            if hand:
                fallback_card = hand[0]
                print(f"  Playing {fallback_card.name} instead...")
                action.apply(game, player, card_to_play=fallback_card.name)
            else:
                if player_idx in game.state.waiting_for_players:
                    game.state.waiting_for_players.remove(player_idx)
            return False

    def run_loop(self, game, game_logger):
        """Custom game loop with rounds and simultaneous play."""
        while not game.state.is_terminal():
            # Round loop
            while not game.board.is_round_over():
                if not game.state.waiting_for_players:
                    game.board.pass_hands()
                    game.state.waiting_for_players = set(range(game.num_players))
                    continue

                player = game.get_current_player()
                if player is None:
                    break

                self.run_turn(game, player, game_logger)
                time.sleep(0.5)

            # Round ended
            if self.ui:
                self.ui.refresh(game)
            game.end_round()
            ui.render_round_end(game)
            time.sleep(3)

    def on_game_end(self, game):
        """Show final game screen."""
        ui.render_game_end(game)


if __name__ == "__main__":
    SushiGoRunner.main(
        game_class=SushiGoGame,
        prompt_builder_class=SushiGoPromptBuilder,
        output_schema=PlayCardAction.OutputSchema,
        ui_module=ui,
        game_dir=Path(__file__).parent,
        default_num_players=config.num_players,
    )()
