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
from .mongodb_client import MongoDBClient
from .query import GameDataQuery
from .serializers import StateSerializer

__all__ = [
    "LoggingConfig",
    "GameLogger",
    "LoggedGame",
    "LoggedLLMAgent",
    "MongoDBClient",
    "GameDataQuery",
    "StateSerializer",
]
