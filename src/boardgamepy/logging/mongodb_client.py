"""MongoDB client manager with connection pooling and error handling."""

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import logging

from .config import LoggingConfig


logger = logging.getLogger(__name__)


class MongoDBClient:
    """
    MongoDB client manager with connection pooling and error handling.

    Handles connection lifecycle, index creation, and strict error handling
    based on configuration.
    """

    def __init__(self, config: LoggingConfig):
        """
        Initialize MongoDB client.

        Args:
            config: LoggingConfig instance with connection settings

        Raises:
            RuntimeError: If ENABLE_LOGGING=true but MongoDB is unavailable
        """
        self.config = config
        self._client: Optional[MongoClient] = None
        self._db = None

        if config.enable_logging:
            self._connect()

    def _connect(self):
        """
        Establish MongoDB connection and verify availability.

        Raises:
            RuntimeError: If connection fails and logging is enabled
        """
        try:
            self._client = MongoClient(
                self.config.mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000
            )

            # Test connection
            self._client.admin.command('ping')

            # Get database
            self._db = self._client[self.config.mongo_db_name]

            # Ensure indexes
            self._ensure_indexes()

            logger.info(f"Connected to MongoDB at {self.config.mongo_uri}")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            if self.config.enable_logging:
                # Strict mode: fail if logging enabled but MongoDB unavailable
                raise RuntimeError(
                    f"ENABLE_LOGGING=true but MongoDB unavailable at {self.config.mongo_uri}. "
                    f"Error: {e}"
                ) from e
            else:
                logger.warning(f"MongoDB unavailable: {e}")
                self._client = None
                self._db = None

    def _ensure_indexes(self):
        """Create indexes for performance."""
        if self._db is None:
            return

        # Games collection indexes
        games = self._db.games
        games.create_index([("game_id", ASCENDING)], unique=True)
        games.create_index([("game_name", ASCENDING)])
        games.create_index([("timestamp_start", ASCENDING)])

        # Turns collection indexes
        turns = self._db.turns
        turns.create_index([("game_id", ASCENDING), ("turn_number", ASCENDING)])
        turns.create_index([("timestamp", ASCENDING)])

        logger.debug("MongoDB indexes ensured")

    @property
    def games(self):
        """
        Get games collection.

        Returns:
            pymongo.collection.Collection

        Raises:
            RuntimeError: If MongoDB is not connected
        """
        if self._db is None:
            raise RuntimeError("MongoDB not connected")
        return self._db.games

    @property
    def turns(self):
        """
        Get turns collection.

        Returns:
            pymongo.collection.Collection

        Raises:
            RuntimeError: If MongoDB is not connected
        """
        if self._db is None:
            raise RuntimeError("MongoDB not connected")
        return self._db.turns

    @property
    def is_connected(self) -> bool:
        """
        Check if MongoDB is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._client is not None and self._db is not None

    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")
