"""Splendor cards and game pieces."""

from dataclasses import dataclass
from enum import Enum
import random


class GemType(Enum):
    """Types of gems in Splendor."""

    DIAMOND = "Diamond"  # White
    SAPPHIRE = "Sapphire"  # Blue
    EMERALD = "Emerald"  # Green
    RUBY = "Ruby"  # Red
    ONYX = "Onyx"  # Black
    GOLD = "Gold"  # Wild (from reserving)


@dataclass
class DevelopmentCard:
    """A development card that can be purchased."""

    tier: int  # 1, 2, or 3
    points: int  # Prestige points
    bonus: GemType  # Permanent gem bonus
    cost: dict[GemType, int]  # Gems required to purchase
    card_id: int = 0  # Unique identifier

    def __str__(self) -> str:
        cost_str = ", ".join(f"{count}{gem.value[0]}" for gem, count in self.cost.items())
        bonus_icon = _get_gem_icon(self.bonus)
        return f"T{self.tier} [{bonus_icon}] {self.points}pts ({cost_str})"


@dataclass
class Noble:
    """A noble tile that visits players."""

    points: int = 3  # Always worth 3 points
    requirements: dict[GemType, int] = None  # Card bonuses required
    noble_id: int = 0

    def __str__(self) -> str:
        req_str = ", ".join(f"{count}{gem.value[0]}" for gem, count in self.requirements.items())
        return f"Noble (3pts: {req_str})"


def _get_gem_icon(gem: GemType) -> str:
    """Get emoji/icon for gem type."""
    icons = {
        GemType.DIAMOND: "💎",
        GemType.SAPPHIRE: "🔷",
        GemType.EMERALD: "🟢",
        GemType.RUBY: "🔴",
        GemType.ONYX: "⚫",
        GemType.GOLD: "🟡",
    }
    return icons.get(gem, "?")


def create_tier1_cards() -> list[DevelopmentCard]:
    """Create tier 1 development cards."""
    cards = []
    card_id = 0

    # 0-point cards with various costs
    configs = [
        # Diamond bonus
        (0, GemType.DIAMOND, {GemType.ONYX: 3}),
        (0, GemType.DIAMOND, {GemType.ONYX: 2, GemType.SAPPHIRE: 1}),
        (0, GemType.DIAMOND, {GemType.RUBY: 1, GemType.SAPPHIRE: 1, GemType.EMERALD: 1, GemType.ONYX: 1}),
        (0, GemType.DIAMOND, {GemType.RUBY: 2, GemType.EMERALD: 1}),
        (0, GemType.DIAMOND, {GemType.SAPPHIRE: 3}),
        (0, GemType.DIAMOND, {GemType.SAPPHIRE: 2, GemType.EMERALD: 2}),
        (0, GemType.DIAMOND, {GemType.EMERALD: 2, GemType.ONYX: 2}),
        (1, GemType.DIAMOND, {GemType.RUBY: 4}),
        # Sapphire bonus
        (0, GemType.SAPPHIRE, {GemType.EMERALD: 3}),
        (0, GemType.SAPPHIRE, {GemType.EMERALD: 2, GemType.ONYX: 1}),
        (0, GemType.SAPPHIRE, {GemType.DIAMOND: 1, GemType.EMERALD: 1, GemType.RUBY: 1, GemType.ONYX: 1}),
        (0, GemType.SAPPHIRE, {GemType.DIAMOND: 2, GemType.RUBY: 1}),
        (0, GemType.SAPPHIRE, {GemType.DIAMOND: 3}),
        (0, GemType.SAPPHIRE, {GemType.DIAMOND: 2, GemType.EMERALD: 2}),
        (0, GemType.SAPPHIRE, {GemType.RUBY: 2, GemType.ONYX: 2}),
        (1, GemType.SAPPHIRE, {GemType.EMERALD: 4}),
        # Emerald bonus
        (0, GemType.EMERALD, {GemType.RUBY: 3}),
        (0, GemType.EMERALD, {GemType.RUBY: 2, GemType.DIAMOND: 1}),
        (0, GemType.EMERALD, {GemType.SAPPHIRE: 1, GemType.RUBY: 1, GemType.DIAMOND: 1, GemType.ONYX: 1}),
        (0, GemType.EMERALD, {GemType.SAPPHIRE: 2, GemType.ONYX: 1}),
        (0, GemType.EMERALD, {GemType.RUBY: 3}),
        (0, GemType.EMERALD, {GemType.SAPPHIRE: 2, GemType.ONYX: 2}),
        (0, GemType.EMERALD, {GemType.DIAMOND: 2, GemType.RUBY: 2}),
        (1, GemType.EMERALD, {GemType.SAPPHIRE: 4}),
        # Ruby bonus
        (0, GemType.RUBY, {GemType.SAPPHIRE: 3}),
        (0, GemType.RUBY, {GemType.SAPPHIRE: 2, GemType.EMERALD: 1}),
        (0, GemType.RUBY, {GemType.DIAMOND: 1, GemType.SAPPHIRE: 1, GemType.EMERALD: 1, GemType.ONYX: 1}),
        (0, GemType.RUBY, {GemType.DIAMOND: 2, GemType.ONYX: 1}),
        (0, GemType.RUBY, {GemType.EMERALD: 3}),
        (0, GemType.RUBY, {GemType.DIAMOND: 2, GemType.SAPPHIRE: 2}),
        (0, GemType.RUBY, {GemType.EMERALD: 2, GemType.ONYX: 2}),
        (1, GemType.RUBY, {GemType.ONYX: 4}),
        # Onyx bonus
        (0, GemType.ONYX, {GemType.DIAMOND: 3}),
        (0, GemType.ONYX, {GemType.DIAMOND: 2, GemType.RUBY: 1}),
        (0, GemType.ONYX, {GemType.DIAMOND: 1, GemType.SAPPHIRE: 1, GemType.EMERALD: 1, GemType.RUBY: 1}),
        (0, GemType.ONYX, {GemType.SAPPHIRE: 2, GemType.EMERALD: 1}),
        (0, GemType.ONYX, {GemType.ONYX: 3}),
        (0, GemType.ONYX, {GemType.DIAMOND: 2, GemType.RUBY: 2}),
        (0, GemType.ONYX, {GemType.SAPPHIRE: 2, GemType.EMERALD: 2}),
        (1, GemType.ONYX, {GemType.DIAMOND: 4}),
    ]

    for points, bonus, cost in configs:
        cards.append(DevelopmentCard(tier=1, points=points, bonus=bonus, cost=cost, card_id=card_id))
        card_id += 1

    return cards


