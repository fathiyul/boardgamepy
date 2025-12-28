"""Human agent implementation for Incan Gold."""

from typing import TYPE_CHECKING
from actions import DecisionOutput

if TYPE_CHECKING:
    from game import IncanGoldGame
    from boardgamepy.core.player import Player


class IncanGoldHumanAgent:
    """Human agent for Incan Gold that handles input via console."""

    def get_action(self, game: "IncanGoldGame", player: "Player") -> DecisionOutput:
        """Get action from human player via console input."""
        player_idx = int(player.team.split()[-1]) - 1

        # Show current situation
        temp_gems = game.board.player_temp_gems[player_idx]
        safe_gems = game.board.player_gems[player_idx]

        print()
        print(f"You are carrying: {temp_gems} gems")
        print(f"Safe in camp: {safe_gems} gems")
        print(f"Gems on the path: {game.board.gems_on_path}")
        print()

        # Show hazard situation
        if game.board.hazards_seen:
            print("Hazards encountered so far:")
            for hazard_type, count in game.board.hazards_seen.items():
                if count == 1:
                    print(f"  {hazard_type.value}: 1 (DANGER - second one collapses temple!)")
            print()

        print("Your options:")
        print("  c - CONTINUE exploring (risky but potentially rewarding)")
        print("  r - RETURN to camp (safe, keep your gems)")
        print("  (or just press Enter to continue)")
        print()

        # Get decision
        while True:
            choice = input("Your decision (c/r): ").strip().lower()
            if choice == "" or choice in ["c", "continue"]:
                decision = "continue"
                break
            elif choice in ["r", "return"]:
                decision = "return"
                break
            print("  Please enter 'c' to continue, 'r' to return, or Enter to continue")

        return DecisionOutput(
            decision=decision,
            reasoning=None,
        )
