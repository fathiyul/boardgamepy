"""Configuration for Incan Gold game."""

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

        # Game settings
        self.num_players = 4  # 3-8 players, default 4

        if not self.OPENAI_API_KEY and not self.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY or OPENROUTER_API_KEY is missing in .env file or environment variables."
            )


config = Config()
