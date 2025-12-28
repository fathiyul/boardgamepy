"""Love Letter game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from game import LoveLetterGame
from prompts import LoveLetterPromptBuilder
from actions import PlayCardAction
from config import config
import ui


class LoveLetterRunner(GameRunner):
    """Runner for Love Letter with round-based gameplay."""

    def run_turn(self, game, player, game_logger):
        """Custom turn handling for Love Letter."""
        player_idx = game.state.current_player_idx

        # Check if player is eliminated
        if player_idx in game.board.eliminated:
            self._advance_to_next_active_player(game)
            return True

        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        # Draw card for turn
        if game.board.deck:
            drawn_card = game.board.deck[-1]
            game.draw_card_for_turn()
            ui.render_draw(player_idx, drawn_card)

        if self.ui:
            self.ui.refresh(game)

        # Get action from AI
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            game.board.eliminate_player(player_idx)
            return False

        ui.render_move(
            game.state.get_current_player_name(),
            llm_output.card_to_play,
            llm_output.target_player,
            llm_output.guess_card,
            llm_output.reasoning,
        )

        action = PlayCardAction()
        params = {
            "card_to_play": llm_output.card_to_play,
            "target_player": llm_output.target_player,
            "guess_card": llm_output.guess_card,
        }

        if action.validate(game, player, **params):
            result = action.apply(game, player, **params)
            ui.render_action_result(result)

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
                    action_params=params,
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )

            game.state.consecutive_invalid_actions = 0
            return True
        else:
            game.state.consecutive_invalid_actions += 1
            print(f"Invalid move: {llm_output.card_to_play} (Strike {game.state.consecutive_invalid_actions}/3)")
            time.sleep(2)

            if game.state.consecutive_invalid_actions >= 3:
                print(f"Player {player_idx + 1} made 3 consecutive invalid moves - ELIMINATED")
                game.board.eliminate_player(player_idx)
                game.state.consecutive_invalid_actions = 0

            self._advance_to_next_active_player(game)
            return False

    def _advance_to_next_active_player(self, game):
        """Advance to next non-eliminated player."""
        player_idx = game.state.current_player_idx
        next_idx = (player_idx + 1) % game.num_players
        while next_idx in game.board.eliminated:
            next_idx = (next_idx + 1) % game.num_players
        game.state.current_player_idx = next_idx

    def run_loop(self, game, game_logger):
        """Custom game loop with multiple rounds."""
        while not game.state.is_terminal():
            # Round loop
            while not game.state.round_over:
                player = game.get_current_player()
                if player is None:
                    break

                success = self.run_turn(game, player, game_logger)
                if success:
                    time.sleep(1.5)

            # Round ended
            if self.ui:
                self.ui.refresh(game)
            ui.render_round_end(game)
            time.sleep(3)

            if game.state.is_over:
                break

            game.start_new_round()

    def on_game_end(self, game):
        """Show final game screen."""
        ui.render_game_end(game)


if __name__ == "__main__":
    LoveLetterRunner.main(
        game_class=LoveLetterGame,
        prompt_builder_class=LoveLetterPromptBuilder,
        output_schema=PlayCardAction.OutputSchema,
        ui_module=ui,
        game_dir=Path(__file__).parent,
        default_num_players=config.num_players,
    )()
