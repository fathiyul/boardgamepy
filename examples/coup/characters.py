"""Coup character definitions."""

from dataclasses import dataclass
from enum import Enum


class CharacterType(Enum):
    """Character types in Coup."""

    DUKE = ("Duke", 3, "👑")  # (name, count, emoji)
    ASSASSIN = ("Assassin", 3, "🗡️")
    CAPTAIN = ("Captain", 3, "⚓")
    AMBASSADOR = ("Ambassador", 3, "📜")
    CONTESSA = ("Contessa", 3, "👸")

    def __init__(self, char_name: str, count: int, emoji: str):
        self.char_name = char_name
        self.count = count
        self.emoji = emoji


@dataclass
class Character:
    """A Coup character card."""

    type: CharacterType
    id: int  # Unique ID for this card instance
    revealed: bool = False  # Whether this card has been revealed (lost influence)

    @property
    def name(self) -> str:
        return self.type.char_name

    @property
    def emoji(self) -> str:
        return self.type.emoji

    def __str__(self) -> str:
        return f"{self.emoji} {self.name}"

    def __repr__(self) -> str:
        return f"Character({self.name}, revealed={self.revealed})"


def create_deck() -> list[Character]:
    """Create a standard Coup deck (15 cards)."""
    deck = []
    card_id = 0

    for char_type in CharacterType:
        for _ in range(char_type.count):
            deck.append(Character(type=char_type, id=card_id))
            card_id += 1

    return deck


# Character abilities for reference
CHARACTER_ABILITIES = {
    CharacterType.DUKE: "Take 3 coins (Tax). Blocks Foreign Aid.",
    CharacterType.ASSASSIN: "Pay 3 coins to assassinate another player's influence.",
    CharacterType.CAPTAIN: "Steal 2 coins from another player. Blocks stealing.",
    CharacterType.AMBASSADOR: "Exchange cards with deck. Blocks stealing.",
    CharacterType.CONTESSA: "Blocks assassination.",
}
