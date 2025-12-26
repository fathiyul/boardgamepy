"""Subtract-a-Square board implementation."""

import math
from typing import TYPE_CHECKING
from boardgamepy import Board

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class SubtractASquareBoard(Board):
    """
    Subtract-a-Square game board with a single pile.

    Players can only remove perfect square numbers (1, 4, 9, 16, 25, ...)
    from the pile on each turn.
    """

    def __init__(self, initial_count: int):
        """
        Initialize board with a pile of objects.

        Args:
            initial_count: Starting number of objects in the pile
        """
        if initial_count < 1:
            raise ValueError("Initial count must be at least 1")
        self.count = initial_count
        self.initial_count = initial_count

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view (no hidden information).

        Everyone sees the pile count.
        """
        stones = "●" * min(self.count, 50)  # Limit visual display to 50
        if self.count > 50:
            stones += f"... (+{self.count - 50} more)"

        return f"Pile: {stones}\nCount: {self.count}"

    def remove(self, amount: int) -> None:
        """
        Remove objects from the pile.

        Args:
            amount: Number of objects to remove (must be a perfect square)

        Raises:
            ValueError: If amount is not valid
        """
        if not self.is_perfect_square(amount):
            raise ValueError(f"{amount} is not a perfect square")

        if amount > self.count:
            raise ValueError(f"Cannot remove {amount} from pile with {self.count} objects")

        self.count -= amount

    def is_empty(self) -> bool:
        """Check if pile is empty (game over condition)."""
        return self.count == 0

    def get_valid_moves(self) -> list[int]:
        """
        Get list of valid moves (perfect squares <= current count).

        Returns:
            List of valid amounts that can be removed
        """
        max_square_root = int(math.sqrt(self.count))
        return [i * i for i in range(1, max_square_root + 1)]

    @staticmethod
    def is_perfect_square(n: int) -> bool:
        """Check if a number is a perfect square."""
        if n < 1:
            return False
        sqrt = int(math.sqrt(n))
        return sqrt * sqrt == n
