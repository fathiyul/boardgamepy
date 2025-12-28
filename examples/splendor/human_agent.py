"""Human agent implementation for Splendor."""

from typing import TYPE_CHECKING
from actions import GameActionOutput
from cards import GemType

if TYPE_CHECKING:
    from game import SplendorGame
    from boardgamepy.core.player import Player


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


class SplendorHumanAgent:
    """Human agent for Splendor that handles input via console."""

    def get_action(self, game: "SplendorGame", player: "Player") -> GameActionOutput:
        """Get action from human player via console input."""
        player_idx = player.player_idx

        # Show current situation
        self._show_player_status(game, player_idx)
        self._show_available_actions(game, player_idx)

        # Get action type
        while True:
            print("\nWhat would you like to do?")
            print("  1. Take gems")
            print("  2. Purchase a card")
            print("  3. Reserve a card")

            choice = input("\nYour choice (1-3): ").strip()

            if choice == "1":
                return self._take_gems(game, player_idx)
            elif choice == "2":
                result = self._purchase_card(game, player_idx)
                if result:
                    return result
            elif choice == "3":
                result = self._reserve_card(game, player_idx)
                if result:
                    return result
            else:
                print("Please enter 1, 2, or 3")

    def _show_player_status(self, game: "SplendorGame", player_idx: int) -> None:
        """Show the current player's status."""
        print()
        print("=" * 50)
        print("YOUR STATUS")
        print("=" * 50)

        # Gems
        gems = game.board.player_gems[player_idx]
        total_gems = game.board.get_total_gems(player_idx)
        print(f"\nYour gems ({total_gems}/10):")
        gem_list = []
        for gem in [GemType.DIAMOND, GemType.SAPPHIRE, GemType.EMERALD, GemType.RUBY, GemType.ONYX, GemType.GOLD]:
            count = gems[gem]
            if count > 0:
                gem_list.append(f"{_get_gem_icon(gem)} {gem.value}×{count}")
        print(f"  {', '.join(gem_list) if gem_list else 'None'}")

        # Bonuses from cards
        bonuses = game.board.get_player_bonuses(player_idx)
        bonus_list = []
        for gem in [GemType.DIAMOND, GemType.SAPPHIRE, GemType.EMERALD, GemType.RUBY, GemType.ONYX]:
            count = bonuses[gem]
            if count > 0:
                bonus_list.append(f"{_get_gem_icon(gem)}×{count}")
        print(f"\nYour bonuses (permanent): {', '.join(bonus_list) if bonus_list else 'None'}")

        # Points
        card_points = game.board.get_player_points(player_idx)
        noble_points = len(game.state.player_nobles.get(player_idx, [])) * 3
        total = card_points + noble_points
        print(f"\nYour points: {total} ({card_points} from cards + {noble_points} from nobles)")

        # Reserved cards
        reserved = game.board.player_reserved[player_idx]
        if reserved:
            print(f"\nYour reserved cards:")
            for card in reserved:
                cost_str = ", ".join(f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items())
                can_afford = "✅" if game.board.can_afford_card(player_idx, card) else "❌"
                print(f"  [{card.card_id}] {can_afford} {card.points}pts {_get_gem_icon(card.bonus)} Cost: {cost_str}")

    def _show_available_actions(self, game: "SplendorGame", player_idx: int) -> None:
        """Show available actions."""
        print()
        print("=" * 50)
        print("AVAILABLE ACTIONS")
        print("=" * 50)

        # Gem bank
        print("\nGem Bank:")
        gem_list = []
        for gem in [GemType.DIAMOND, GemType.SAPPHIRE, GemType.EMERALD, GemType.RUBY, GemType.ONYX]:
            count = game.board.gem_bank[gem]
            gem_list.append(f"{_get_gem_icon(gem)} {gem.value}:{count}")
        gold_count = game.board.gem_bank[GemType.GOLD]
        gem_list.append(f"{_get_gem_icon(GemType.GOLD)} Gold:{gold_count}")
        print(f"  {', '.join(gem_list)}")

        # Affordable cards
        affordable = []
        for card in (game.board.tier1_display + game.board.tier2_display + game.board.tier3_display):
            if game.board.can_afford_card(player_idx, card):
                affordable.append(card)

        if affordable:
            print(f"\nCards you can afford:")
            for card in affordable:
                cost_str = ", ".join(f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items())
                print(f"  [{card.card_id}] T{card.tier} {card.points}pts {_get_gem_icon(card.bonus)} Cost: {cost_str}")

    def _take_gems(self, game: "SplendorGame", player_idx: int) -> GameActionOutput:
        """Handle taking gems action."""
        print("\n--- TAKE GEMS ---")

        # Check gem limits
        total_gems = game.board.get_total_gems(player_idx)
        max_take = min(3, 10 - total_gems)

        if max_take <= 0:
            print("You have 10 gems! You cannot take more.")
            print("(You can still take gems but must return some)")

        # Show options
        print("\nOptions:")
        print("  a. Take 3 different gems (1 of each)")
        print("  b. Take 2 of the same gem (requires 4+ in bank)")

        while True:
            choice = input("\nYour choice (a/b): ").strip().lower()

            if choice == "a":
                return self._take_three_different(game, player_idx)
            elif choice == "b":
                result = self._take_two_same(game, player_idx)
                if result:
                    return result
            else:
                print("Please enter 'a' or 'b'")

    def _take_three_different(self, game: "SplendorGame", player_idx: int) -> GameActionOutput:
        """Take 3 different gems."""
        gem_names = ["Diamond", "Sapphire", "Emerald", "Ruby", "Onyx"]
        available = [g for g in gem_names if game.board.gem_bank[GemType[g.upper()]] > 0]

        print(f"\nAvailable gems: {', '.join(available)}")

        gems = []
        for i in range(3):
            while True:
                prompt = f"Gem {i + 1} (or press Enter if done): " if i > 0 else f"First gem: "
                choice = input(prompt).strip().capitalize()

                if choice == "" and i >= 1:
                    # Pad with None
                    while len(gems) < 3:
                        gems.append(None)
                    break

                if choice not in available:
                    print(f"  Please choose from: {', '.join(available)}")
                    continue

                if choice in gems:
                    print(f"  You already selected {choice}. Choose a different gem.")
                    continue

                gems.append(choice)
                available.remove(choice)
                break

            if len(gems) == 3:
                break

        return GameActionOutput(
            action_type="take_gems",
            gem1=gems[0],
            gem2=gems[1] if len(gems) > 1 else None,
            gem3=gems[2] if len(gems) > 2 else None,
            take_two=False,
            reasoning=None,
        )

    def _take_two_same(self, game: "SplendorGame", player_idx: int) -> GameActionOutput | None:
        """Take 2 of the same gem."""
        gem_names = ["Diamond", "Sapphire", "Emerald", "Ruby", "Onyx"]
        available = [g for g in gem_names if game.board.gem_bank[GemType[g.upper()]] >= 4]

        if not available:
            print("No gems have 4+ in bank. You must take 3 different.")
            return None

        print(f"\nGems with 4+ available: {', '.join(available)}")

        while True:
            choice = input("Which gem to take 2 of? ").strip().capitalize()

            if choice not in available:
                print(f"  Please choose from: {', '.join(available)}")
                continue

            return GameActionOutput(
                action_type="take_gems",
                gem1=choice,
                gem2=None,
                gem3=None,
                take_two=True,
                reasoning=None,
            )

    def _purchase_card(self, game: "SplendorGame", player_idx: int) -> GameActionOutput | None:
        """Handle purchasing a card."""
        print("\n--- PURCHASE CARD ---")

        # Show purchasable cards
        all_cards = []
        reserved = game.board.player_reserved[player_idx]

        # Reserved cards first
        if reserved:
            print("\nYour reserved cards:")
            for card in reserved:
                cost_str = ", ".join(f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items())
                can_afford = "✅" if game.board.can_afford_card(player_idx, card) else "❌"
                print(f"  [{card.card_id}] {can_afford} T{card.tier} {card.points}pts {_get_gem_icon(card.bonus)} Cost: {cost_str}")
                if game.board.can_afford_card(player_idx, card):
                    all_cards.append((card, True))

        # Display cards
        print("\nCards on display:")
        for tier_name, tier_cards in [("Tier 3", game.board.tier3_display),
                                       ("Tier 2", game.board.tier2_display),
                                       ("Tier 1", game.board.tier1_display)]:
            print(f"  {tier_name}:")
            for card in tier_cards:
                cost_str = ", ".join(f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items())
                can_afford = "✅" if game.board.can_afford_card(player_idx, card) else "❌"
                print(f"    [{card.card_id}] {can_afford} {card.points}pts {_get_gem_icon(card.bonus)} Cost: {cost_str}")
                if game.board.can_afford_card(player_idx, card):
                    all_cards.append((card, False))

        if not all_cards:
            print("\nYou cannot afford any cards!")
            return None

        # Get choice
        while True:
            choice = input("\nEnter card ID to purchase (or 'back'): ").strip()

            if choice.lower() == "back":
                return None

            try:
                card_id = int(choice)

                # Check reserved first
                for card in reserved:
                    if card.card_id == card_id:
                        if game.board.can_afford_card(player_idx, card):
                            return GameActionOutput(
                                action_type="purchase",
                                card_id=card_id,
                                from_reserved=True,
                                reasoning=None,
                            )
                        else:
                            print("  You cannot afford this card!")
                            break

                # Check display
                for card in game.board.tier1_display + game.board.tier2_display + game.board.tier3_display:
                    if card.card_id == card_id:
                        if game.board.can_afford_card(player_idx, card):
                            return GameActionOutput(
                                action_type="purchase",
                                card_id=card_id,
                                from_reserved=False,
                                reasoning=None,
                            )
                        else:
                            print("  You cannot afford this card!")
                            break
                else:
                    print("  Invalid card ID")

            except ValueError:
                print("  Please enter a valid card ID number")

    def _reserve_card(self, game: "SplendorGame", player_idx: int) -> GameActionOutput | None:
        """Handle reserving a card."""
        print("\n--- RESERVE CARD ---")

        # Check reserve limit
        if len(game.board.player_reserved[player_idx]) >= 3:
            print("You already have 3 reserved cards! Cannot reserve more.")
            return None

        # Show available cards
        print("\nCards on display:")
        for tier_name, tier_cards, tier_num in [("Tier 3", game.board.tier3_display, 3),
                                                 ("Tier 2", game.board.tier2_display, 2),
                                                 ("Tier 1", game.board.tier1_display, 1)]:
            print(f"  {tier_name}:")
            for card in tier_cards:
                cost_str = ", ".join(f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items())
                print(f"    [{card.card_id}] {card.points}pts {_get_gem_icon(card.bonus)} Cost: {cost_str}")

        gold_available = game.board.gem_bank[GemType.GOLD] > 0
        if gold_available:
            print(f"\n(You will receive a {_get_gem_icon(GemType.GOLD)} gold token)")

        # Get choice
        while True:
            choice = input("\nEnter card ID to reserve (or 'back'): ").strip()

            if choice.lower() == "back":
                return None

            try:
                card_id = int(choice)

                # Find the card
                for tier_cards, tier_num in [(game.board.tier3_display, 3),
                                              (game.board.tier2_display, 2),
                                              (game.board.tier1_display, 1)]:
                    for card in tier_cards:
                        if card.card_id == card_id:
                            return GameActionOutput(
                                action_type="reserve",
                                card_id=card_id,
                                tier=tier_num,
                                reasoning=None,
                            )

                print("  Invalid card ID")

            except ValueError:
                print("  Please enter a valid card ID number")
