"""DixiQuote game configuration."""

from dotenv import load_dotenv
import os


class Config:
    """Configuration for DixiQuote game."""

    def __init__(self):
        # Load .env file
        load_dotenv()

        # API keys
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

        if not self.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is missing in .env file or environment variables."
            )

        # Game settings
        self.num_players = 4  # 3-8 players supported
        self.target_score = 20  # Score to win
        self.max_rounds = 15  # Maximum rounds


config = Config()
