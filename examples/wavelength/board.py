"""Wavelength board implementation."""

import random
from typing import TYPE_CHECKING
from boardgamepy import Board
from spectrums import Spectrum, get_random_spectrum

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class WavelengthBoard(Board):
    """
    Wavelength game board managing spectrum and target.

    The board represents:
    - A spectrum (0 = left extreme, 100 = right extreme)
    - A hidden target position (center of target range)
    - A target range width (default: 10 units, so ±5 from center)
    - Team's dial position (their guess)
    - Opponent's prediction (left/right)
    """

    def __init__(self):
        """Initialize board."""
        self.current_spectrum: Spectrum | None = None
        self.target_center: int = 50  # 0-100
        self.target_range: int = 10  # Width of bulls-eye zone
        self.dial_position: int | None = None  # Team's guess
        self.opponent_prediction: str | None = None  # "left" or "right"
        self.psychic_clue: str | None = None

    def setup_round(self) -> None:
        """Setup a new round with random spectrum and target."""
        self.current_spectrum = get_random_spectrum()
        self.target_center = random.randint(10, 90)  # Avoid extremes
        self.target_range = 10
        self.dial_position = None
        self.opponent_prediction = None
        self.psychic_clue = None

    def set_dial_position(self, position: int) -> None:
        """Set the team's dial guess."""
        self.dial_position = max(0, min(100, position))

    def set_opponent_prediction(self, prediction: str) -> None:
        """Set opponent's left/right prediction."""
        if prediction.lower() in ["left", "right"]:
            self.opponent_prediction = prediction.lower()

    def calculate_score(self) -> tuple[int, bool]:
        """
        Calculate score for the round.

        Returns:
            (base_points, opponent_correct)
            base_points: 0-4 based on accuracy
            opponent_correct: True if opponent's prediction was right
        """
        if self.dial_position is None:
            return 0, False

        # Calculate distance from target center
        distance = abs(self.dial_position - self.target_center)

        # Scoring zones (similar to actual game)
        if distance <= self.target_range // 2:  # Bulls-eye (±5)
            base_points = 4
        elif distance <= self.target_range:  # Close (±10)
            base_points = 3
        elif distance <= self.target_range * 2:  # Medium (±20)
            base_points = 2
        else:  # Far
            base_points = 0

        # Check opponent prediction
        # Opponent predicts: is the TARGET to the LEFT or RIGHT of the GUESS?
        opponent_correct = False
        if self.opponent_prediction and self.dial_position != self.target_center:
            # Target is LEFT of guess means target < dial_position
            if self.target_center < self.dial_position and self.opponent_prediction == "left":
                opponent_correct = True
            # Target is RIGHT of guess means target > dial_position
            elif self.target_center > self.dial_position and self.opponent_prediction == "right":
                opponent_correct = True

        return base_points, opponent_correct

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view with role-based information hiding.

        Psychic sees: spectrum + target position
        Guessing team sees: spectrum + psychic's clue
        Opponent sees: spectrum + psychic's clue
        After reveal: everyone sees everything
        """
        from boardgamepy.core.player import Player

        player: Player = context.player

        lines = ["=== WAVELENGTH ===", ""]

        # Current spectrum
        if self.current_spectrum:
            lines.append(f"Spectrum: {self.current_spectrum}")
            lines.append("")

        # Psychic's clue (if given)
        if self.psychic_clue:
            lines.append(f"Psychic's Clue: \"{self.psychic_clue}\"")
            lines.append("")

        # Target position (only for psychic before guessing)
        if "Psychic" in player.role and self.dial_position is None:
            lines.append(f"🎯 TARGET POSITION: {self.target_center}")
            lines.append(
                f"   Target Range: {self.target_center - self.target_range//2} - {self.target_center + self.target_range//2}"
            )
            lines.append("")

        # Dial position (if set)
        if self.dial_position is not None:
            lines.append(f"Team's Guess: {self.dial_position}")
            lines.append("")

        # Opponent prediction (if set)
        if self.opponent_prediction:
            lines.append(f"Opponent Predicts: Guess is to the {self.opponent_prediction.upper()}")
            lines.append("")

        # Spectrum visualization (after reveal)
        if self.dial_position is not None and self.opponent_prediction is not None:
            lines.append(self._visualize_spectrum())

        return "\n".join(lines)

    def _visualize_spectrum(self) -> str:
        """Create ASCII visualization of spectrum with target and guess."""
        if not self.current_spectrum or self.dial_position is None:
            return ""

        width = 50
        target_pos = int((self.target_center / 100) * width)
        guess_pos = int((self.dial_position / 100) * width)

        # Create visualization line
        viz = ["-"] * width
        viz[target_pos] = "🎯"
        if guess_pos != target_pos:
            viz[guess_pos] = "📍"

        viz_str = "".join(viz)

        return f"""
Spectrum Visualization:
{self.current_spectrum.left:^25} {self.current_spectrum.right:^25}
0{viz_str}100
        🎯 = Target   📍 = Your Guess
"""

    def get_prompt_view(self, context: "ViewContext") -> str:
        """Get simplified view for AI prompts."""
        return self.get_view(context)
