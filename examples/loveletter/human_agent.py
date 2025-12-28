"""Human agent implementation for Love Letter."""

from typing import TYPE_CHECKING
from actions import PlayCardOutput
from cards import CardType

if TYPE_CHECKING:
    from game import LoveLetterGame
    from boardgamepy.core.player import Player


# Card descriptions for human reference
CARD_INFO = {
    "Guard": "(1) Guess a player's card - if correct, they're eliminated",
    "Priest": "(2) Look at another player's hand",
    "Baron": "(3) Compare hands - lower value is eliminated",
    "Handmaid": "(4) Protection until your next turn",
    "Prince": "(5) Force a player (or yourself) to discard and draw",
    "King": "(6) Trade hands with another player",
    "Countess": "(7) Must play if you have King or Prince",
    "Princess": "(8) If you play or discard this, you're eliminated",
}


class LoveLetterHumanAgent:
    """Human agent for Love Letter that handles input via console."""

    def get_action(self, game: "LoveLetterGame", player: "Player") -> PlayCardOutput:
        """Get action from human player via console input."""
        player_idx = game.state.current_player_idx
        hand = game.board.hands[player_idx]

        print()
        print("Your hand:")
        for i, card in enumerate(hand, 1):
            print(f"  {i}. {card.name} {CARD_INFO.get(card.name, '')}")
        print()

        # Check Countess rule
        has_countess = any(c.type == CardType.COUNTESS for c in hand)
        has_king_or_prince = any(c.type in [CardType.KING, CardType.PRINCE] for c in hand)
        must_play_countess = has_countess and has_king_or_prince and len(hand) == 2

        if must_play_countess:
            print("  (You must play Countess because you have King or Prince)")
            card_to_play = "Countess"
        else:
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

        # Get target if needed
        target_player = None
        cards_needing_target = ["Guard", "Priest", "Baron", "King"]
        cards_needing_target_or_self = ["Prince"]

        targetable = game.board.get_targetable_players(player_idx)

        if card_to_play in cards_needing_target:
            if targetable:
                print()
                print("Targetable players:")
                for idx in targetable:
                    print(f"  Player {idx + 1}")
                print()

                while True:
                    target_str = input("Target player number: ").strip()
                    try:
                        target = int(target_str)
                        if target - 1 in targetable:
                            target_player = target
                            break
                    except ValueError:
                        pass
                    print("  Please enter a valid targetable player number")
            else:
                print("  (No targetable players - card will have no effect)")

        elif card_to_play in cards_needing_target_or_self:
            # Prince can target self or others
            valid_targets = targetable | {player_idx}
            print()
            print("Targetable players (including yourself):")
            for idx in valid_targets:
                marker = "(you)" if idx == player_idx else ""
                print(f"  Player {idx + 1} {marker}")
            print()

            while True:
                target_str = input("Target player number: ").strip()
                try:
                    target = int(target_str)
                    if target - 1 in valid_targets:
                        target_player = target
                        break
                except ValueError:
                    pass
                print("  Please enter a valid target")

        # Get guess for Guard
        guess_card = None
        if card_to_play == "Guard" and target_player:
            print()
            print("Guess a card (cannot guess Guard):")
            guessable = ["Priest", "Baron", "Handmaid", "Prince", "King", "Countess", "Princess"]
            for i, card_name in enumerate(guessable, 1):
                print(f"  {i}. {card_name}")
            print()

            while True:
                guess_str = input("Your guess (1-7): ").strip()
                try:
                    guess_idx = int(guess_str) - 1
                    if 0 <= guess_idx < len(guessable):
                        guess_card = guessable[guess_idx]
                        break
                except ValueError:
                    pass
                print("  Please enter a number between 1 and 7")

        # Optional reasoning
        reasoning = input("Reasoning (optional, press Enter to skip): ").strip()

        return PlayCardOutput(
            card_to_play=card_to_play,
            target_player=target_player,
            guess_card=guess_card,
            reasoning=reasoning if reasoning else None,
        )
