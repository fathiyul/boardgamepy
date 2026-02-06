"""
Logging system for BoardGamePy.

Captures game actions, states, LLM interactions for fine-tuning datasets.

Usage:
    from boardgamepy.logging import LoggedGame, LoggedLLMAgent, LoggingConfig

    # Wrap your game
    config = LoggingConfig.load(Path(__file__).parent)
    game = LoggedGame(YourGame(), Path(__file__).parent)

    # Wrap your LLM agents
    base_agent = LLMAgent(llm, prompt_builder, output_schema)
    player.agent = LoggedLLMAgent(base_agent, model_name)

    # Run game - logging happens automatically
    winner = game.run()
"""

from .config import LoggingConfig
from .game_logger import GameLogger
from .logged_game import LoggedGame
from .logged_llm_agent import LoggedLLMAgent
from .query import GameDataQuery
from .serializers import StateSerializer

# Optional dependency: pymongo
try:  # pragma: no cover - optional import
    from .mongodb_client import MongoDBClient  # type: ignore
except Exception:  # ImportError or missing pymongo
    class MongoDBClient:  # type: ignore
        def __init__(self, *_, **__):
            raise ImportError(
                "pymongo is required for MongoDB logging. Install with pip install pymongo or disable logging."
            )

__all__ = [
    "LoggingConfig",
    "GameLogger",
    "LoggedGame",
    "LoggedLLMAgent",
    "MongoDBClient",
    "GameDataQuery",
    "StateSerializer",
]
