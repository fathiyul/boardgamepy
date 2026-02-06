"""Utilities for querying logged game data."""

from typing import List, Dict, Any, Optional
from datetime import datetime

try:  # Optional dependency
    from .mongodb_client import MongoDBClient
except Exception:  # ImportError or missing pymongo
    class MongoDBClient:  # type: ignore
        def __init__(self, *_, **__):
            raise ImportError(
                "pymongo is required for MongoDB query helpers. Install with pip install pymongo or disable logging."
            )
from .config import LoggingConfig


class GameDataQuery:
    """Query interface for logged game data."""

    def __init__(self, config: Optional[LoggingConfig] = None):
        """
        Initialize query interface.

        Args:
            config: Optional LoggingConfig (if None, loads default)
        """
        if config is None:
            config = LoggingConfig.load()
        self.mongodb = MongoDBClient(config)

    def get_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Get game metadata by ID.

        Args:
            game_id: Unique game session ID

        Returns:
            Game document dict or None if not found
        """
        return self.mongodb.games.find_one({"game_id": game_id})

    def get_turns(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Get all turns for a game, ordered by turn number.

        Args:
            game_id: Unique game session ID

        Returns:
            List of turn documents
        """
        return list(
            self.mongodb.turns
            .find({"game_id": game_id})
            .sort("turn_number", 1)
        )

    def get_recent_games(
        self,
        game_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent games, optionally filtered by game name.

        Args:
            game_name: Optional game name filter
            limit: Maximum number of games to return

        Returns:
            List of game documents
        """
        query = {}
        if game_name:
            query["game_name"] = game_name

        return list(
            self.mongodb.games
            .find(query)
            .sort("timestamp_start", -1)
            .limit(limit)
        )

    def export_for_finetuning(
        self,
        game_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Export LLM interactions in format suitable for fine-tuning.

        Args:
            game_name: Optional filter by game name
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Optional limit on number of turns

        Returns:
            List of dicts with format:
            {
              "messages": [...],
              "response": {...},
              "metadata": {...}
            }
        """
        # Build query
        query = {}

        if game_name:
            # First get game IDs matching game_name
            game_ids = [
                g["game_id"]
                for g in self.mongodb.games.find({"game_name": game_name}, {"game_id": 1})
            ]
            query["game_id"] = {"$in": game_ids}

        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["timestamp"] = date_query

        # Only get turns with LLM calls
        query["llm_call"] = {"$ne": None}

        # Execute query
        cursor = self.mongodb.turns.find(query, {"llm_call": 1, "_id": 0})

        if limit:
            cursor = cursor.limit(limit)

        # Extract LLM calls
        return [turn["llm_call"] for turn in cursor]

    def get_game_stats(self, game_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregate statistics for games.

        Args:
            game_name: Optional filter by game name

        Returns:
            Dict with stats: total_games, avg_turns, avg_duration, etc.
        """
        match_query = {}
        if game_name:
            match_query["game_name"] = game_name

        pipeline = [
            {"$match": match_query},
            {"$match": {"outcome": {"$ne": None}}},  # Only completed games
            {
                "$group": {
                    "_id": None,
                    "total_games": {"$sum": 1},
                    "avg_turns": {"$avg": "$outcome.total_turns"},
                    "avg_duration": {"$avg": "$outcome.duration_seconds"},
                    "max_turns": {"$max": "$outcome.total_turns"},
                    "min_turns": {"$min": "$outcome.total_turns"}
                }
            }
        ]

        result = list(self.mongodb.games.aggregate(pipeline))
        if result:
            return result[0]
        else:
            return {
                "total_games": 0,
                "avg_turns": 0,
                "avg_duration": 0,
                "max_turns": 0,
                "min_turns": 0
            }
