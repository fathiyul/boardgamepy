"""Human agent implementation for DixiQuote."""

from typing import TYPE_CHECKING
from boardgamepy.core.player import Player

if TYPE_CHECKING:
    from game import DixiQuoteGame


class DixiQuoteHumanAgent:
    """
    Human agent for DixiQuote that handles input for all roles.

    This agent prompts the human player for decisions via console input.
    """

    def get_action(self, game: "DixiQuoteGame", player: Player):
        """
        Get action from human player via console input.

        Args:
            game: Current game instance
            player: The human player

        Returns:
            Action output matching the expected schema
        """
        phase = game.state.phase

        if phase == "choose_situation":
            return self._get_situation_choice(game, player)
        elif phase == "give_quote":
            return self._get_quote(game, player)
        elif phase == "submit_situations":
            return self._get_submission(game, player)
        elif phase == "vote":
            return self._get_vote(game, player)
        else:
            raise ValueError(f"Unknown phase: {phase}")

    def _get_situation_choice(self, game: "DixiQuoteGame", player: Player):
        """Get situation choice from human Storyteller."""
        from actions import ChooseSituationOutput

        hand = game.get_player_hand(player.player_idx)

        print()
        print(f"Your Hand ({len(hand)} cards):")
        for i, situation in enumerate(hand, 1):
            print(f"  {i}. {situation}")
        print()

        while True:
            choice = input("→ Enter card number or full situation text: ").strip()

            # Try as number first
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(hand):
                    situation = hand[idx]
                    break
                print(f"  ❌ Number must be between 1 and {len(hand)}!")
            except ValueError:
                # Not a number, try as situation text
                if choice in hand:
                    situation = choice
                    break
                print("  ❌ Not a valid situation card. Try again!")

        reasoning = input("→ Reasoning (optional): ").strip()

        return ChooseSituationOutput(
            situation=situation, reasoning=reasoning if reasoning else None
        )

    def _get_quote(self, game: "DixiQuoteGame", player: Player):
        """Get quote from human Storyteller."""
        from actions import GiveQuoteOutput

        print()
        print(f"Your chosen situation: {game.state.storyteller_situation}")
        print()

        while True:
            quote = input("→ Enter your poetic/quote-like clue (single line): ").strip()
            if quote:
                break
            print("  ❌ Quote cannot be empty!")

        reasoning = input("→ Reasoning (optional): ").strip()

        return GiveQuoteOutput(quote=quote, reasoning=reasoning if reasoning else None)

    def _get_submission(self, game: "DixiQuoteGame", player: Player):
        """Get situation submission from human player."""
        from actions import SubmitSituationOutput

        hand = game.get_player_hand(player.player_idx)

        print()
        print(f"Quote: \"{game.state.storyteller_quote}\"")
        print()
        print(f"Your Hand ({len(hand)} cards):")
        for i, situation in enumerate(hand, 1):
            print(f"  {i}. {situation}")
        print()

        while True:
            choice = input("→ Enter card number or full situation text: ").strip()

            # Try as number first
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(hand):
                    situation = hand[idx]
                    break
                print(f"  ❌ Number must be between 1 and {len(hand)}!")
            except ValueError:
                # Not a number, try as situation text
                if choice in hand:
                    situation = choice
                    break
                print("  ❌ Not a valid situation card. Try again!")

        reasoning = input("→ Reasoning (optional): ").strip()

        return SubmitSituationOutput(
            situation=situation, reasoning=reasoning if reasoning else None
        )

    def _get_vote(self, game: "DixiQuoteGame", player: Player):
        """Get vote from human player."""
        from actions import VoteOutput

        all_situations = game.state.get_all_submitted_situations()

        # Get player's own submission and remove it from the list
        own_submission = None
        if player.player_idx in game.state.submitted_situations:
            own_submission = game.state.submitted_situations[player.player_idx]

        # Filter out player's own submission
        votable_situations = [s for s in all_situations if s != own_submission]

        print()
        print(f"Quote: \"{game.state.storyteller_quote}\"")
        print()
        if own_submission:
            print("(Your own submission has been hidden)")
            print()
        print("Available Situations to Vote For:")
        for i, situation in enumerate(votable_situations, 1):
            print(f"  {i}. {situation}")
        print()

        while True:
            choice = input("→ Enter card number or full situation text: ").strip()

            # Try as number first
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(votable_situations):
                    situation = votable_situations[idx]
                    break
                print(f"  ❌ Number must be between 1 and {len(votable_situations)}!")
            except ValueError:
                # Not a number, try as situation text
                if choice in votable_situations:
                    situation = choice
                    break
                print("  ❌ Not a valid situation. Try again!")

        reasoning = input("→ Reasoning (optional): ").strip()

        return VoteOutput(
            situation=situation, reasoning=reasoning if reasoning else None
        )
