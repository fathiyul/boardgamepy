"""Game piece abstractions."""

from abc import ABC
from dataclasses import dataclass
from typing import Any


@dataclass
class Piece(ABC):
    """
    Base class for game pieces.

    Represents any game element that has identity and state
    (e.g., cards, tokens, chess pieces, tiles).

    Subclasses should add game-specific fields.

    Attributes:
        id: Unique identifier for this piece
        state: Current state of the piece (game-specific)
    """

    id: Any
    state: Any = None
