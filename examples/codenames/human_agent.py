"""Human agent implementation for Codenames."""

from typing import TYPE_CHECKING
from boardgamepy.core.player import Player
from boardgamepy.protocols import SimpleViewContext
from .actions import ClueAction, GuessAction, PassAction

if TYPE_CHECKING:
    from game import CodenamesGame


class CodenamesHumanAgent:
    """
    Human agent for Codenames that handles input for both roles.

    This agent prompts the human player for decisions via console input,
    showing them the appropriate board view based on their role.
    """

    def get_action(self, game: "CodenamesGame", player: Player):
        """
        Get action from human player via console input.

        Args:
            game: Current game instance
            player: The human player

        Returns:
            Action output matching the expected schema (ClueOutput or GuessOutput)
        """
        # Board is already shown by ui.refresh() in main loop
        # Just get the player's action

        if player.role == "Spymaster":
            return self._get_clue_from_human(game, player)
        else:  # Operatives
            return self._get_guess_from_human(game, player)

    def _get_clue_from_human(self, game: "CodenamesGame", player: Player):
        """Get clue from human spymaster."""
        from .actions import ClueOutput

        print()  # Blank line for spacing

        # Get clue word
        while True:
            clue = input("→ Enter your one-word clue: ").strip()
            if clue and ' ' not in clue:
                break
            print("  ❌ Clue must be a single word with no spaces!")

        # Get count
        while True:
            try:
                count_str = input("→ Enter count (1-9): ").strip()
                count = int(count_str)
                if 1 <= count <= 9:
                    break
                print("  ❌ Count must be between 1 and 9!")
            except ValueError:
                print("  ❌ Please enter a valid number!")

        # Optional reasoning
        reasoning = input("→ Reasoning (optional): ").strip()

        return ClueOutput(
            clue=clue,
            count=count,
            reasoning=reasoning if reasoning else None
        )

    def _get_guess_from_human(self, game: "CodenamesGame", player: Player):
        """Get guess or pass from human operatives."""
        from .actions import GuessOutput

        print()  # Blank line for spacing
        print(f"Guesses remaining: {game.state.guesses_remaining}")

        # Get action choice
        while True:
            action_choice = input("→ Enter codename to guess, or 'pass': ").strip()

            if action_choice.lower() == "pass":
                reasoning = input("→ Reasoning (optional): ").strip()
                return GuessOutput(
                    action="pass",
                    codename=None,
                    reasoning=reasoning if reasoning else None
                )

            # Check if it's a valid codename
            if game.board.find_by_codename(action_choice):
                reasoning = input("→ Reasoning (optional): ").strip()
                return GuessOutput(
                    action="guess",
                    codename=action_choice,
                    reasoning=reasoning if reasoning else None
                )

            print(f"  ❌ '{action_choice}' is not a valid hidden codename. Try again!")
