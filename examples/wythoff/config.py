"""Configuration for Wythoff's Game."""

from dotenv import load_dotenv
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Game configuration."""

    def __init__(self):
        # Load .env file
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

        # Default pile sizes (8, 13) is a P-position (losing position)
        # Try (5, 8) or (10, 16) for non-P-positions
        self.pile_a = 8
        self.pile_b = 13

        if not self.OPENAI_API_KEY and not self.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY or OPENROUTER_API_KEY is missing in .env file or environment variables."
            )


config = Config()
