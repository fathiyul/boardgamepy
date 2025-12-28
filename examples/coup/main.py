"""Coup game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from game import CoupGame
from prompts import CoupPromptBuilder
from actions import TakeTurnAction
from config import config
import ui


class CoupRunner(GameRunner):
    """Runner for Coup with custom turn logic."""

    def run_turn(self, game, player, game_logger):
        """Custom turn handling for Coup."""
        player_idx = game.state.current_player_idx

        # Check if player has influence
        if not game.board.has_influence(player_idx):
            self._advance_to_next_active_player(game)
            return True

        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        if self.ui:
            self.ui.refresh(game)

        # Get action from AI
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            game.board.reveal_random_influence(player_idx)
            game.board.reveal_random_influence(player_idx)
            return False

        # Enforce must-coup rule
        if game.board.coins[player_idx] >= 10 and llm_output.action != "coup":
            print("Invalid: Must coup with 10+ coins! Auto-couping...")
            time.sleep(2)
            targets = [
                i for i in range(game.num_players)
                if i != player_idx and game.board.has_influence(i)
            ]
            if targets:
                llm_output.action = "coup"
                llm_output.target_player = targets[0] + 1
            else:
                game.board.reveal_random_influence(player_idx)
                return False

        action = TakeTurnAction()
        params = {
            "action": llm_output.action,
            "target_player": llm_output.target_player,
            "character_to_reveal": llm_output.character_to_reveal,
        }

        if action.validate(game, player, **params):
            ui.render_move(
                game.state.get_current_player_name(),
                llm_output.action,
                f"Player {llm_output.target_player}" if llm_output.target_player else None,
                None,
                None,
                llm_output.reasoning,
            )

            action.apply(game, player, **params)

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
            print(f"Invalid action: {llm_output.action} (Strike {game.state.consecutive_invalid_actions}/3)")
            time.sleep(2)

            if game.state.consecutive_invalid_actions >= 3:
                print(f"Player {player_idx + 1} made 3 consecutive invalid moves - LOSES ALL INFLUENCE")
                for card in game.board.influence[player_idx]:
                    card.revealed = True
                game.state.consecutive_invalid_actions = 0

            return False

    def _advance_to_next_active_player(self, game):
        """Advance to next player with influence."""
        player_idx = game.state.current_player_idx
        next_idx = (player_idx + 1) % game.num_players
        while not game.board.has_influence(next_idx):
            next_idx = (next_idx + 1) % game.num_players
        game.state.current_player_idx = next_idx

    def run_loop(self, game, game_logger):
        """Custom game loop with turn limit."""
        turn_count = 0
        max_turns = 100

        while not game.state.is_terminal() and turn_count < max_turns:
            turn_count += 1
            player = game.get_current_player()
            if player is None:
                break

            success = self.run_turn(game, player, game_logger)
            if success:
                time.sleep(1.5)

        if turn_count >= max_turns:
            print("\nTurn limit reached!")

    def on_game_end(self, game):
        """Show final game screen."""
        if self.ui:
            self.ui.refresh(game)
        ui.render_game_end(game)


if __name__ == "__main__":
    CoupRunner.main(
        game_class=CoupGame,
        prompt_builder_class=CoupPromptBuilder,
        output_schema=TakeTurnAction.OutputSchema,
        ui_module=ui,
        game_dir=Path(__file__).parent,
        default_num_players=config.num_players,
    )()
