"""Codenames board implementation."""

from dataclasses import dataclass, field
from typing import Literal
import random

from boardgamepy import Board
from boardgamepy.protocols import ViewContext

CardType = Literal["Red", "Blue", "Civilian", "Assassin"]
CardState = Literal["Hidden", "Revealed"]


@dataclass
class CodenamesCard:
    """A card on the Codenames board."""

    id: int
    code: str
    type: CardType
    state: CardState = "Hidden"


class CodenamesBoard(Board):
    """
    Codenames 5x5 board with role-based views.

    - Spymasters see card types
    - Operatives only see codenames
    """

    cards: dict[int, CodenamesCard] = field(default_factory=dict)

    def __init__(self, cards: dict[int, CodenamesCard] | None = None):
        """Initialize board with cards."""
        self.cards = cards or {}

    @classmethod
    def create_random(cls, codenames: list[str]) -> "CodenamesBoard":
        """
        Create a random Codenames board.

        Args:
            codenames: Pool of codenames to choose from

        Returns:
            New board with random card assignment

        Raises:
            ValueError: If fewer than 25 codenames provided
        """
        if len(codenames) < 25:
            raise ValueError("Need at least 25 unique codenames!")

        # Select and shuffle codenames
        selected_codes = random.sample(codenames, 25)

        # Create card type pool (Red starts first: 9R/8B/7C/1A)
        card_types: list[CardType] = (
            ["Red"] * 9 + ["Blue"] * 8 + ["Civilian"] * 7 + ["Assassin"] * 1  # type: ignore
        )

        # Shuffle card types
        random.shuffle(card_types)

        # Create cards
        cards_dict = {
            i + 1: CodenamesCard(id=i + 1, code=selected_codes[i], type=card_types[i])
            for i in range(25)
        }

        return cls(cards=cards_dict)

    def get_view(self, context: ViewContext) -> str:
        """
        Get role-based view of the board.

        Spymasters see card types, Operatives only see codenames.
        """
        if context.player.role == "Spymaster":
            return self._spymaster_view()
        return self._operatives_view()

    def get_prompt_view(self, context: ViewContext) -> str:
        """
        Get board view optimized for LLM prompts.

        Uses same logic as get_view() - role-based filtering.
        """
        return self.get_view(context)

    def _operatives_view(self) -> str:
        """View for operatives - shows only remaining cards without types."""
        hidden = [c for c in self.cards.values() if c.state == "Hidden"]
        hidden.sort(key=lambda c: c.id)

        lines = ["Remaining cards (you can guess from these):"]
        for card in hidden:
            lines.append(f"{card.id:2d}. {card.code}")
        return "\n".join(lines)

    def _spymaster_view(self) -> str:
        """View for spymaster - shows card types grouped."""
        hidden = [c for c in self.cards.values() if c.state == "Hidden"]

        # Group by type
        groups: dict[CardType, list[CodenamesCard]] = {
            "Red": [],
            "Blue": [],
            "Civilian": [],
            "Assassin": [],
        }

        for card in hidden:
            groups[card.type].append(card)

        # Sort each group by id
        for group in groups.values():
            group.sort(key=lambda c: c.id)

        lines = ["Remaining cards:"]

        # Display in strategic order
        for card_type in ["Red", "Blue", "Civilian", "Assassin"]:
            if not groups[card_type]:  # type: ignore
                continue
            lines.append(f"\n{card_type.upper()}:")
            for card in groups[card_type]:  # type: ignore
                lines.append(f"{card.id:2d}. {card.code}")

        return "\n".join(lines)

    def reveal(self, card_id: int) -> CodenamesCard:
        """
        Reveal a card by ID.

        Args:
            card_id: ID of card to reveal

        Returns:
            The revealed card

        Raises:
            ValueError: If card doesn't exist
        """
        if card_id not in self.cards:
            raise ValueError(f"Card with id {card_id} does not exist!")
        card = self.cards[card_id]
        card.state = "Revealed"
        return card

    def find_by_codename(self, codename: str) -> CodenamesCard | None:
        """
        Find a card by its codename.

        Args:
            codename: Codename to search for (case-insensitive)

        Returns:
            Card if found, None otherwise
        """
        for card in self.cards.values():
            if card.code.lower() == codename.lower():
                return card
        return None
