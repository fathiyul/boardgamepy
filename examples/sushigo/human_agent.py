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
        player_idx = int(player.team.split()[-1]) - 1
        hand = game.board.hands[player_idx]

        # Show hand with effects (view already shows hand, but here we add effects)
        print("\nYour hand:")
        for i, card in enumerate(hand, 1):
            effect = CARD_EFFECTS.get(card.type, "")
            print(f"  {i}. {card.name} - {effect}")
        print()

        # Get card choice
        while True:
            choice = input(f"Which card to play (1-{len(hand)})? ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(hand):
                    card_to_play = hand[idx].name
                    break
            except ValueError:
                pass
            print(f"  Please enter a number between 1 and {len(hand)}")

        return PlayCardOutput(
            card_to_play=card_to_play,
            reasoning=None,
        )
