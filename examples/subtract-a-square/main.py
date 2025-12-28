"""Subtract-a-Square game using boardgamepy framework."""

from pathlib import Path

from boardgamepy import GameRunner
from game import SubtractASquareGame
from prompts import SubtractASquarePromptBuilder
from actions import RemoveAction
import ui


class SubtractASquareRunner(GameRunner):
    """Runner for Subtract-a-Square with custom UI."""

    def render_move_ui(self, game, player, llm_output):
        """Render the move."""
        ui.render_move(
            game.state.current_player,
            llm_output.amount,
            llm_output.reasoning,
        )


if __name__ == "__main__":
    SubtractASquareRunner.main(
        game_class=SubtractASquareGame,
        prompt_builder_class=SubtractASquarePromptBuilder,
        output_schema=RemoveAction.OutputSchema,
        action_class=RemoveAction,
        ui_module=ui,
        game_dir=Path(__file__).parent,
    )()
