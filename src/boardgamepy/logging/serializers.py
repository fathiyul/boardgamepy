"""Serialization utilities for polymorphic game states."""

from typing import Any, Dict
from pydantic import BaseModel
from dataclasses import is_dataclass, asdict


class StateSerializer:
    """
    Serializes polymorphic game states to MongoDB-compatible dictionaries.

    Handles different types of objects:
    - Pydantic BaseModel instances
    - Python dataclasses
    - Plain dictionaries (converts all keys to strings for MongoDB)
    - Primitive types (str, int, float, bool)
    - Lists and nested structures

    Note: MongoDB requires all dictionary keys to be strings, so integer
    keys (like {0: value, 1: value}) are automatically converted to strings.
    """

    @staticmethod
    def serialize(obj: Any) -> Any:
        """
        Serialize object to JSON-compatible format.

        Args:
            obj: Object to serialize (state, board, any Python object)

        Returns:
            JSON-compatible dict, list, or primitive
        """
        if obj is None:
            return None

        # Pydantic BaseModel - convert to dict and recursively serialize
        if isinstance(obj, BaseModel):
            return StateSerializer.serialize(obj.model_dump())

        # Dataclass - convert to dict and recursively serialize
        if is_dataclass(obj):
            return StateSerializer.serialize(asdict(obj))

        # Already a dict - recursively serialize values
        # Convert keys to strings for MongoDB compatibility
        if isinstance(obj, dict):
            return {str(k): StateSerializer.serialize(v) for k, v in obj.items()}

        # List or tuple - recursively serialize items
        if isinstance(obj, (list, tuple)):
            return [StateSerializer.serialize(item) for item in obj]

        # Set - convert to list
        if isinstance(obj, set):
            return list(obj)

        # Primitive types
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Fallback: try to convert to dict via __dict__ and recursively serialize
        try:
            return StateSerializer.serialize(vars(obj))
        except TypeError:
            # If all else fails, convert to string representation
            return {"_repr": str(obj), "_type": type(obj).__name__}
