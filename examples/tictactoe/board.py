"""Tic-Tac-Toe board implementation."""

from typing import Literal, TYPE_CHECKING
from boardgamepy import Board
from boardgamepy.protocols import SimpleViewContext

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext

Mark = Literal["X", "O", " "]


class TicTacToeBoard(Board):
    """
    3x3 Tic-Tac-Toe board.

    Positions numbered 1-9:
    1 | 2 | 3
    ---------
    4 | 5 | 6
    ---------
    7 | 8 | 9
    """

    def __init__(self):
        """Initialize empty board."""
        self.grid: dict[int, Mark] = {i: " " for i in range(1, 10)}

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view (no hidden information in Tic-Tac-Toe).

        Everyone sees the same board state.
        """
        lines = ["Positions:"]
        lines.append(f" {self.grid[1]} | {self.grid[2]} | {self.grid[3]} ")
        lines.append("-----------")
        lines.append(f" {self.grid[4]} | {self.grid[5]} | {self.grid[6]} ")
        lines.append("-----------")
        lines.append(f" {self.grid[7]} | {self.grid[8]} | {self.grid[9]} ")
        return "\n".join(lines)

    def place_mark(self, position: int, mark: Mark) -> None:
        """Place a mark at the given position."""
        if position < 1 or position > 9:
            raise ValueError(f"Position must be 1-9, got {position}")
        if self.grid[position] != " ":
            raise ValueError(f"Position {position} is already taken")
        self.grid[position] = mark

    def is_position_empty(self, position: int) -> bool:
        """Check if a position is empty."""
        return self.grid.get(position, " ") == " "

    def get_empty_positions(self) -> list[int]:
        """Get list of empty positions."""
        return [pos for pos in range(1, 10) if self.grid[pos] == " "]

    def check_winner(self) -> Mark | None:
        """
        Check if there's a winner.

        Returns:
            "X" or "O" if there's a winner, None otherwise
        """
        # All possible winning combinations
        winning_combinations = [
            [1, 2, 3],  # Top row
            [4, 5, 6],  # Middle row
            [7, 8, 9],  # Bottom row
            [1, 4, 7],  # Left column
            [2, 5, 8],  # Middle column
            [3, 6, 9],  # Right column
            [1, 5, 9],  # Diagonal \
            [3, 5, 7],  # Diagonal /
        ]

        for combo in winning_combinations:
            marks = [self.grid[pos] for pos in combo]
            if marks[0] != " " and marks[0] == marks[1] == marks[2]:
                return marks[0]

        return None

    def is_full(self) -> bool:
        """Check if board is full (draw condition)."""
        return all(mark != " " for mark in self.grid.values())
