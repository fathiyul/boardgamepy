"""Love Letter card definitions."""

from dataclasses import dataclass
from enum import Enum


class CardType(Enum):
    """Card types in Love Letter."""

    GUARD = ("Guard", 1, 5, "💂")  # (name, card_value, count, emoji)
    PRIEST = ("Priest", 2, 2, "🙏")
    BARON = ("Baron", 3, 2, "⚔️")
    HANDMAID = ("Handmaid", 4, 2, "🛡️")
    PRINCE = ("Prince", 5, 2, "🤴")
    KING = ("King", 6, 1, "👑")
    COUNTESS = ("Countess", 7, 1, "👸")
    PRINCESS = ("Princess", 8, 1, "👰")

    def __init__(self, card_name: str, card_value: int, count: int, emoji: str):
        self.card_name = card_name
        self.card_value = card_value
        self.count = count
        self.emoji = emoji


@dataclass
class Card:
    """A Love Letter card."""

    type: CardType
    id: int  # Unique ID for this specific card instance

    @property
    def name(self) -> str:
        return self.type.card_name

    @property
    def value(self) -> int:
        return self.type.card_value

    @property
    def emoji(self) -> str:
        return self.type.emoji

    def __str__(self) -> str:
        return f"{self.emoji} {self.name} ({self.value})"

    def __repr__(self) -> str:
        return f"Card({self.name}, {self.value})"


def create_deck() -> list[Card]:
    """Create a standard Love Letter deck (16 cards)."""
    deck = []
    card_id = 0

    for card_type in CardType:
        for _ in range(card_type.count):
            deck.append(Card(type=card_type, id=card_id))
            card_id += 1

    return deck


# Card effect descriptions for reference
CARD_EFFECTS = {
    CardType.GUARD: "Guess another player's card (not Guard). If correct, they're eliminated.",
    CardType.PRIEST: "Look at another player's hand.",
    CardType.BARON: "Compare hands with another player. Lower value is eliminated.",
    CardType.HANDMAID: "Protection until your next turn. Cannot be targeted.",
    CardType.PRINCE: "Choose a player (may be yourself) to discard and draw a new card.",
    CardType.KING: "Trade hands with another player.",
    CardType.COUNTESS: "Must discard if you have King or Prince in hand.",
    CardType.PRINCESS: "If you discard this, you're eliminated.",
}
