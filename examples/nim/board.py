"""Nim board implementation."""

from typing import TYPE_CHECKING
from boardgamepy import Board

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class NimBoard(Board):
    """
    Nim game board with multiple piles.

    Each pile contains a number of objects (stones, sticks, etc.).
    Players remove objects from one pile per turn.
    """

    def __init__(self, piles: list[int]):
        """
        Initialize board with given pile sizes.

        Args:
            piles: List of integers representing objects in each pile
                   e.g., [3, 5, 7] means 3 piles with 3, 5, and 7 objects
        """
        self.piles = list(piles)  # Copy to avoid mutation

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view (no hidden information in Nim).

        Everyone sees all piles.
        """
        lines = ["Piles:"]
        for i, count in enumerate(self.piles, 1):
            stones = "●" * count if count > 0 else "(empty)"
            lines.append(f"  Pile {i}: {stones} ({count})")
        return "\n".join(lines)

    def remove_from_pile(self, pile_index: int, count: int) -> None:
        """
        Remove objects from a pile.

        Args:
            pile_index: Index of pile (0-based)
            count: Number of objects to remove

        Raises:
            ValueError: If pile_index invalid or count too large
        """
        if pile_index < 0 or pile_index >= len(self.piles):
            raise ValueError(f"Invalid pile index: {pile_index}")

        if count < 1:
            raise ValueError("Must remove at least 1 object")

        if count > self.piles[pile_index]:
            raise ValueError(
                f"Cannot remove {count} from pile with {self.piles[pile_index]} objects"
            )

        self.piles[pile_index] -= count

    def is_pile_valid(self, pile_index: int) -> bool:
        """Check if pile index is valid."""
        return 0 <= pile_index < len(self.piles)

    def get_pile_size(self, pile_index: int) -> int:
        """Get number of objects in a pile."""
        if not self.is_pile_valid(pile_index):
            return 0
        return self.piles[pile_index]

    def is_empty(self) -> bool:
        """Check if all piles are empty (game over condition)."""
        return all(count == 0 for count in self.piles)

    def total_objects(self) -> int:
        """Get total number of objects remaining."""
        return sum(self.piles)

    def get_non_empty_piles(self) -> list[int]:
        """Get indices of non-empty piles (0-based)."""
        return [i for i, count in enumerate(self.piles) if count > 0]
