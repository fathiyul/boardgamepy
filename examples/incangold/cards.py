"""Incan Gold path cards."""

from dataclasses import dataclass
from enum import Enum
import random


class HazardType(Enum):
    """Types of hazards in the temple."""

    SNAKE = "Snake"
    SPIDER = "Spider"
    FIRE = "Fire"
    ROCKSLIDE = "Rockslide"
    MUMMY = "Mummy"


class CardType(Enum):
    """Types of path cards."""

    TREASURE = "Treasure"
    ARTIFACT = "Artifact"
    HAZARD = "Hazard"


@dataclass
class PathCard:
    """A path card in the temple."""

    card_type: CardType
    value: int = 0  # Gems for treasure, artifact value, or 0 for hazard
    hazard: HazardType | None = None  # Type of hazard if this is a hazard card
    artifact_id: int = 0  # Unique ID for artifacts

    @property
    def is_treasure(self) -> bool:
        return self.card_type == CardType.TREASURE

    @property
    def is_artifact(self) -> bool:
        return self.card_type == CardType.ARTIFACT

    @property
    def is_hazard(self) -> bool:
        return self.card_type == CardType.HAZARD

    def __str__(self) -> str:
        if self.is_treasure:
            return f"💎 {self.value} gems"
        elif self.is_artifact:
            return f"🏺 Artifact ({self.value} pts)"
        elif self.is_hazard:
            return f"⚠️ {self.hazard.value}"
        return "Unknown"

    def __repr__(self) -> str:
        return f"PathCard({self})"


def create_deck() -> list[PathCard]:
    """
    Create a standard Incan Gold deck.

    Deck composition:
    - Treasure cards: 15 cards with values 1-17 gems
    - Artifacts: 5 unique artifacts (5, 5, 10, 10, 15 points)
    - Hazards: 15 hazard cards (3 of each type)
    """
    deck = []

    # Treasure cards (varying values)
    treasure_values = [1, 2, 3, 4, 5, 5, 7, 7, 9, 11, 11, 13, 14, 15, 17]
    for value in treasure_values:
        deck.append(PathCard(card_type=CardType.TREASURE, value=value))

    # Artifact cards (5 unique artifacts)
    artifact_values = [5, 5, 10, 10, 15]
    for i, value in enumerate(artifact_values):
        deck.append(PathCard(card_type=CardType.ARTIFACT, value=value, artifact_id=i + 1))

    # Hazard cards (3 of each hazard type)
    for hazard_type in HazardType:
        for _ in range(3):
            deck.append(PathCard(card_type=CardType.HAZARD, hazard=hazard_type))

    return deck


def shuffle_deck(deck: list[PathCard]) -> list[PathCard]:
    """Shuffle the deck."""
    shuffled = deck.copy()
    random.shuffle(shuffled)
    return shuffled
