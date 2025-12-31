from dotenv import load_dotenv
import os


class Config:
    def __init__(self):
        # Load .env file
        load_dotenv()
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

        if not self.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is missing in .env file or environment variables."
            )


config = Config()
