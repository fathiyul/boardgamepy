"""Wavelength spectrum cards."""

from dataclasses import dataclass
import random


@dataclass
class Spectrum:
    """A spectrum with two extremes."""

    left: str  # Left extreme (0)
    right: str  # Right extreme (100)

    def __str__(self) -> str:
        return f"{self.left} ← → {self.right}"


# Collection of spectrum cards
SPECTRUM_CARDS = [
    # Temperature & Physical
    Spectrum("Cold", "Hot"),
    Spectrum("Soft", "Hard"),
    Spectrum("Light", "Heavy"),
    Spectrum("Slow", "Fast"),
    Spectrum("Quiet", "Loud"),
    Spectrum("Weak", "Strong"),
    Spectrum("Small", "Large"),
    Spectrum("Short", "Tall"),
    # Quality & Opinion
    Spectrum("Bad", "Good"),
    Spectrum("Boring", "Exciting"),
    Spectrum("Useless", "Useful"),
    Spectrum("Overrated", "Underrated"),
    Spectrum("Worst", "Best"),
    Spectrum("Hate It", "Love It"),
    Spectrum("Unpopular", "Popular"),
    # Morality & Ethics
    Spectrum("Evil", "Good"),
    Spectrum("Selfish", "Selfless"),
    Spectrum("Illegal", "Legal"),
    Spectrum("Unethical", "Ethical"),
    # Time
    Spectrum("Old", "New"),
    Spectrum("Past", "Future"),
    Spectrum("Ancient", "Modern"),
    Spectrum("Temporary", "Permanent"),
    # Complexity
    Spectrum("Simple", "Complex"),
    Spectrum("Easy", "Difficult"),
    Spectrum("Shallow", "Deep"),
    Spectrum("Casual", "Serious"),
    # Cost & Value
    Spectrum("Cheap", "Expensive"),
    Spectrum("Worthless", "Valuable"),
    Spectrum("Free", "Costly"),
    # Social
    Spectrum("Introverted", "Extroverted"),
    Spectrum("Formal", "Casual"),
    Spectrum("Private", "Public"),
    Spectrum("Alone", "Together"),
    # Nature
    Spectrum("Natural", "Artificial"),
    Spectrum("Organic", "Synthetic"),
    Spectrum("Wild", "Domesticated"),
    # Abstract
    Spectrum("Chaos", "Order"),
    Spectrum("Random", "Planned"),
    Spectrum("Flexible", "Rigid"),
    Spectrum("Abstract", "Concrete"),
    # Emotion
    Spectrum("Sad", "Happy"),
    Spectrum("Calm", "Angry"),
    Spectrum("Fearful", "Brave"),
    Spectrum("Anxious", "Confident"),
    # Aesthetics
    Spectrum("Ugly", "Beautiful"),
    Spectrum("Plain", "Fancy"),
    Spectrum("Messy", "Neat"),
    Spectrum("Dull", "Colorful"),
    # Knowledge
    Spectrum("Ignorant", "Knowledgeable"),
    Spectrum("Dumb", "Smart"),
    Spectrum("Naive", "Wise"),
    # Food & Taste
    Spectrum("Bland", "Flavorful"),
    Spectrum("Bitter", "Sweet"),
    Spectrum("Mild", "Spicy"),
    Spectrum("Healthy", "Unhealthy"),
]


def get_random_spectrum() -> Spectrum:
    """Get a random spectrum card."""
    return random.choice(SPECTRUM_CARDS)


def get_spectrum_description(spectrum: Spectrum, position: int) -> str:
    """
    Get a description of where a position falls on the spectrum.

    Args:
        spectrum: The spectrum
        position: Position from 0-100

    Returns:
        Human-readable description
    """
    if position < 20:
        return f"Very {spectrum.left.lower()}"
    elif position < 40:
        return f"Moderately {spectrum.left.lower()}"
    elif position < 60:
        return "Neutral/Middle"
    elif position < 80:
        return f"Moderately {spectrum.right.lower()}"
    else:
        return f"Very {spectrum.right.lower()}"