def create_tier2_cards() -> list[DevelopmentCard]:
    """Create tier 2 development cards."""
    cards = []
    card_id = 100

    configs = [
        # Diamond bonus
        (1, GemType.DIAMOND, {GemType.EMERALD: 3, GemType.RUBY: 2, GemType.ONYX: 2}),
        (1, GemType.DIAMOND, {GemType.EMERALD: 3, GemType.RUBY: 3}),
        (2, GemType.DIAMOND, {GemType.RUBY: 5}),
        (2, GemType.DIAMOND, {GemType.SAPPHIRE: 5}),
        (2, GemType.DIAMOND, {GemType.SAPPHIRE: 2, GemType.EMERALD: 1, GemType.RUBY: 1, GemType.ONYX: 1}),
        (3, GemType.DIAMOND, {GemType.DIAMOND: 6}),
        # Sapphire bonus
        (1, GemType.SAPPHIRE, {GemType.DIAMOND: 2, GemType.RUBY: 2, GemType.ONYX: 3}),
        (1, GemType.SAPPHIRE, {GemType.DIAMOND: 3, GemType.ONYX: 3}),
        (2, GemType.SAPPHIRE, {GemType.EMERALD: 5}),
        (2, GemType.SAPPHIRE, {GemType.ONYX: 5}),
        (2, GemType.SAPPHIRE, {GemType.DIAMOND: 2, GemType.EMERALD: 1, GemType.RUBY: 1, GemType.ONYX: 1}),
        (3, GemType.SAPPHIRE, {GemType.SAPPHIRE: 6}),
        # Emerald bonus
        (1, GemType.EMERALD, {GemType.DIAMOND: 3, GemType.SAPPHIRE: 2, GemType.ONYX: 2}),
        (1, GemType.EMERALD, {GemType.DIAMOND: 3, GemType.SAPPHIRE: 3}),
        (2, GemType.EMERALD, {GemType.DIAMOND: 5}),
        (2, GemType.EMERALD, {GemType.RUBY: 5}),
        (2, GemType.EMERALD, {GemType.DIAMOND: 1, GemType.SAPPHIRE: 2, GemType.RUBY: 1, GemType.ONYX: 1}),
        (3, GemType.EMERALD, {GemType.EMERALD: 6}),
        # Ruby bonus
        (1, GemType.RUBY, {GemType.DIAMOND: 2, GemType.SAPPHIRE: 3, GemType.EMERALD: 2}),
        (1, GemType.RUBY, {GemType.SAPPHIRE: 3, GemType.EMERALD: 3}),
        (2, GemType.RUBY, {GemType.SAPPHIRE: 5}),
        (2, GemType.RUBY, {GemType.DIAMOND: 5}),
        (2, GemType.RUBY, {GemType.DIAMOND: 1, GemType.SAPPHIRE: 1, GemType.EMERALD: 2, GemType.ONYX: 1}),
        (3, GemType.RUBY, {GemType.RUBY: 6}),
        # Onyx bonus
        (1, GemType.ONYX, {GemType.DIAMOND: 2, GemType.SAPPHIRE: 2, GemType.EMERALD: 3}),
        (1, GemType.ONYX, {GemType.DIAMOND: 3, GemType.RUBY: 3}),
        (2, GemType.ONYX, {GemType.EMERALD: 5}),
        (2, GemType.ONYX, {GemType.SAPPHIRE: 5}),
        (2, GemType.ONYX, {GemType.DIAMOND: 1, GemType.SAPPHIRE: 1, GemType.EMERALD: 1, GemType.RUBY: 2}),
        (3, GemType.ONYX, {GemType.ONYX: 6}),
    ]

    for points, bonus, cost in configs:
        cards.append(DevelopmentCard(tier=2, points=points, bonus=bonus, cost=cost, card_id=card_id))
        card_id += 1

    return cards


