"""Subtract-a-Square game actions."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

from boardgamepy import Action

if TYPE_CHECKING:
    from game import SubtractASquareGame
    from boardgamepy.core.player import Player


class RemoveOutput(BaseModel):
    """LLM structured output for removing objects."""

    amount: int = Field(..., description="Perfect square number to remove (1, 4, 9, 16, ...)", ge=1)
    reasoning: str | None = Field(None, description="Explanation of move strategy")


class RemoveAction(Action["SubtractASquareGame"]):
    """Action for removing a perfect square number of objects from the pile."""

    name = "remove"
    display_name = "Remove Perfect Square"
    OutputSchema = RemoveOutput

    def validate(
        self, game: "SubtractASquareGame", player: "Player", amount: int
    ) -> bool:
        """
        Validate removal.

        Move is invalid if:
        - Game is over
        - Amount is not a perfect square
        - Amount is greater than pile count
        """
        if game.state.is_over:
            return False

        if not game.board.is_perfect_square(amount):
            return False

        if amount > game.board.count:
            return False

        return True

    def apply(self, game: "SubtractASquareGame", player: "Player", amount: int) -> None:
        """
        Apply removal.

        Removes objects from pile, logs action, checks for game end,
        and switches player.
        """
        # Remove objects
        game.board.remove(amount)

        # Log to history
        game.history.add_action(
            self, player, amount=amount, player_name=game.state.current_player
        )

        # Check if game is over (pile empty)
        if game.board.is_empty():
            # The player who just moved took the last object and wins
            game.state.is_over = True
            game.state.winner = game.state.current_player
            return

        # Switch player
        game.state.current_player = (
            "Player 2" if game.state.current_player == "Player 1" else "Player 1"
        )

    def to_history_record(
        self, player: "Player", amount: int, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "remove",
            "player": player_name,
            "amount": amount,
        }
