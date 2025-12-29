"""
BoardGamePy - A framework for building AI-playable board games.

This package provides abstractions for creating board games with:
- Role-based information hiding
- AI integration via LLMs
- Action history tracking
- Human/AI hybrid play
"""

__version__ = "0.3.2"

# Core abstractions
from boardgamepy.core import (
    Player,
    HumanAgent,
    AIAgent,
    GameState,
    Action,
    GameHistory,
    Round,
    Game,
    GameRunner,
)

# Components
from boardgamepy.components import Board, Piece

# AI integration
from boardgamepy.ai import PromptBuilder, LLMAgent

# UI
from boardgamepy.ui import UIRenderer

# Protocols
from boardgamepy.protocols import ViewContext, PlayerAgent, SimpleViewContext

__all__ = [
    # Core
    "Player",
    "HumanAgent",
    "AIAgent",
    "GameState",
    "Action",
    "GameHistory",
    "Round",
    "Game",
    "GameRunner",
    # Components
    "Board",
    "Piece",
    # AI
    "PromptBuilder",
    "LLMAgent",
    # UI
    "UIRenderer",
    # Protocols
    "ViewContext",
    "PlayerAgent",
    "SimpleViewContext",
]
