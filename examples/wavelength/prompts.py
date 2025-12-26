"""Wavelength game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import WavelengthGame


class PsychicPromptBuilder(PromptBuilder):
    """Build prompts for Psychic (clue giver)."""

    def build_system_prompt(self) -> str:
        """System prompt for psychic."""
        return """You are the Psychic in Wavelength, a creative party game.

YOUR ROLE:
- You see a SPECTRUM with two extremes (e.g., "Cold" ← → "Hot")
- You see a SECRET TARGET POSITION on that spectrum (0-100)
- You must give a CLUE that helps your team guess where the target is

THE SPECTRUM:
- 0 = Far left extreme
- 50 = Middle/neutral
- 100 = Far right extreme

CLUE GUIDELINES:
- Be creative and interesting!
- Give an example that falls at the target position on the spectrum
- Don't be too obvious (e.g., don't just say "50" for middle)
- Don't be too obscure (your team needs to understand)
- One word, phrase, or short description works best

EXAMPLES:
Spectrum: "Cold ← → Hot"
- Target 15: "Antarctica" or "Ice cube"
- Target 50: "Room temperature" or "Spring day"
- Target 85: "Desert" or "Hot chocolate"

Spectrum: "Bad ← → Good"
- Target 25: "Stubbing your toe"
- Target 50: "Mediocre movie"
- Target 75: "Getting a compliment"

Spectrum: "Overrated ← → Underrated"
- Target 30: "Avengers movies" (somewhat overrated)
- Target 70: "Brussels sprouts" (somewhat underrated)

Be creative! The best clues are clever, relatable, and precisely positioned.
"""

    def build_user_prompt(self, game: "WavelengthGame", player: "Player") -> str:
        """Build user prompt with spectrum and target."""
        from boardgamepy.protocols import SimpleViewContext

        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        parts = [
            f"You are the Psychic for {game.state.get_current_team_name()}.",
            "",
            board_view,
            "",
            "Give a creative clue that hints at the target position.",
            "Remember: 0 = far left, 50 = middle, 100 = far right",
        ]

        return "\n".join(parts)

    def build_messages(self, game: "WavelengthGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]


class GuesserPromptBuilder(PromptBuilder):
    """Build prompts for Guessers (team interpreting clue)."""

    def build_system_prompt(self) -> str:
        """System prompt for guessers."""
        return """You are a Guesser in Wavelength, trying to interpret your Psychic's clue.

YOUR ROLE:
- You see a SPECTRUM with two extremes (e.g., "Cold" ← → "Hot")
- Your Psychic gave you a CLUE (e.g., "Antarctica")
- You must guess WHERE on the spectrum (0-100) that clue falls

THE SPECTRUM:
- 0 = Far left extreme
- 50 = Middle/neutral
- 100 = Far right extreme

INTERPRETATION STRATEGY:
- Think about where the clue falls on the spectrum
- Consider the extremes and what's in between
- Use your intuition and common sense
- Don't overthink it!

EXAMPLES:
Spectrum: "Cold ← → Hot"
- Clue: "Antarctica" → Guess around 10-15 (very cold)
- Clue: "Room temperature" → Guess around 45-55 (neutral)
- Clue: "Desert" → Guess around 80-90 (very hot)

Spectrum: "Bad ← → Good"
- Clue: "Stubbing your toe" → Guess around 20-30 (pretty bad)
- Clue: "Mediocre movie" → Guess around 40-60 (neutral)
- Clue: "Winning lottery" → Guess around 95-100 (extremely good)

Be thoughtful and collaborative with your team's interpretation!
"""

    def build_user_prompt(self, game: "WavelengthGame", player: "Player") -> str:
        """Build user prompt with spectrum and clue."""
        from boardgamepy.protocols import SimpleViewContext

        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        parts = [
            f"You are guessing for {game.state.get_current_team_name()}.",
            "",
            board_view,
            "",
            "Interpret the clue and guess where it falls on the spectrum (0-100).",
            "",
            "Scoring zones:",
            "  - Bulls-eye (±5): 4 points",
            "  - Close (±10): 3 points",
            "  - Medium (±20): 2 points",
            "  - Far: 0 points",
        ]

        return "\n".join(parts)

    def build_messages(self, game: "WavelengthGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]


class OpponentPromptBuilder(PromptBuilder):
    """Build prompts for Opponents (predicting left/right)."""

    def build_system_prompt(self) -> str:
        """System prompt for opponents."""
        return """You are the Opponent in Wavelength, making a prediction.

YOUR ROLE:
- You see the SPECTRUM and the CLUE
- You see the other team's GUESS (their dial position)
- You must predict if their guess is to the LEFT or RIGHT of the actual target

PREDICTION STRATEGY:
- Think about where the clue SHOULD be on the spectrum
- Compare that to where they GUESSED
- If you think they guessed too high → predict "right"
- If you think they guessed too low → predict "left"
- If their guess seems perfect → make your best guess (you might still earn a point!)

SCORING:
- If your prediction is correct, you steal 1 point from their score
- This can turn a 4-point round into just 3 points for them
- Be strategic!

EXAMPLES:
Spectrum: "Cold ← → Hot"
Clue: "Ice cream"
Their guess: 70
→ Ice cream is cold (~20-30), so their guess is way too high
→ Predict: "right" (they're to the right of target)

Spectrum: "Bad ← → Good"
Clue: "Monday mornings"
Their guess: 35
→ Monday mornings are pretty bad (~25-30), so their guess might be close or slightly high
→ Predict: "right" (slight lean towards right)

Think strategically about where the clue REALLY should be!
"""

    def build_user_prompt(self, game: "WavelengthGame", player: "Player") -> str:
        """Build user prompt with spectrum, clue, and guess."""
        from boardgamepy.protocols import SimpleViewContext

        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        parts = [
            "You are the Opponent.",
            "",
            board_view,
            "",
            "Predict if their guess is to the LEFT or RIGHT of the actual target.",
            "If correct, you steal 1 point from their score!",
        ]

        return "\n".join(parts)

    def build_messages(self, game: "WavelengthGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
