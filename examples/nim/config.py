"""Configuration for Nim game."""

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
        self.default_piles = [3, 5, 7]  # Classic Nim

        if not self.OPENAI_API_KEY or not self.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY or OPENROUTER_API_KEY is missing in .env file or environment variables."
            )


config = Config()
