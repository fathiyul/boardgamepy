"""Splendor game actions."""

from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field

from boardgamepy import Action
from cards import GemType

if TYPE_CHECKING:
    from game import SplendorGame
    from boardgamepy.core.player import Player


class TakeGemsOutput(BaseModel):
    """LLM structured output for taking gems."""

    action_type: Literal["take_gems"] = Field(..., description="Must be 'take_gems'")
    gem1: str = Field(..., description="First gem type (Diamond/Sapphire/Emerald/Ruby/Onyx)")
    gem2: str | None = Field(None, description="Second gem type (different from gem1)")
    gem3: str | None = Field(None, description="Third gem type (different from gem1 and gem2)")
    take_two: bool = Field(
        False, description="True to take 2 of gem1 (requires 4+ available), False to take 3 different"
    )
    reasoning: str | None = Field(None, description="Why you chose these gems")


class PurchaseCardOutput(BaseModel):
    """LLM structured output for purchasing a card."""

    action_type: Literal["purchase"] = Field(..., description="Must be 'purchase'")
    card_id: int = Field(..., description="ID of the card to purchase (from display or reserved)")
    from_reserved: bool = Field(False, description="True if purchasing from your reserved cards")
    reasoning: str | None = Field(None, description="Why you're purchasing this card")


class ReserveCardOutput(BaseModel):
    """LLM structured output for reserving a card."""

    action_type: Literal["reserve"] = Field(..., description="Must be 'reserve'")
    card_id: int = Field(..., description="ID of the card to reserve from display")
    tier: int = Field(..., description="Tier of the card (1, 2, or 3)")
    reasoning: str | None = Field(None, description="Why you're reserving this card")


# Simplified output schema - avoid nullable types to reduce schema branches
class GameActionOutput(BaseModel):
    """Combined output schema for all actions."""

    action_type: Literal["take_gems", "purchase", "reserve"] = Field(
        ..., description="Type of action to take"
    )

    # Take gems fields - use empty string instead of None
    gem1: str = Field("", description="First gem type (Diamond/Sapphire/Emerald/Ruby/Onyx)")
    gem2: str = Field("", description="Second gem type (different from gem1, or empty)")
    gem3: str = Field("", description="Third gem type (different from gem1 and gem2, or empty)")
    take_two: bool = Field(False, description="True to take 2 of gem1, False to take 3 different")

    # Purchase/Reserve fields - use 0 instead of None
    card_id: int = Field(0, description="Card ID for purchase/reserve actions")
    from_reserved: bool = Field(False, description="True if purchasing from reserved cards")
    tier: int = Field(0, description="Card tier for reserve action (1, 2, or 3)")

    reasoning: str = Field("", description="Reasoning for action")


class TakeGemsAction(Action["SplendorGame"]):
    """Action for taking gem tokens."""

    name = "take_gems"
    display_name = "Take Gems"
    OutputSchema = TakeGemsOutput

    def _parse_gem(self, gem_str: str) -> GemType | None:
        """Parse gem type from string."""
        gem_str = gem_str.lower()
        mapping = {
            "diamond": GemType.DIAMOND,
            "sapphire": GemType.SAPPHIRE,
            "emerald": GemType.EMERALD,
            "ruby": GemType.RUBY,
            "onyx": GemType.ONYX,
        }
        return mapping.get(gem_str)

    def validate(
        self,
        game: "SplendorGame",
        player: "Player",
        gem1: str,
        gem2: str = "",
        gem3: str = "",
        take_two: bool = False,
        **kwargs,
    ) -> bool:
        """Validate gem taking action."""
        player_idx = player.player_idx

        # Parse gems
        g1 = self._parse_gem(gem1)
        if not g1 or g1 == GemType.GOLD:
            return False

        if take_two:
            # Taking 2 of same gem
            if gem2 or gem3:
                return False  # Should only specify gem1

            # Must have 4+ available
            if game.board.gem_bank.get(g1, 0) < 4:
                return False

            # Check if player will exceed 10 gems
            if game.board.get_total_gems(player_idx) + 2 > 10:
                return False

        else:
            # Taking 3 different gems
            if not gem2 or not gem3:
                return False

            g2 = self._parse_gem(gem2)
            g3 = self._parse_gem(gem3)

            if not g2 or not g3:
                return False

            # Must be different
            if g1 == g2 or g1 == g3 or g2 == g3:
                return False

            # Must be available
            if game.board.gem_bank.get(g1, 0) < 1:
                return False
            if game.board.gem_bank.get(g2, 0) < 1:
                return False
            if game.board.gem_bank.get(g3, 0) < 1:
                return False

            # Check if player will exceed 10 gems
            if game.board.get_total_gems(player_idx) + 3 > 10:
                return False

        return True

    def apply(
        self,
        game: "SplendorGame",
        player: "Player",
        gem1: str,
        gem2: str = "",
        gem3: str = "",
        take_two: bool = False,
        **kwargs,
    ) -> None:
        """Apply gem taking action."""
        player_idx = player.player_idx

        g1 = self._parse_gem(gem1)

        if take_two:
            gems_to_take = {g1: 2}
        else:
            g2 = self._parse_gem(gem2)
            g3 = self._parse_gem(gem3)
            gems_to_take = {g1: 1, g2: 1, g3: 1}

        game.board.take_gems(player_idx, gems_to_take)

        # Log action
        game.history.add_action(
            self,
            player,
            gems_taken=gems_to_take,
            player_name=player.team,
        )

    def to_history_record(self, player: "Player", gems_taken: dict, player_name: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "take_gems",
            "player": player_name,
            "gems": {gem.value: count for gem, count in gems_taken.items()},
        }


