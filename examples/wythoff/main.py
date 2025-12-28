"""Wythoff's Game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from game import WythoffGame
from prompts import WythoffPromptBuilder
from actions import RemoveFromAAction, RemoveFromBAction, RemoveFromBothAction
import ui


class WythoffRunner(GameRunner):
    """Runner for Wythoff with custom turn logic (multiple action types)."""

    def run_turn(self, game, player, game_logger):
        """Custom turn handling for multiple action types."""
        # Capture state before
        state_before = copy.deepcopy(game.state)

        # Refresh UI
        if self.ui:
            self.ui.refresh(game)

        # Get action from AI
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            return False

        # Render move
        ui.render_move(
            game.state.current_player,
            llm_output.move_type,
            llm_output.count,
            llm_output.reasoning,
        )

        # Select action class based on move type
        move_type = llm_output.move_type
        count = llm_output.count

        if move_type == "pile_a":
            action = RemoveFromAAction()
        elif move_type == "pile_b":
            action = RemoveFromBAction()
        elif move_type == "both":
            action = RemoveFromBothAction()
        else:
            print(f"Invalid move type: {move_type}")
            time.sleep(2)
            return False

        if action.validate(game, player, count=count):
            action.apply(game, player, count=count)

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
                    action_params={"move_type": move_type, "count": count},
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )
            return True
        else:
            print(f"Invalid move: {move_type} with count {count}")
            time.sleep(2)
            return False


if __name__ == "__main__":
    WythoffRunner.main(
        game_class=WythoffGame,
        prompt_builder_class=WythoffPromptBuilder,
        output_schema=RemoveFromAAction.OutputSchema,
        ui_module=ui,
        game_dir=Path(__file__).parent,
    )()
