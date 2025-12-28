"""Splendor board implementation."""

from typing import TYPE_CHECKING
from boardgamepy import Board
from cards import (
    GemType,
    DevelopmentCard,
    Noble,
    create_tier1_cards,
    create_tier2_cards,
    create_tier3_cards,
    create_nobles,
    shuffle_cards,
)

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class SplendorBoard(Board):
    """
    Splendor game board managing gems, cards, and nobles.

    Tracks:
    - Gem bank (available tokens)
    - Card displays (tier 1, 2, 3)
    - Card decks (face-down)
    - Noble tiles
    - Player collections (gems, cards, reserved cards)
    """

    def __init__(self, num_players: int):
        """
        Initialize board for Splendor.

        Args:
            num_players: Number of players (2-4)
        """
        if num_players < 2 or num_players > 4:
            raise ValueError("Splendor requires 2-4 players")

        self.num_players = num_players

        # Gem bank (available tokens)
        self.gem_bank: dict[GemType, int] = {}
        self._initialize_gem_bank()

        # Card decks and displays
        self.tier1_deck: list[DevelopmentCard] = []
        self.tier2_deck: list[DevelopmentCard] = []
        self.tier3_deck: list[DevelopmentCard] = []

        self.tier1_display: list[DevelopmentCard] = []  # 4 visible cards
        self.tier2_display: list[DevelopmentCard] = []
        self.tier3_display: list[DevelopmentCard] = []

        # Nobles
        self.nobles: list[Noble] = []

        # Player collections
        self.player_gems: dict[int, dict[GemType, int]] = {}
        self.player_cards: dict[int, list[DevelopmentCard]] = {}
        self.player_reserved: dict[int, list[DevelopmentCard]] = {}

        for i in range(num_players):
            self.player_gems[i] = {gem: 0 for gem in GemType}
            self.player_cards[i] = []
            self.player_reserved[i] = []

    def _initialize_gem_bank(self) -> None:
        """Initialize gem bank based on number of players."""
        # Regular gems
        if self.num_players == 2:
            tokens_per_gem = 4
        elif self.num_players == 3:
            tokens_per_gem = 5
        else:  # 4 players
            tokens_per_gem = 7

        for gem in [GemType.DIAMOND, GemType.SAPPHIRE, GemType.EMERALD, GemType.RUBY, GemType.ONYX]:
            self.gem_bank[gem] = tokens_per_gem

        # Gold tokens (always 5)
        self.gem_bank[GemType.GOLD] = 5

    def setup_game(self) -> None:
        """Setup the game board."""
        # Create and shuffle card decks
        self.tier1_deck = shuffle_cards(create_tier1_cards())
        self.tier2_deck = shuffle_cards(create_tier2_cards())
        self.tier3_deck = shuffle_cards(create_tier3_cards())

        # Fill displays (4 cards each)
        self.tier1_display = [self.tier1_deck.pop() for _ in range(4)]
        self.tier2_display = [self.tier2_deck.pop() for _ in range(4)]
        self.tier3_display = [self.tier3_deck.pop() for _ in range(4)]

        # Setup nobles (num_players + 1)
        all_nobles = create_nobles()
        import random

        random.shuffle(all_nobles)
        self.nobles = all_nobles[: self.num_players + 1]

    def refill_display(self, tier: int) -> None:
        """Refill a card display after purchase."""
        if tier == 1 and self.tier1_deck:
            self.tier1_display.append(self.tier1_deck.pop())
        elif tier == 2 and self.tier2_deck:
            self.tier2_display.append(self.tier2_deck.pop())
        elif tier == 3 and self.tier3_deck:
            self.tier3_display.append(self.tier3_deck.pop())

    def get_card_from_display(self, card_id: int) -> tuple[DevelopmentCard, int] | None:
        """Get card from display by ID. Returns (card, tier) or None."""
        for card in self.tier1_display:
            if card.card_id == card_id:
                self.tier1_display.remove(card)
                return card, 1

        for card in self.tier2_display:
            if card.card_id == card_id:
                self.tier2_display.remove(card)
                return card, 2

        for card in self.tier3_display:
            if card.card_id == card_id:
                self.tier3_display.remove(card)
                return card, 3

        return None

    def get_reserved_card(self, player_idx: int, card_id: int) -> DevelopmentCard | None:
        """Get a reserved card for purchase."""
        for card in self.player_reserved[player_idx]:
            if card.card_id == card_id:
                self.player_reserved[player_idx].remove(card)
                return card
        return None

    def can_afford_card(self, player_idx: int, card: DevelopmentCard) -> bool:
        """Check if player can afford a card (including bonuses and gold)."""
        player_gems = self.player_gems[player_idx].copy()
        bonuses = self.get_player_bonuses(player_idx)

        gold_needed = 0

        for gem, cost in card.cost.items():
            # Apply bonuses
            available = player_gems[gem] + bonuses.get(gem, 0)
            if available < cost:
                gold_needed += cost - available

        # Can use gold as wild
        return player_gems[GemType.GOLD] >= gold_needed

    def purchase_card(self, player_idx: int, card: DevelopmentCard) -> None:
        """
        Purchase a card, deducting gems (with bonuses and gold).

        Assumes can_afford_card has already been checked.
        """
        player_gems = self.player_gems[player_idx]
        bonuses = self.get_player_bonuses(player_idx)

        # Calculate what needs to be paid
        to_pay = {}
        gold_to_use = 0

        for gem, cost in card.cost.items():
            bonus = bonuses.get(gem, 0)
            after_bonus = max(0, cost - bonus)
            gems_available = player_gems[gem]

            if gems_available >= after_bonus:
                to_pay[gem] = after_bonus
            else:
                to_pay[gem] = gems_available
                gold_to_use += after_bonus - gems_available

        # Deduct gems
        for gem, amount in to_pay.items():
            player_gems[gem] -= amount
            self.gem_bank[gem] += amount

        # Deduct gold
        if gold_to_use > 0:
            player_gems[GemType.GOLD] -= gold_to_use
            self.gem_bank[GemType.GOLD] += gold_to_use

        # Add card to player collection
        self.player_cards[player_idx].append(card)

    def get_player_bonuses(self, player_idx: int) -> dict[GemType, int]:
        """Get player's gem bonuses from cards."""
        bonuses = {gem: 0 for gem in GemType}

        for card in self.player_cards[player_idx]:
            bonuses[card.bonus] += 1

        return bonuses

    def get_player_points(self, player_idx: int) -> int:
        """Get player's prestige points."""
        points = 0

        # Points from cards
        for card in self.player_cards[player_idx]:
            points += card.points

        # Points from nobles (already claimed)
        # Nobles are not in a separate list, they're just checked and points awarded
        # For simplicity, we'll track nobles separately
        return points

    def check_nobles(self, player_idx: int) -> list[Noble]:
        """Check which nobles the player qualifies for."""
        bonuses = self.get_player_bonuses(player_idx)
        qualifying_nobles = []

        for noble in self.nobles:
            qualifies = True
            for gem, required in noble.requirements.items():
                if bonuses.get(gem, 0) < required:
                    qualifies = False
                    break

            if qualifies:
                qualifying_nobles.append(noble)

        return qualifying_nobles

    def claim_noble(self, player_idx: int, noble: Noble) -> None:
        """Claim a noble for a player."""
        if noble in self.nobles:
            self.nobles.remove(noble)
            # Add noble to player's collection (we'll track this separately in game state)

    def get_total_gems(self, player_idx: int) -> int:
        """Get total number of gems a player has."""
        return sum(self.player_gems[player_idx].values())

    def return_gems(self, player_idx: int, gems_to_return: dict[GemType, int]) -> None:
        """Return gems from player to bank."""
        for gem, count in gems_to_return.items():
            self.player_gems[player_idx][gem] -= count
            self.gem_bank[gem] += count

    def take_gems(self, player_idx: int, gems_to_take: dict[GemType, int]) -> None:
        """Take gems from bank to player."""
        for gem, count in gems_to_take.items():
            self.player_gems[player_idx][gem] += count
            self.gem_bank[gem] -= count

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view for a player.

        All information is public in Splendor.
        """
        from boardgamepy.core.player import Player

        player: Player = context.player
        player_idx = player.player_idx

        lines = ["=== SPLENDOR ===", ""]

        # Gem bank
        lines.append("Gem Bank:")
        for gem in [GemType.DIAMOND, GemType.SAPPHIRE, GemType.EMERALD, GemType.RUBY, GemType.ONYX, GemType.GOLD]:
            count = self.gem_bank[gem]
            lines.append(f"  {gem.value}: {count}")
        lines.append("")

        # Card displays
        lines.append("Available Cards:")
        lines.append("  Tier 3:")
        for card in self.tier3_display:
            lines.append(f"    {card}")
        lines.append("  Tier 2:")
        for card in self.tier2_display:
            lines.append(f"    {card}")
        lines.append("  Tier 1:")
        for card in self.tier1_display:
            lines.append(f"    {card}")
        lines.append("")

        # Nobles
        lines.append("Nobles:")
        for noble in self.nobles:
            lines.append(f"  {noble}")
        lines.append("")

        # Your collection
        your_gems = self.player_gems[player_idx]
        your_cards = self.player_cards[player_idx]
        your_bonuses = self.get_player_bonuses(player_idx)
        your_points = self.get_player_points(player_idx)

        lines.append("Your Collection:")
        lines.append(f"  Points: {your_points}")
        lines.append(f"  Gems: {dict(your_gems)}")
        lines.append(f"  Bonuses: {dict(your_bonuses)}")
        lines.append(f"  Cards: {len(your_cards)}")

        if self.player_reserved[player_idx]:
            lines.append("  Reserved:")
            for card in self.player_reserved[player_idx]:
                lines.append(f"    {card}")

        return "\n".join(lines)
