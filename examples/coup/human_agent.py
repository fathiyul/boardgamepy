"""Human agent implementation for Coup."""

from typing import TYPE_CHECKING
from actions import CoupActionOutput

if TYPE_CHECKING:
    from game import CoupGame
    from boardgamepy.core.player import Player


# Action descriptions for human reference
ACTION_INFO = {
    "income": "Take 1 coin (cannot be blocked)",
    "foreign_aid": "Take 2 coins (can be blocked by Duke)",
    "coup": "Pay 7 coins to eliminate one influence (cannot be blocked)",
    "tax": "Claim Duke - Take 3 coins",
    "assassinate": "Claim Assassin - Pay 3 coins to eliminate one influence",
    "steal": "Claim Captain - Take 2 coins from another player",
    "exchange": "Claim Ambassador - Exchange cards with the Court",
}


class CoupHumanAgent:
    """Human agent for Coup that handles input via console."""

    def get_action(self, game: "CoupGame", player: "Player") -> CoupActionOutput:
        """Get action from human player via console input."""
        player_idx = game.state.current_player_idx
        coins = game.board.coins[player_idx]

        # Show your influence
        print()
        print("Your influence cards:")
        for card in game.board.influence[player_idx]:
            if card.revealed:
                print(f"  [REVEALED] {card.type.char_name}")
            else:
                print(f"  {card.type.char_name}")
        print(f"\nYour coins: {coins}")
        print()

        # Must coup with 10+ coins
        if coins >= 10:
            print("You have 10+ coins - you MUST coup!")
            action = "coup"
        else:
            # Show available actions
            print("Available actions:")
            actions = []

            # Always available
            actions.append(("income", "1"))
            print(f"  1. Income - {ACTION_INFO['income']}")

            actions.append(("foreign_aid", "2"))
            print(f"  2. Foreign Aid - {ACTION_INFO['foreign_aid']}")

            if coins >= 7:
                actions.append(("coup", "3"))
                print(f"  3. Coup - {ACTION_INFO['coup']}")

            # Character actions (can be claimed even if you don't have the character)
            actions.append(("tax", "4"))
            print(f"  4. Tax (Duke) - {ACTION_INFO['tax']}")

            if coins >= 3:
                actions.append(("assassinate", "5"))
                print(f"  5. Assassinate (Assassin) - {ACTION_INFO['assassinate']}")

            actions.append(("steal", "6"))
            print(f"  6. Steal (Captain) - {ACTION_INFO['steal']}")

            actions.append(("exchange", "7"))
            print(f"  7. Exchange (Ambassador) - {ACTION_INFO['exchange']}")

            print()

            # Get action choice
            valid_nums = [num for _, num in actions]
            while True:
                choice = input(f"Choose action ({'/'.join(valid_nums)}): ").strip()
                for act, num in actions:
                    if choice == num:
                        action = act
                        break
                else:
                    print(f"  Please enter one of: {', '.join(valid_nums)}")
                    continue
                break

        # Get target if needed
        target_player = None
        actions_needing_target = ["coup", "assassinate", "steal"]

        if action in actions_needing_target:
            # Find valid targets
            valid_targets = []
            for i in range(game.num_players):
                if i != player_idx and game.board.has_influence(i):
                    valid_targets.append(i + 1)

            if valid_targets:
                print()
                print("Available targets:")
                for t in valid_targets:
                    target_coins = game.board.coins[t - 1]
                    print(f"  Player {t} ({target_coins} coins)")
                print()

                while True:
                    target_str = input("Target player number: ").strip()
                    try:
                        target = int(target_str)
                        if target in valid_targets:
                            target_player = target
                            break
                    except ValueError:
                        pass
                    print(f"  Please enter one of: {valid_targets}")

        # Optional reasoning
        reasoning = input("Reasoning (optional, press Enter to skip): ").strip()

        return CoupActionOutput(
            action=action,
            target_player=target_player,
            challenge=False,
            character_to_reveal=None,
            reasoning=reasoning if reasoning else None,
        )
