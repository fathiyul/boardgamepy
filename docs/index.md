# Welcome to BoardGamePy

**BoardGamePy** is a lean Python framework for building board games that can be played by AI agents (using LLMs) or human players.

It provides the core abstractions needed to manage game state, turn mechanics, information hiding (fog of war), and AI integration, without imposing a specific UI or game logic.

## Key Features

- **Role-based information hiding**: Built-in support for games where different players see different information.
- **AI integration**: First-class support for LLM-powered agents with automatic prompt generation.
- **Per-player model configuration**: Assign different LLM models to different players.
- **Action history tracking**: Automatic logging of all actions for replay and debugging.
- **Human/AI hybrid play**: Mix human and AI players in the same game.
- **Error resilience**: Auto-elimination for agents that repeatedly fail to produce valid actions.

## Quick Start

Install the package:

```bash
pip install boardgamepy
```

Check out the [Getting Started](getting-started.md) guide to build your first game.

## Architecture

The framework is built around a few core classes:

- **`Game`**: The central coordinator.
- **`GameState`**: A dataclass holding the mutable state of the game.
- **`Board`**: Renders the game state for players (handling information hiding).
- **`Action`**: Defines what players can do.
- **`Player`**: Represents a participant (Human or AI).

## Next Steps

- Follow the [Getting Started](getting-started.md) tutorial.
- Explore the [GitHub Repository](https://github.com/fathiyul/boardgamepy).
