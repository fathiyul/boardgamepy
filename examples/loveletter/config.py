"""Configuration for Love Letter game."""

from dotenv import load_dotenv
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Game configuration."""

    def __init__(self):
        # Load .env file
        load_dotenv()
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

        # Game settings
        self.num_players = 2  # 2-4 players

        if not self.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is missing in .env file or environment variables."
            )


config = Config()
