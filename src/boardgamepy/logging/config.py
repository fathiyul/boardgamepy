"""Configuration system for boardgamepy logging."""

from dataclasses import dataclass
from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Optional


@dataclass
class LoggingConfig:
    """Centralized logging configuration with hierarchical .env loading."""

    # MongoDB settings
    mongo_uri: str
    mongo_db_name: str
    enable_logging: bool
    log_level: str

    # Model names
    openai_model: str
    openrouter_model: str

    # LangSmith settings
    langsmith_tracing: bool
    langsmith_project: str
    langsmith_endpoint: str

    @classmethod
    def load(cls, game_dir: Optional[Path] = None) -> "LoggingConfig":
        """
        Load configuration with hierarchical .env loading.

        Priority: game-specific .env > root .env > defaults

        Args:
            game_dir: Optional path to game directory with local .env

        Returns:
            LoggingConfig instance with merged configuration
        """
        # Load root .env first
        root_env = Path(__file__).parent.parent.parent.parent / ".env"
        if root_env.exists():
            load_dotenv(root_env)

        # Load game-specific .env if provided (overrides root)
        if game_dir:
            game_env = game_dir / ".env"
            if game_env.exists():
                load_dotenv(game_env, override=True)

        # Parse configuration
        enable_logging = os.getenv("ENABLE_LOGGING", "false").lower() == "true"
        langsmith_tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

        # Set LangSmith environment variables for LangChain to pick up
        # LangChain automatically detects these, but we ensure they're set
        if langsmith_tracing:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            if os.getenv("LANGCHAIN_API_KEY"):
                os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
            if os.getenv("LANGCHAIN_PROJECT"):
                os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")
            if os.getenv("LANGCHAIN_ENDPOINT"):
                os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")

        return cls(
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            mongo_db_name=os.getenv("MONGO_DB_NAME", "boardgamepy_logs"),
            enable_logging=enable_logging,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            openrouter_model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp"),
            langsmith_tracing=langsmith_tracing,
            langsmith_project=os.getenv("LANGCHAIN_PROJECT", "boardgamepy"),
            langsmith_endpoint=os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),
        )

    def get_model_name(self, provider: str) -> str:
        """
        Get model name for specific provider.

        Args:
            provider: "openai" or "openrouter"

        Returns:
            Model name string
        """
        if provider == "openai":
            return self.openai_model
        elif provider == "openrouter":
            return self.openrouter_model
        return "unknown"
