"""Sushi Go! card definitions."""

from dataclasses import dataclass
from enum import Enum


class CardType(Enum):
    """Card types in Sushi Go!"""

    # Maki rolls (most/second most scoring)
    MAKI_1 = ("Maki Roll", 1, 6)  # (name, maki_count, deck_count)
    MAKI_2 = ("Maki Roll", 2, 12)
    MAKI_3 = ("Maki Roll", 3, 8)

    # Set collection
    TEMPURA = ("Tempura", 0, 14)  # 2 = 5 points
    SASHIMI = ("Sashimi", 0, 14)  # 3 = 10 points
    DUMPLING = ("Dumpling", 0, 14)  # 1,3,6,10,15 points

    # Nigiri (immediate points, can be tripled with wasabi)
    EGG_NIGIRI = ("Egg Nigiri", 0, 5, 1)  # (name, maki, deck_count, points)
    SALMON_NIGIRI = ("Salmon Nigiri", 0, 10, 2)
    SQUID_NIGIRI = ("Squid Nigiri", 0, 5, 3)

    # Special
    WASABI = ("Wasabi", 0, 6)  # Triples next nigiri
    CHOPSTICKS = ("Chopsticks", 0, 4)  # Take 2 cards next turn

    # Dessert (scored at end of game)
    PUDDING = ("Pudding", 0, 10)  # Most +6, least -6

    def __init__(self, card_name: str, maki_value: int, count: int, points: int = 0):
        self.card_name = card_name
        self.maki_value = maki_value
        self.count = count
        self.points = points  # For nigiri


@dataclass
class Card:
    """A Sushi Go! card."""

    type: CardType
    id: int  # Unique ID for this card instance

    @property
    def name(self) -> str:
        """Get card display name."""
        if self.type in [CardType.MAKI_1, CardType.MAKI_2, CardType.MAKI_3]:
            return f"{self.type.card_name} ({self.type.maki_value})"
        return self.type.card_name

    @property
    def is_nigiri(self) -> bool:
        """Check if this is a nigiri card."""
        return self.type in [CardType.EGG_NIGIRI, CardType.SALMON_NIGIRI, CardType.SQUID_NIGIRI]

    @property
    def is_maki(self) -> bool:
        """Check if this is a maki roll."""
        return self.type in [CardType.MAKI_1, CardType.MAKI_2, CardType.MAKI_3]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Card({self.name})"


def create_deck() -> list[Card]:
    """Create a standard Sushi Go! deck (108 cards)."""
    deck = []
    card_id = 0

    for card_type in CardType:
        for _ in range(card_type.count):
            deck.append(Card(type=card_type, id=card_id))
            card_id += 1

    return deck


# Card descriptions for reference
CARD_DESCRIPTIONS = {
    CardType.MAKI_1: "1 maki icon. Most maki = 6pts, 2nd = 3pts",
    CardType.MAKI_2: "2 maki icons. Most maki = 6pts, 2nd = 3pts",
    CardType.MAKI_3: "3 maki icons. Most maki = 6pts, 2nd = 3pts",
    CardType.TEMPURA: "2 Tempura = 5 points",
    CardType.SASHIMI: "3 Sashimi = 10 points",
    CardType.DUMPLING: "1/2/3/4/5+ = 1/3/6/10/15 points",
    CardType.EGG_NIGIRI: "Worth 1 point (3 if on Wasabi)",
    CardType.SALMON_NIGIRI: "Worth 2 points (6 if on Wasabi)",
    CardType.SQUID_NIGIRI: "Worth 3 points (9 if on Wasabi)",
    CardType.WASABI: "Triple the value of next nigiri played",
    CardType.CHOPSTICKS: "Exchange to take 2 cards in a future turn",
    CardType.PUDDING: "Most puddings at game end = +6, least = -6",
}
