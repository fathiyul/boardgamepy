"""Configuration system for boardgamepy logging."""

from dataclasses import dataclass, field
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

    # Model configuration
    default_model: str

    # LangSmith settings
    langsmith_tracing: bool
    langsmith_project: str
    langsmith_endpoint: str

    # Fields with defaults must come after non-default fields
    player_models: dict[int, str] = field(default_factory=dict)

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

        # Get default model (support legacy OPENROUTER_MODEL for backwards compat)
        default_model = os.getenv(
            "DEFAULT_MODEL",
            os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        )

        # Get per-player models (MODEL_PLAYER_1, MODEL_PLAYER_2, etc.)
        player_models = {}
        for i in range(1, 20):  # Support up to 20 players
            model = os.getenv(f"MODEL_PLAYER_{i}")
            if model:
                player_models[i - 1] = model  # Convert to 0-indexed

        return cls(
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            mongo_db_name=os.getenv("MONGO_DB_NAME", "boardgamepy_logs"),
            enable_logging=enable_logging,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            default_model=default_model,
            player_models=player_models,
            langsmith_tracing=langsmith_tracing,
            langsmith_project=os.getenv("LANGCHAIN_PROJECT", "boardgamepy"),
            langsmith_endpoint=os.getenv(
                "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
            ),
        )

    def get_model_for_player(self, player_idx: int) -> str:
        """
        Get model name for a specific player.

        Args:
            player_idx: 0-indexed player index

        Returns:
            Model name string (per-player override or default)
        """
        return self.player_models.get(player_idx, self.default_model)

    def get_short_model_name(self, model: str) -> str:
        """
        Get shortened model name for display (removes provider prefix).

        Args:
            model: Full model name like "google/gemini-2.5-flash"

        Returns:
            Short name like "gemini-2.5-flash"
        """
        if "/" in model:
            return model.split("/", 1)[1]
        return model

    # Legacy property for backwards compatibility
    @property
    def openrouter_model(self) -> str:
        """Legacy property, returns default_model."""
        return self.default_model
