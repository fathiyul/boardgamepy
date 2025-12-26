"""Wythoff's Game board implementation."""

import math
from typing import TYPE_CHECKING
from boardgamepy import Board

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class WythoffBoard(Board):
    """
    Wythoff's Game board with two piles.

    Players can:
    1. Remove any number from pile A only
    2. Remove any number from pile B only
    3. Remove the SAME number from both piles simultaneously
    """

    def __init__(self, pile_a: int, pile_b: int):
        """
        Initialize board with two piles.

        Args:
            pile_a: Initial count for pile A
            pile_b: Initial count for pile B
        """
        if pile_a < 0 or pile_b < 0:
            raise ValueError("Pile counts must be non-negative")
        self.pile_a = pile_a
        self.pile_b = pile_b
        self.initial_a = pile_a
        self.initial_b = pile_b

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view (no hidden information).

        Everyone sees both pile counts.
        """
        stones_a = "●" * min(self.pile_a, 40)
        stones_b = "●" * min(self.pile_b, 40)

        if self.pile_a > 40:
            stones_a += f"... (+{self.pile_a - 40} more)"
        if self.pile_b > 40:
            stones_b += f"... (+{self.pile_b - 40} more)"

        lines = [
            "Two Piles:",
            f"  Pile A: {stones_a} ({self.pile_a})",
            f"  Pile B: {stones_b} ({self.pile_b})",
        ]
        return "\n".join(lines)

    def remove_from_a(self, count: int) -> None:
        """
        Remove objects from pile A only.

        Args:
            count: Number to remove

        Raises:
            ValueError: If count is invalid
        """
        if count < 1:
            raise ValueError("Must remove at least 1 object")
        if count > self.pile_a:
            raise ValueError(f"Cannot remove {count} from pile A with {self.pile_a} objects")
        self.pile_a -= count

    def remove_from_b(self, count: int) -> None:
        """
        Remove objects from pile B only.

        Args:
            count: Number to remove

        Raises:
            ValueError: If count is invalid
        """
        if count < 1:
            raise ValueError("Must remove at least 1 object")
        if count > self.pile_b:
            raise ValueError(f"Cannot remove {count} from pile B with {self.pile_b} objects")
        self.pile_b -= count

    def remove_from_both(self, count: int) -> None:
        """
        Remove same number from both piles simultaneously.

        Args:
            count: Number to remove from each pile

        Raises:
            ValueError: If count is invalid
        """
        if count < 1:
            raise ValueError("Must remove at least 1 object")
        if count > self.pile_a:
            raise ValueError(f"Cannot remove {count} from pile A with {self.pile_a} objects")
        if count > self.pile_b:
            raise ValueError(f"Cannot remove {count} from pile B with {self.pile_b} objects")
        self.pile_a -= count
        self.pile_b -= count

    def is_empty(self) -> bool:
        """Check if both piles are empty (game over)."""
        return self.pile_a == 0 and self.pile_b == 0

    def total_objects(self) -> int:
        """Get total objects across both piles."""
        return self.pile_a + self.pile_b

    @staticmethod
    def is_losing_position(a: int, b: int) -> bool:
        """
        Check if (a, b) is a losing position (P-position) in Wythoff's game.

        Uses the golden ratio to determine P-positions.
        P-positions are characterized by the Beatty sequences.

        Args:
            a: Pile A count (should be min of the two)
            b: Pile B count (should be max of the two)

        Returns:
            True if this is a losing position
        """
        # Ensure a <= b
        if a > b:
            a, b = b, a

        # Golden ratio φ = (1 + √5) / 2
        phi = (1 + math.sqrt(5)) / 2

        # For each k, the k-th P-position is (a_k, b_k) where:
        # a_k = floor(k * φ)
        # b_k = floor(k * φ²) = a_k + k

        # Check if current position matches any P-position
        # We only need to check k values up to a (since a_k >= k)
        for k in range(a + 1):
            a_k = int(k * phi)
            b_k = int(k * phi * phi)
            if a_k == a and b_k == b:
                return True

        return False

    def get_move_type_hint(self) -> str:
        """Get a hint about the current position."""
        if self.is_losing_position(self.pile_a, self.pile_b):
            return "This is a losing position! Any move gives opponent advantage."
        return "This is a winning position. There exists a move to a losing position."