def create_tier3_cards() -> list[DevelopmentCard]:
    """Create tier 3 development cards."""
    cards = []
    card_id = 200

    configs = [
        # Diamond bonus
        (3, GemType.DIAMOND, {GemType.DIAMOND: 3, GemType.SAPPHIRE: 3, GemType.EMERALD: 5, GemType.RUBY: 3}),
        (4, GemType.DIAMOND, {GemType.ONYX: 7}),
        (4, GemType.DIAMOND, {GemType.SAPPHIRE: 3, GemType.EMERALD: 6, GemType.RUBY: 3}),
        (5, GemType.DIAMOND, {GemType.SAPPHIRE: 7, GemType.ONYX: 3}),
        # Sapphire bonus
        (3, GemType.SAPPHIRE, {GemType.SAPPHIRE: 3, GemType.EMERALD: 3, GemType.RUBY: 5, GemType.ONYX: 3}),
        (4, GemType.SAPPHIRE, {GemType.RUBY: 7}),
        (4, GemType.SAPPHIRE, {GemType.EMERALD: 3, GemType.RUBY: 6, GemType.ONYX: 3}),
        (5, GemType.SAPPHIRE, {GemType.EMERALD: 7, GemType.DIAMOND: 3}),
        # Emerald bonus
        (3, GemType.EMERALD, {GemType.DIAMOND: 5, GemType.SAPPHIRE: 3, GemType.RUBY: 3, GemType.ONYX: 3}),
        (4, GemType.EMERALD, {GemType.SAPPHIRE: 7}),
        (4, GemType.EMERALD, {GemType.DIAMOND: 3, GemType.SAPPHIRE: 6, GemType.ONYX: 3}),
        (5, GemType.EMERALD, {GemType.DIAMOND: 7, GemType.RUBY: 3}),
        # Ruby bonus
        (3, GemType.RUBY, {GemType.DIAMOND: 3, GemType.EMERALD: 3, GemType.RUBY: 3, GemType.ONYX: 5}),
        (4, GemType.RUBY, {GemType.DIAMOND: 7}),
        (4, GemType.RUBY, {GemType.DIAMOND: 6, GemType.EMERALD: 3, GemType.ONYX: 3}),
        (5, GemType.RUBY, {GemType.SAPPHIRE: 7, GemType.ONYX: 3}),
        # Onyx bonus
        (3, GemType.ONYX, {GemType.DIAMOND: 3, GemType.SAPPHIRE: 5, GemType.EMERALD: 3, GemType.RUBY: 3}),
        (4, GemType.ONYX, {GemType.EMERALD: 7}),
        (4, GemType.ONYX, {GemType.DIAMOND: 3, GemType.RUBY: 3, GemType.ONYX: 6}),
        (5, GemType.ONYX, {GemType.RUBY: 7, GemType.SAPPHIRE: 3}),
    ]

    for points, bonus, cost in configs:
        cards.append(DevelopmentCard(tier=3, points=points, bonus=bonus, cost=cost, card_id=card_id))
        card_id += 1

    return cards


def create_nobles() -> list[Noble]:
    """Create noble tiles."""
    nobles = []

    configs = [
        {GemType.DIAMOND: 4, GemType.SAPPHIRE: 4},
        {GemType.DIAMOND: 3, GemType.SAPPHIRE: 3, GemType.EMERALD: 3},
        {GemType.SAPPHIRE: 4, GemType.EMERALD: 4},
        {GemType.SAPPHIRE: 3, GemType.EMERALD: 3, GemType.RUBY: 3},
        {GemType.EMERALD: 4, GemType.RUBY: 4},
        {GemType.EMERALD: 3, GemType.RUBY: 3, GemType.ONYX: 3},
        {GemType.RUBY: 4, GemType.ONYX: 4},
        {GemType.RUBY: 3, GemType.ONYX: 3, GemType.DIAMOND: 3},
        {GemType.ONYX: 4, GemType.DIAMOND: 4},
        {GemType.ONYX: 3, GemType.DIAMOND: 3, GemType.SAPPHIRE: 3},
    ]

    for i, requirements in enumerate(configs):
        nobles.append(Noble(points=3, requirements=requirements, noble_id=i))

    return nobles


def shuffle_cards(cards: list[DevelopmentCard]) -> list[DevelopmentCard]:
    """Shuffle development cards."""
    shuffled = cards.copy()
    random.shuffle(shuffled)
    return shuffled
