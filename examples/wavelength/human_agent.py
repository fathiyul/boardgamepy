"""Human agent implementations for Wavelength."""

from typing import TYPE_CHECKING
from actions import GiveClueOutput, GuessPositionOutput, PredictDirectionOutput

if TYPE_CHECKING:
    from game import WavelengthGame
    from boardgamepy.core.player import Player


class WavelengthPsychicHumanAgent:
    """Human agent for Psychic role - sees target, gives clue."""

    def get_action(self, game: "WavelengthGame", player: "Player") -> GiveClueOutput:
        """Get clue from human psychic."""
        print()
        print("=" * 50)
        print("YOU ARE THE PSYCHIC")
        print("=" * 50)

        # Show the spectrum
        spectrum = game.board.current_spectrum
        print(f"\nSpectrum: {spectrum.left} <-----> {spectrum.right}")
        print(f"  0 = {spectrum.left}")
        print(f"  100 = {spectrum.right}")

        # Show the target (only psychic sees this!)
        target = game.board.target_center
        target_min = target - game.board.target_range // 2
        target_max = target + game.board.target_range // 2
        print(f"\nTARGET POSITION: {target}")
        print(f"  Bulls-eye zone: {target_min} - {target_max}")
        print(f"  (This is hidden from your teammates!)")

        # Get clue
        print("\nGive a clue that hints at this position on the spectrum.")
        print("Your teammates will use this to guess the target number.")
        print()

        while True:
            clue = input("Your clue: ").strip()
            if clue:
                break
            print("  Please enter a clue")

        # Optional reasoning
        reasoning = input("Reasoning (optional, press Enter to skip): ").strip()

        return GiveClueOutput(
            clue=clue,
            reasoning=reasoning if reasoning else None,
        )


class WavelengthGuesserHumanAgent:
    """Human agent for Guesser role - interprets clue, guesses position."""

    def get_action(self, game: "WavelengthGame", player: "Player") -> GuessPositionOutput:
        """Get position guess from human guesser."""
        print()
        print("=" * 50)
        print("YOU ARE A GUESSER")
        print("=" * 50)

        # Show the spectrum
        spectrum = game.board.current_spectrum
        print(f"\nSpectrum: {spectrum.left} <-----> {spectrum.right}")
        print(f"  0 = {spectrum.left}")
        print(f"  100 = {spectrum.right}")

        # Show the clue
        print(f"\nPsychic's Clue: \"{game.board.psychic_clue}\"")
        print("\nBased on this clue, guess where the target is on the spectrum.")
        print("Enter a number from 0-100")
        print()

        while True:
            try:
                choice = input("Your guess (0-100): ").strip()
                position = int(choice)
                if 0 <= position <= 100:
                    break
                print("  Please enter a number between 0 and 100")
            except ValueError:
                print("  Please enter a valid number")

        # Optional reasoning
        reasoning = input("Reasoning (optional, press Enter to skip): ").strip()

        return GuessPositionOutput(
            position=position,
            reasoning=reasoning if reasoning else None,
        )


class WavelengthOpponentHumanAgent:
    """Human agent for Opponent role - predicts direction."""

    def get_action(self, game: "WavelengthGame", player: "Player") -> PredictDirectionOutput:
        """Get direction prediction from human opponent."""
        print()
        print("=" * 50)
        print("YOU ARE THE OPPONENT")
        print("=" * 50)

        # Show the spectrum
        spectrum = game.board.current_spectrum
        print(f"\nSpectrum: {spectrum.left} <-----> {spectrum.right}")
        print(f"  0 = {spectrum.left}")
        print(f"  100 = {spectrum.right}")

        # Show the clue and guess
        print(f"\nPsychic's Clue: \"{game.board.psychic_clue}\"")
        print(f"Team's Guess: {game.board.dial_position}")

        print("\nPredict: Is the actual target to the LEFT or RIGHT of their guess?")
        print("  If you're correct, they lose 1 point!")
        print()

        while True:
            choice = input("Your prediction (left/right): ").strip().lower()
            if choice in ["left", "l"]:
                prediction = "left"
                break
            elif choice in ["right", "r"]:
                prediction = "right"
                break
            print("  Please enter 'left' or 'right'")

        # Optional reasoning
        reasoning = input("Reasoning (optional, press Enter to skip): ").strip()

        return PredictDirectionOutput(
            prediction=prediction,
            reasoning=reasoning if reasoning else None,
        )
