"""Wythoff's Game actions."""

from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field

from boardgamepy import Action

if TYPE_CHECKING:
    from game import WythoffGame
    from boardgamepy.core.player import Player


class WythoffMoveOutput(BaseModel):
    """LLM structured output for Wythoff's Game moves."""

    move_type: Literal["pile_a", "pile_b", "both"] = Field(
        ...,
        description="Type of move: 'pile_a' (remove from A only), 'pile_b' (remove from B only), 'both' (remove same amount from both)",
    )
    count: int = Field(..., description="Number of objects to remove (must be at least 1)")
    reasoning: str | None = Field(None, description="Explanation of move strategy")


class RemoveFromAAction(Action["WythoffGame"]):
    """Action for removing objects from pile A only."""

    name = "remove_a"
    display_name = "Remove from Pile A"
    OutputSchema = WythoffMoveOutput

    def validate(self, game: "WythoffGame", player: "Player", count: int) -> bool:
        """Validate removal from pile A."""
        if game.state.is_over:
            return False
        if count < 1:
            return False
        if count > game.board.pile_a:
            return False
        return True

    def apply(self, game: "WythoffGame", player: "Player", count: int) -> None:
        """Apply removal from pile A."""
        game.board.remove_from_a(count)

        # Log to history
        game.history.add_action(
            self, player, count=count, player_name=game.state.current_player
        )

        # Check if game is over
        if game.board.is_empty():
            game.state.is_over = True
            game.state.winner = game.state.current_player
            return

        # Switch player
        game.state.current_player = (
            "Player 2" if game.state.current_player == "Player 1" else "Player 1"
        )

    def to_history_record(
        self, player: "Player", count: int, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "remove_a",
            "player": player_name,
            "count": count,
        }


class RemoveFromBAction(Action["WythoffGame"]):
    """Action for removing objects from pile B only."""

    name = "remove_b"
    display_name = "Remove from Pile B"
    OutputSchema = WythoffMoveOutput

    def validate(self, game: "WythoffGame", player: "Player", count: int) -> bool:
        """Validate removal from pile B."""
        if game.state.is_over:
            return False
        if count < 1:
            return False
        if count > game.board.pile_b:
            return False
        return True

    def apply(self, game: "WythoffGame", player: "Player", count: int) -> None:
        """Apply removal from pile B."""
        game.board.remove_from_b(count)

        # Log to history
        game.history.add_action(
            self, player, count=count, player_name=game.state.current_player
        )

        # Check if game is over
        if game.board.is_empty():
            game.state.is_over = True
            game.state.winner = game.state.current_player
            return

        # Switch player
        game.state.current_player = (
            "Player 2" if game.state.current_player == "Player 1" else "Player 1"
        )

    def to_history_record(
        self, player: "Player", count: int, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "remove_b",
            "player": player_name,
            "count": count,
        }


class RemoveFromBothAction(Action["WythoffGame"]):
    """Action for removing same amount from both piles."""

    name = "remove_both"
    display_name = "Remove from Both Piles"
    OutputSchema = WythoffMoveOutput

    def validate(self, game: "WythoffGame", player: "Player", count: int) -> bool:
        """Validate removal from both piles."""
        if game.state.is_over:
            return False
        if count < 1:
            return False
        if count > game.board.pile_a or count > game.board.pile_b:
            return False
        return True

    def apply(self, game: "WythoffGame", player: "Player", count: int) -> None:
        """Apply removal from both piles."""
        game.board.remove_from_both(count)

        # Log to history
        game.history.add_action(
            self, player, count=count, player_name=game.state.current_player
        )

        # Check if game is over
        if game.board.is_empty():
            game.state.is_over = True
            game.state.winner = game.state.current_player
            return

        # Switch player
        game.state.current_player = (
            "Player 2" if game.state.current_player == "Player 1" else "Player 1"
        )

    def to_history_record(
        self, player: "Player", count: int, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "remove_both",
            "player": player_name,
            "count": count,
        }
