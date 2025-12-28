"""Tic-Tac-Toe game using boardgamepy framework."""

from pathlib import Path

from boardgamepy import GameRunner
from game import TicTacToeGame
from prompts import TicTacToePromptBuilder
from actions import MoveAction
import ui


class TicTacToeRunner(GameRunner):
    """Runner for TicTacToe with custom UI."""

    def render_move_ui(self, game, player, llm_output):
        """Render the move."""
        ui.render_move(
            game.state.current_player,
            llm_output.position,
            llm_output.reasoning,
        )


if __name__ == "__main__":
    TicTacToeRunner.main(
        game_class=TicTacToeGame,
        prompt_builder_class=TicTacToePromptBuilder,
        output_schema=MoveAction.OutputSchema,
        action_class=MoveAction,
        ui_module=ui,
        game_dir=Path(__file__).parent,
    )()
