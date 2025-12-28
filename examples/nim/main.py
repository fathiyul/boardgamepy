"""Nim game using boardgamepy framework."""

from pathlib import Path

from boardgamepy import GameRunner
from game import NimGame
from prompts import NimPromptBuilder
from actions import RemoveAction
import ui


class NimRunner(GameRunner):
    """Runner for Nim with custom UI."""

    def render_move_ui(self, game, player, llm_output):
        """Render the move."""
        ui.render_move(
            game.state.current_player,
            llm_output.pile,
            llm_output.count,
            llm_output.reasoning,
        )


if __name__ == "__main__":
    NimRunner.main(
        game_class=NimGame,
        prompt_builder_class=NimPromptBuilder,
        output_schema=RemoveAction.OutputSchema,
        action_class=RemoveAction,
        ui_module=ui,
        game_dir=Path(__file__).parent,
    )()
