"""Human agent implementation for Sushi Go!"""

from typing import TYPE_CHECKING

from actions import PlayCardOutput
from cards import CardType

if TYPE_CHECKING:
    from game import SushiGoGame

    from boardgamepy.core.player import Player


# Short card effect descriptions
CARD_EFFECTS = {
    CardType.MAKI_1: "Most: 6/3pts",
    CardType.MAKI_2: "Most: 6/3pts",
    CardType.MAKI_3: "Most: 6/3pts",
    CardType.TEMPURA: "2 = 5pts",
    CardType.SASHIMI: "3 = 10pts",
    CardType.DUMPLING: "1/2/3/4/5+ = 1/3/6/10/15pts",
    CardType.EGG_NIGIRI: "1pt",
    CardType.SALMON_NIGIRI: "2pts",
    CardType.SQUID_NIGIRI: "3pts",
    CardType.WASABI: "3x next Nigiri",
    CardType.CHOPSTICKS: "Swap to play 2 cards",
    CardType.PUDDING: "End: Most +6, Least -6",
}


class SushiGoHumanAgent:
    """Human agent for Sushi Go! that handles input via console."""

    def get_action(self, game: "SushiGoGame", player: "Player") -> PlayCardOutput:
        """Get action from human player via console input."""
        player_idx = player.player_idx
        hand = game.board.hands[player_idx]
        collection = game.board.collections[player_idx]

        # Auto-take last card (no need to choose)
        if len(hand) == 1:
            card_to_play = hand[0].name
            print(f"\nLast card - auto-playing: {card_to_play}")
            return PlayCardOutput(
                card_to_play=card_to_play,
                second_card=None,
                reasoning=None,
            )

        # Check if player has chopsticks in collection
        has_chopsticks = any(c.type == CardType.CHOPSTICKS for c in collection)

        # Show hand with effects
        print("\nYour hand:")
        for i, card in enumerate(hand, 1):
            effect = CARD_EFFECTS.get(card.type, "")
            print(f"  {i}. {card.name} - {effect}")
        print()

        if has_chopsticks and len(hand) >= 2:
            print("  🥢 You have CHOPSTICKS! You can play 2 cards this turn.")
            print()

        # Get first card choice
        while True:
            choice = input(f"Which card to play (1-{len(hand)})? ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(hand):
                    first_card = hand[idx]
                    card_to_play = first_card.name
                    break
            except ValueError:
                pass
            print(f"  Please enter a number between 1 and {len(hand)}")

        second_card = None

        # If player has chopsticks and more than 1 card left, offer to use them
        if has_chopsticks and len(hand) >= 2:
            print()
            use_chopsticks = input("Use CHOPSTICKS to play a second card? (y/n): ").strip().lower()
            if use_chopsticks in ["y", "yes"]:
                # Show remaining cards
                print("\nRemaining cards:")
                remaining = [(i, c) for i, c in enumerate(hand, 1) if c.id != first_card.id]
                for orig_idx, card in remaining:
                    effect = CARD_EFFECTS.get(card.type, "")
                    print(f"  {orig_idx}. {card.name} - {effect}")
                print()

                # Get second card choice
                valid_indices = [i for i, _ in remaining]
                while True:
                    choice = input(f"Which second card ({'/'.join(map(str, valid_indices))})? ").strip()
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(hand) and hand[idx].id != first_card.id:
                            second_card = hand[idx].name
                            print(f"\nUsing chopsticks to play: {card_to_play} + {second_card}")
                            break
                    except ValueError:
                        pass
                    print(f"  Please enter a valid number from: {valid_indices}")

        return PlayCardOutput(
            card_to_play=card_to_play,
            second_card=second_card,
            reasoning=None,
        )
