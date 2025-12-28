"""Human agent implementation for Strategic Rock Paper Scissors."""

from typing import TYPE_CHECKING
from actions import StrategyChoiceOutput

if TYPE_CHECKING:
    from strategy_game import StrategyRPSGame
    from boardgamepy.core.player import Player


class RPSHumanAgent:
    """Human agent for Strategic RPS that handles input via console."""

    def get_action(self, game: "StrategyRPSGame", player: "Player") -> StrategyChoiceOutput:
        """Get action from human player via console input."""
        print()
        print("Your choices:")
        print("  (r) Rock")
        print("  (p) Paper")
        print("  (s) Scissors")
        print()

        # Get choice
        while True:
            choice_input = input("Your choice (r/p/s): ").strip().lower()
            if choice_input in ["r", "rock"]:
                choice = "rock"
                break
            elif choice_input in ["p", "paper"]:
                choice = "paper"
                break
            elif choice_input in ["s", "scissors"]:
                choice = "scissors"
                break
            print("  Please enter 'r' for Rock, 'p' for Paper, or 's' for Scissors")

        # Optional reasoning
        reasoning = input("Reasoning (optional, press Enter to skip): ").strip()

        return StrategyChoiceOutput(
            choice=choice,
            reasoning=reasoning if reasoning else None,
        )