class PurchaseCardAction(Action["SplendorGame"]):
    """Action for purchasing a development card."""

    name = "purchase_card"
    display_name = "Purchase Card"
    OutputSchema = PurchaseCardOutput

    def validate(
        self,
        game: "SplendorGame",
        player: "Player",
        card_id: int,
        from_reserved: bool = False,
        **kwargs,
    ) -> bool:
        """Validate card purchase."""
        player_idx = player.player_idx

        # Get the card
        if from_reserved:
            card = None
            for c in game.board.player_reserved[player_idx]:
                if c.card_id == card_id:
                    card = c
                    break
            if not card:
                return False
        else:
            result = game.board.get_card_from_display(card_id)
            if not result:
                return False
            card, _ = result
            # Put it back (we're just validating)
            tier = card.tier
            if tier == 1:
                game.board.tier1_display.append(card)
            elif tier == 2:
                game.board.tier2_display.append(card)
            else:
                game.board.tier3_display.append(card)

        # Can afford?
        return game.board.can_afford_card(player_idx, card)

    def apply(
        self,
        game: "SplendorGame",
        player: "Player",
        card_id: int,
        from_reserved: bool = False,
        **kwargs,
    ) -> None:
        """Apply card purchase."""
        player_idx = player.player_idx

        # Get the card
        if from_reserved:
            card = game.board.get_reserved_card(player_idx, card_id)
        else:
            result = game.board.get_card_from_display(card_id)
            card, tier = result

        # Purchase
        game.board.purchase_card(player_idx, card)

        # Refill display if not from reserved
        if not from_reserved:
            game.board.refill_display(tier)

        # Log action
        game.history.add_action(
            self,
            player,
            card=str(card),
            card_id=card_id,
            player_name=player.team,
        )

    def to_history_record(self, player: "Player", card: str, player_name: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "purchase_card",
            "player": player_name,
            "card": card,
        }


class ReserveCardAction(Action["SplendorGame"]):
    """Action for reserving a development card."""

    name = "reserve_card"
    display_name = "Reserve Card"
    OutputSchema = ReserveCardOutput

    def validate(
        self,
        game: "SplendorGame",
        player: "Player",
        card_id: int,
        tier: int,
        **kwargs,
    ) -> bool:
        """Validate card reservation."""
        player_idx = player.player_idx

        # Can't reserve more than 3 cards
        if len(game.board.player_reserved[player_idx]) >= 3:
            return False

        # Card must exist in display
        result = game.board.get_card_from_display(card_id)
        if not result:
            return False

        card, card_tier = result

        # Put it back (we're just validating)
        if card_tier == 1:
            game.board.tier1_display.append(card)
        elif card_tier == 2:
            game.board.tier2_display.append(card)
        else:
            game.board.tier3_display.append(card)

        return True

    def apply(
        self,
        game: "SplendorGame",
        player: "Player",
        card_id: int,
        tier: int,
        **kwargs,
    ) -> None:
        """Apply card reservation."""
        player_idx = player.player_idx

        # Get the card
        result = game.board.get_card_from_display(card_id)
        card, card_tier = result

        # Reserve it
        game.board.player_reserved[player_idx].append(card)

        # Give gold token if available
        if game.board.gem_bank[GemType.GOLD] > 0:
            game.board.take_gems(player_idx, {GemType.GOLD: 1})

        # Refill display
        game.board.refill_display(card_tier)

        # Log action
        game.history.add_action(
            self,
            player,
            card=str(card),
            card_id=card_id,
            player_name=player.team,
        )

    def to_history_record(self, player: "Player", card: str, player_name: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "reserve_card",
            "player": player_name,
            "card": card,
        }
