"""Tic-Tac-Toe game actions."""

from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field

from boardgamepy import Action

if TYPE_CHECKING:
    from game import TicTacToeGame
    from boardgamepy.core.player import Player


class MoveOutput(BaseModel):
    """LLM structured output for making a move."""

    position: int = Field(
        ..., description="Position to place mark (1-9)", ge=1, le=9
    )
    reasoning: str | None = Field(None, description="Explanation of move choice")


class MoveAction(Action["TicTacToeGame"]):
    """Action for placing a mark (X or O) on the board."""

    name = "move"
    display_name = "Place Mark"
    OutputSchema = MoveOutput

    def validate(self, game: "TicTacToeGame", player: "Player", position: int) -> bool:
        """
        Validate move.

        Move is invalid if:
        - Game is over
        - Position is out of range (1-9)
        - Position is already taken
        """
        if game.state.is_over:
            return False

        if position < 1 or position > 9:
            return False

        return game.board.is_position_empty(position)

    def apply(self, game: "TicTacToeGame", player: "Player", position: int) -> None:
        """
        Apply move.

        Places the mark, checks for winner, and switches player.
        """
        # Place the mark
        mark = game.state.current_player
        game.board.place_mark(position, mark)

        # Log to history
        game.history.add_action(self, player, position=position, mark=mark)

        # Check for winner
        winner = game.board.check_winner()
        if winner:
            game.state.is_over = True
            game.state.winner = winner
            return

        # Check for draw
        if game.board.is_full():
            game.state.is_over = True
            game.state.winner = "Draw"
            return

        # Switch player
        game.state.current_player = "O" if mark == "X" else "X"

    def to_history_record(
        self, player: "Player", position: int, mark: str, **params
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "move",
            "player": mark,
            "position": position,
        }
