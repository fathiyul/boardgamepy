"""MongoDB client manager with connection pooling and error handling."""

from pymongo import MongoClient, ASCENDING
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    InvalidURI,
    ConfigurationError,
)
from typing import Optional
import logging
import urllib.parse

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
                serverSelectionTimeoutMS=10000,  # 10 second timeout (DNS can be slow)
                connectTimeoutMS=10000,
            )

            # Test connection
            self._client.admin.command("ping")

            # Get database
            self._db = self._client[self.config.mongo_db_name]

            # Ensure indexes
            self._ensure_indexes()

            logger.info(f"Connected to MongoDB at {self.config.mongo_uri}")

        except InvalidURI as e:
            # Special handling for invalid URI errors (often due to unescaped passwords)
            if "password must be escaped" in str(e).lower():
                raise RuntimeError(
                    f"MongoDB password contains special characters that need URL encoding.\n"
                    f"\n"
                    f"Your password likely contains characters like: # ! % @ $ & + , / : ; = ? @ [ ]\n"
                    f"\n"
                    f"Fix this by encoding your password:\n"
                    f"  python3 -c \"import urllib.parse; print(urllib.parse.quote_plus('your-password'))\"\n"
                    f"\n"
                    f"Then use the encoded password in your MONGO_URI in .env\n"
                    f"Original error: {e}"
                ) from e
            else:
                raise RuntimeError(f"Invalid MongoDB URI: {e}") from e

        except ConfigurationError as e:
            # DNS resolution errors for mongodb+srv URIs
            if "DNS operation timed out" in str(
                e
            ) or "resolution lifetime expired" in str(e):
                raise RuntimeError(
                    f"DNS timeout when connecting to MongoDB Atlas.\n"
                    f"\n"
                    f"This usually means:\n"
                    f"  1. Network/firewall is blocking DNS queries\n"
                    f"  2. DNS resolver issues on your system\n"
                    f"  3. VPN interference\n"
                    f"\n"
                    f"Try these fixes:\n"
                    f"  1. Test network: ping 8.8.8.8\n"
                    f"  2. Use direct connection instead of mongodb+srv://\n"
                    f"     Get it from Atlas: Cluster → Connect → Drivers → Connection String Only\n"
                    f"  3. Try different DNS: Add 'nameserver 8.8.8.8' to /etc/resolv.conf\n"
                    f"  4. Disable VPN temporarily\n"
                    f"\n"
                    f"Original error: {e}"
                ) from e
            else:
                raise RuntimeError(f"MongoDB configuration error: {e}") from e

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
