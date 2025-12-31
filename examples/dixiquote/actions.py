"""DixiQuote game actions."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

from boardgamepy import Action

if TYPE_CHECKING:
    from game import DixiQuoteGame
    from boardgamepy.core.player import Player


class ChooseSituationOutput(BaseModel):
    """LLM structured output for choosing a situation card."""

    situation: str = Field(..., description="The situation card text you choose from your hand")
    reasoning: str | None = Field(None, description="Short explanation of why you chose this situation")


class ChooseSituationAction(Action["DixiQuoteGame"]):
    """Action for storyteller choosing a situation card."""

    name = "choose_situation"
    display_name = "Choose Situation"
    OutputSchema = ChooseSituationOutput

    def validate(self, game: "DixiQuoteGame", player: "Player", situation: str) -> bool:
        """Validate situation choice."""
        if game.state.is_over:
            return False

        # Must be storyteller
        if player.player_idx != game.state.storyteller_idx:
            return False

        # Must be in choose_situation phase
        if game.state.phase != "choose_situation":
            return False

        # Situation must be in player's hand
        hand = game.get_player_hand(player.player_idx)
        return situation in hand

    def apply(self, game: "DixiQuoteGame", player: "Player", situation: str) -> None:
        """Apply situation choice."""
        game.state.storyteller_situation = situation
        game.state.phase = "give_quote"
        game.state.consecutive_invalid_actions = 0  # Reset for new phase

        # Log to history
        game.history.add_action(self, player, situation=situation)

    def to_history_record(self, player: "Player", situation: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "choose_situation",
            "player": player.name,
            "player_idx": player.player_idx,
            "situation": situation,
        }


class GiveQuoteOutput(BaseModel):
    """LLM structured output for giving a quote."""

    quote: str = Field(..., description="A poetic, quote-like clue (single line or sentence fragment)")
    reasoning: str | None = Field(None, description="Short explanation of how this quote relates to your situation")


class GiveQuoteAction(Action["DixiQuoteGame"]):
    """Action for storyteller giving a quote."""

    name = "give_quote"
    display_name = "Give Quote"
    OutputSchema = GiveQuoteOutput

    def validate(self, game: "DixiQuoteGame", player: "Player", quote: str) -> bool:
        """Validate quote."""
        if game.state.is_over:
            return False

        # Must be storyteller
        if player.player_idx != game.state.storyteller_idx:
            return False

        # Must be in give_quote phase
        if game.state.phase != "give_quote":
            return False

        # Quote must not be empty
        return len(quote.strip()) > 0

    def apply(self, game: "DixiQuoteGame", player: "Player", quote: str) -> None:
        """Apply quote."""
        game.state.storyteller_quote = quote.strip()
        game.state.phase = "submit_situations"
        game.state.consecutive_invalid_actions = 0  # Reset for new phase

        # Log to history
        game.history.add_action(self, player, quote=quote)

    def to_history_record(self, player: "Player", quote: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "give_quote",
            "player": player.name,
            "player_idx": player.player_idx,
            "quote": quote,
        }


class SubmitSituationOutput(BaseModel):
    """LLM structured output for submitting a situation card."""

    situation: str = Field(..., description="The situation card from your hand that best fits the quote")
    reasoning: str | None = Field(None, description="Short explanation of why this situation fits the quote")


class SubmitSituationAction(Action["DixiQuoteGame"]):
    """Action for non-storyteller players submitting a situation card."""

    name = "submit_situation"
    display_name = "Submit Situation"
    OutputSchema = SubmitSituationOutput

    def validate(self, game: "DixiQuoteGame", player: "Player", situation: str) -> bool:
        """Validate situation submission."""
        if game.state.is_over:
            return False

        # Must NOT be storyteller
        if player.player_idx == game.state.storyteller_idx:
            return False

        # Must be in submit_situations phase
        if game.state.phase != "submit_situations":
            return False

        # Must not have already submitted
        if player.player_idx in game.state.submitted_situations:
            return False

        # Situation must be in player's hand
        hand = game.get_player_hand(player.player_idx)
        return situation in hand

    def apply(self, game: "DixiQuoteGame", player: "Player", situation: str) -> None:
        """Apply situation submission."""
        game.state.submitted_situations[player.player_idx] = situation

        # Check if all non-storyteller, non-skipped players have submitted
        num_expected = len(game.players) - 1  # All except storyteller
        num_skipped = len(game.state.skipped_players)
        if len(game.state.submitted_situations) >= num_expected - num_skipped:
            game.state.phase = "vote"
            game.state.consecutive_invalid_actions = 0  # Reset for new phase

        # Log to history
        game.history.add_action(self, player, situation=situation)

    def to_history_record(self, player: "Player", situation: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "submit_situation",
            "player": player.name,
            "player_idx": player.player_idx,
            "situation": situation,
        }


class VoteOutput(BaseModel):
    """LLM structured output for voting."""

    situation: str = Field(..., description="The situation you believe best matches the storyteller's quote")
    reasoning: str | None = Field(None, description="Short explanation of why you chose this situation")


class VoteAction(Action["DixiQuoteGame"]):
    """Action for voting on situations."""

    name = "vote"
    display_name = "Vote"
    OutputSchema = VoteOutput

    def validate(self, game: "DixiQuoteGame", player: "Player", situation: str) -> bool:
        """Validate vote."""
        if game.state.is_over:
            return False

        # Must NOT be storyteller
        if player.player_idx == game.state.storyteller_idx:
            return False

        # Must be in vote phase
        if game.state.phase != "vote":
            return False

        # Must not have already voted
        if player.player_idx in game.state.votes:
            return False

        # Situation must be in the submitted pool
        all_situations = game.state.get_all_submitted_situations()
        if situation not in all_situations:
            return False

        # Cannot vote for own submission
        if player.player_idx in game.state.submitted_situations:
            if game.state.submitted_situations[player.player_idx] == situation:
                return False

        return True

    def apply(self, game: "DixiQuoteGame", player: "Player", situation: str) -> None:
        """Apply vote."""
        game.state.votes[player.player_idx] = situation

        # Check if all non-storyteller, non-skipped players have voted
        num_expected = len(game.players) - 1  # All except storyteller
        num_skipped = len(game.state.skipped_players)
        if len(game.state.votes) >= num_expected - num_skipped:
            game.state.phase = "scoring"
            game.state.consecutive_invalid_actions = 0  # Reset for new phase

        # Log to history
        game.history.add_action(self, player, situation=situation)

    def to_history_record(self, player: "Player", situation: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "vote",
            "player": player.name,
            "player_idx": player.player_idx,
            "situation": situation,
        }
