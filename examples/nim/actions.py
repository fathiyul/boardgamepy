"""Nim game actions."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

from boardgamepy import Action

if TYPE_CHECKING:
    from game import NimGame
    from boardgamepy.core.player import Player


class RemoveOutput(BaseModel):
    """LLM structured output for removing objects."""

    pile: int = Field(..., description="Pile number to remove from (1-based)", ge=1)
    count: int = Field(..., description="Number of objects to remove", ge=1)
    reasoning: str | None = Field(None, description="Explanation of move strategy")


class RemoveAction(Action["NimGame"]):
    """Action for removing objects from a pile."""

    name = "remove"
    display_name = "Remove Objects"
    OutputSchema = RemoveOutput

    def validate(self, game: "NimGame", player: "Player", pile: int, count: int) -> bool:
        """
        Validate removal.

        Move is invalid if:
        - Game is over
        - Pile number is invalid (must be 1-based and <= number of piles)
        - Count is invalid (< 1 or > pile size)
        - Pile is empty
        """
        if game.state.is_over:
            return False

        # Convert to 0-based index
        pile_index = pile - 1

        if not game.board.is_pile_valid(pile_index):
            return False

        pile_size = game.board.get_pile_size(pile_index)

        if count < 1 or count > pile_size:
            return False

        return True

    def apply(self, game: "NimGame", player: "Player", pile: int, count: int) -> None:
        """
        Apply removal.

        Removes objects from pile, logs action, checks for game end,
        and switches player.
        """
        # Convert to 0-based index
        pile_index = pile - 1

        # Remove objects
        game.board.remove_from_pile(pile_index, count)

        # Log to history
        game.history.add_action(
            self, player, pile=pile, count=count, player_name=game.state.current_player
        )

        # Check if game is over (all piles empty)
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
        self, player: "Player", pile: int, count: int, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "remove",
            "player": player_name,
            "pile": pile,
            "count": count,
        }
