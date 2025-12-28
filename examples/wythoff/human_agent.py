"""Human agent implementation for Wythoff's Game."""

from typing import TYPE_CHECKING
from actions import WythoffMoveOutput

if TYPE_CHECKING:
    from game import WythoffGame
    from boardgamepy.core.player import Player


class WythoffHumanAgent:
    """Human agent for Wythoff's Game that handles input via console."""

    def get_action(self, game: "WythoffGame", player: "Player") -> WythoffMoveOutput:
        """Get action from human player via console input."""
        print()
        print(f"Pile A: {game.board.pile_a}, Pile B: {game.board.pile_b}")
        print()
        print("Available moves:")
        print("  1. Remove from Pile A only")
        print("  2. Remove from Pile B only")
        print("  3. Remove from BOTH piles (same amount)")
        print()

        # Get move type
        while True:
            choice = input("Choose move type (1/2/3): ").strip()
            if choice == "1":
                move_type = "pile_a"
                max_count = game.board.pile_a
                break
            elif choice == "2":
                move_type = "pile_b"
                max_count = game.board.pile_b
                break
            elif choice == "3":
                move_type = "both"
                max_count = min(game.board.pile_a, game.board.pile_b)
                break
            print("  Please enter 1, 2, or 3")

        # Get count
        while True:
            try:
                count_str = input(f"How many to remove (1-{max_count})? ").strip()
                count = int(count_str)
                if 1 <= count <= max_count:
                    break
                print(f"  Count must be between 1 and {max_count}")
            except ValueError:
                print("  Please enter a valid number")

        # Optional reasoning
        reasoning = input("Reasoning (optional, press Enter to skip): ").strip()

        return WythoffMoveOutput(
            move_type=move_type,
            count=count,
            reasoning=reasoning if reasoning else None,
        )
