"""Main game logger that captures all game actions, states, and LLM interactions."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
import logging

try:  # Optional dependency
    from .mongodb_client import MongoDBClient
except Exception:  # ImportError or missing pymongo
    class MongoDBClient:  # type: ignore
        def __init__(self, *_, **__):
            raise ImportError(
                "pymongo is required for MongoDB logging. Install with pip install pymongo or disable logging."
            )
from .config import LoggingConfig
from .serializers import StateSerializer


logger = logging.getLogger(__name__)


class GameLogger:
    """
    Main game logger that captures all game actions, states, and LLM interactions.

    Coordinates logging of:
    - Game metadata and configuration
    - Turn-by-turn state transitions
    - LLM prompts and responses
    - Final game outcomes
    """

    def __init__(self, config: LoggingConfig):
        """
        Initialize game logger.

        Args:
            config: LoggingConfig instance with settings
        """
        self.config = config
        self.mongodb = MongoDBClient(config) if config.enable_logging else None
        self.game_id: Optional[str] = None
        self.turn_number = 0
        self.start_time: Optional[datetime] = None

        # Log LangSmith tracing status
        if config.langsmith_tracing:
            logger.info(
                f"LangSmith tracing enabled - project: {config.langsmith_project}, "
                f"endpoint: {config.langsmith_endpoint}"
            )

    @property
    def enabled(self) -> bool:
        """
        Check if logging is enabled and MongoDB is connected.

        Returns:
            bool: True if logging should occur
        """
        return (
            self.config.enable_logging
            and self.mongodb is not None
            and self.mongodb.is_connected
        )

    def start_game(self, game: Any, config_params: Dict[str, Any]) -> str:
        """
        Log game start and create game document.

        Args:
            game: Game instance
            config_params: Setup configuration parameters

        Returns:
            game_id: Unique game session ID
        """
        if not self.enabled:
            return ""

        self.game_id = str(uuid.uuid4())
        self.start_time = datetime.now(timezone.utc)
        self.turn_number = 0

        # Serialize players
        players = [
            {"name": p.name, "team": p.team, "role": p.role, "agent_type": p.agent_type}
            for p in game.players
        ]

        # Get game name (use class name if name attribute doesn't exist)
        game_name = getattr(game, "name", game.__class__.__name__)

        # Capture initial board state if available
        initial_board = None
        if hasattr(game, "board"):
            try:
                initial_board = StateSerializer.serialize(game.board)
            except Exception as e:
                logger.warning(f"Could not serialize initial board: {e}")

        # Create game document
        game_doc = {
            "game_id": self.game_id,
            "game_name": game_name,
            "timestamp_start": self.start_time,
            "timestamp_end": None,
            "config": config_params,
            "players": players,
            "initial_board": initial_board,
            "final_state": None,
            "outcome": None,
        }

        try:
            self.mongodb.games.insert_one(game_doc)
            logger.info(f"Game started: {self.game_id} ({game_name})")
        except Exception as e:
            logger.error(f"Failed to log game start: {e}")
            if self.config.enable_logging:
                raise

        return self.game_id

    def log_turn(
        self,
        player: Any,
        state_before: Any,
        state_after: Any,
        board_before: Any = None,
        board_after: Any = None,
        action: Any = None,
        action_params: Dict[str, Any] = None,
        action_valid: bool = True,
        llm_call_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a complete turn with all context.

        Args:
            player: Player who took action
            state_before: Game state before action
            state_after: Game state after action
            board_before: Board object before action (will be serialized)
            board_after: Board object after action (will be serialized)
            action: Action instance
            action_params: Action parameters
            action_valid: Whether action was valid
            llm_call_data: Optional LLM call data (messages, response, metadata)
        """
        if not self.enabled:
            return

        self.turn_number += 1

        # Serialize board objects if provided
        board_before_data = None
        board_after_data = None

        if board_before is not None:
            try:
                # If it's a string (legacy), keep it as is
                if isinstance(board_before, str):
                    board_before_data = board_before
                else:
                    # Serialize the board object to capture all data
                    board_before_data = StateSerializer.serialize(board_before)
            except Exception as e:
                logger.warning(f"Could not serialize board_before: {e}")
                board_before_data = str(board_before)

        if board_after is not None:
            try:
                # If it's a string (legacy), keep it as is
                if isinstance(board_after, str):
                    board_after_data = board_after
                else:
                    # Serialize the board object to capture all data
                    board_after_data = StateSerializer.serialize(board_after)
            except Exception as e:
                logger.warning(f"Could not serialize board_after: {e}")
                board_after_data = str(board_after)

        # Build turn document
        turn_doc = {
            "game_id": self.game_id,
            "turn_number": self.turn_number,
            "timestamp": datetime.now(timezone.utc),
            "player": {"name": player.name, "team": player.team, "role": player.role},
            "state_before": StateSerializer.serialize(state_before),
            "state_after": StateSerializer.serialize(state_after),
            "board_before": board_before_data,
            "board_after": board_after_data,
            "action": {
                "type": action.name if action else None,
                "display_name": action.display_name if action else None,
                "params": action_params or {},
                "valid": action_valid,
            },
            "llm_call": llm_call_data,
        }

        try:
            self.mongodb.turns.insert_one(turn_doc)
            logger.debug(f"Turn {self.turn_number} logged for game {self.game_id}")
        except Exception as e:
            logger.error(f"Failed to log turn: {e}")
            if self.config.enable_logging:
                raise

    def end_game(self, game: Any):
        """
        Log game end and update game document with outcome.

        Args:
            game: Game instance at end of game
        """
        if not self.enabled or not self.game_id:
            return

        end_time = datetime.now(timezone.utc)
        duration = (
            (end_time - self.start_time).total_seconds() if self.start_time else 0
        )

        # Update game document
        update_doc = {
            "$set": {
                "timestamp_end": end_time,
                "final_state": StateSerializer.serialize(game.state),
                "outcome": {
                    "winner": str(game.state.get_winner())
                    if game.state.get_winner() is not None
                    else None,
                    "total_turns": self.turn_number,
                    "duration_seconds": duration,
                },
            }
        }

        try:
            self.mongodb.games.update_one({"game_id": self.game_id}, update_doc)
            logger.info(
                f"Game ended: {self.game_id} (winner: {game.state.get_winner()})"
            )
        except Exception as e:
            logger.error(f"Failed to log game end: {e}")
            if self.config.enable_logging:
                raise
