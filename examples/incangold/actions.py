"""Incan Gold game actions."""

from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field

from boardgamepy import Action

if TYPE_CHECKING:
    from game import IncanGoldGame
    from boardgamepy.core.player import Player


class DecisionOutput(BaseModel):
    """LLM structured output for continue/return decision."""

    decision: Literal["continue", "return"] = Field(
        ...,
        description="'continue' to keep exploring (risky!), or 'return' to camp with your gems (safe)",
    )
    reasoning: str | None = Field(None, description="Why you made this decision")


class MakeDecisionAction(Action["IncanGoldGame"]):
    """Action for deciding to continue or return."""

    name = "make_decision"
    display_name = "Continue or Return"
    OutputSchema = DecisionOutput

    def validate(
        self,
        game: "IncanGoldGame",
        player: "Player",
        decision: str,
        **kwargs,
    ) -> bool:
        """Validate decision."""
        player_idx = player.player_idx

        # Must be in decide phase
        if game.state.phase != "decide":
            return False

        # Must be in temple
        if player_idx not in game.board.in_temple:
            return False

        # Valid decision
        if decision not in ["continue", "return"]:
            return False

        # Haven't already decided
        if player_idx in game.state.decisions:
            return False

        return True

    def apply(
        self,
        game: "IncanGoldGame",
        player: "Player",
        decision: str,
        **kwargs,
    ) -> None:
        """Apply decision."""
        player_idx = player.player_idx

        # Record decision
        game.state.decisions[player_idx] = decision

        # Log action
        game.history.add_action(
            self,
            player,
            decision=decision,
            player_name=player.team,
        )

    def to_history_record(
        self, player: "Player", decision: str, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "decision",
            "player": player_name,
            "decision": decision,
        }
