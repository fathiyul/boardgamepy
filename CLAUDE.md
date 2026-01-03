# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BoardGamePy is a Python framework for building AI-playable board games with LLM integration. It provides core abstractions for turn-based games that can be played by AI agents (using LLMs via OpenRouter), human players, or mixed human/AI games.

**Key Design Philosophy:**
- Declarative game definitions (similar to Django models or Pydantic)
- Role-based information hiding built into the core
- AI-first with automatic prompt generation and structured output
- Lean abstractions without over-engineering

## Development Commands

### Running Games

```bash
# Run any example game
cd examples/<game-name>
python main.py

# With CLI arguments (for games that support them)
python main.py -n 4              # Number of players
python main.py -t 7              # Target score/tokens to win
python main.py -n 3 -t 5         # Both

# Common games to test with:
cd examples/rps && python main.py           # Simplest game
cd examples/codenames && python main.py     # Most complex (role-based, team)
cd examples/loveletter && python main.py    # Medium complexity
```

### Building & Installation

```bash
# Install in editable mode for development
pip install -e .

# With AI support (required for LLM agents)
pip install -e ".[ai]"

# With all dependencies including examples
pip install -e ".[ai,examples]"

# Build wheel for distribution
python -m build
```

### Documentation

```bash
# Serve docs locally with live reload
mkdocs serve
# View at http://127.0.0.1:8000

# Build static docs
mkdocs build
```

### Logging & Database

```bash
# View logged games (MongoDB must be running)
python view_logs.py list                    # List recent games
python view_logs.py list Codenames 5        # Last 5 Codenames games
python view_logs.py details <game-id>       # Detailed game info
python view_logs.py stats                   # Overall statistics
python view_logs.py stats Codenames         # Game-specific stats
python view_logs.py export TicTacToe 1000   # Export for fine-tuning

# Start MongoDB (required for logging)
docker run -d -p 27017:27017 --name mongodb mongo:latest
docker stop mongodb
docker start mongodb
```

## Architecture

### Core Abstractions (src/boardgamepy/core/)

The framework is built on 6 core abstractions that work together:

1. **Game** (`game.py`) - Central orchestrator class
   - Coordinates all components (state, board, players, actions)
   - Implements `setup()` to initialize game
   - Provides `get_current_player()` and `next_turn()` hooks
   - Manages game loop via optional `GameRunner`

2. **GameState** (`state.py`) - Pydantic model for game state
   - Always includes: `is_over: bool`, `winner: Any`
   - Add game-specific fields (scores, rounds, current_player, etc.)
   - Automatically serialized for logging

3. **Action** (`action.py`) - Player actions with 3-strike validation
   - Generic over game type: `Action[TGame]`
   - Each action has: `name`, `display_name`, `OutputSchema` (Pydantic)
   - Implements: `validate()`, `apply()`, `to_history_record()`
   - Invalid actions tracked; 3 consecutive = auto-elimination

4. **Board** (`components/board.py`) - Game board with role-based views
   - **Critical feature:** `get_view(context: ViewContext)` enforces information hiding
   - Return different strings based on `context.player.role`
   - Used to show/hide information in AI prompts

5. **Player** (`player.py`) - Player with agent, team, role
   - Has `agent: PlayerAgent` (LLMAgent, HumanAgent, or custom)
   - `team`: for team-based games (e.g., "Red", "Blue")
   - `role`: for role-based games (e.g., "Spymaster", "Operative")

6. **GameHistory** (`history.py`) - Automatic action logging
   - Tracks all actions for replay and AI context
   - Used in prompts to show game progression
   - Serialized to MongoDB when logging enabled

### AI Integration (src/boardgamepy/ai/)

- **PromptBuilder** (`prompt.py`) - Constructs LLM prompts
  - Abstract class with `build_prompt(game, player) -> str`
  - Different builders for different roles (SpymasterPromptBuilder, OperativesPromptBuilder)
  - Accesses `board.get_view(context)` for role-specific information

- **LLMAgent** (`agent.py`) - AI decision-maker
  - Takes: `llm` (ChatOpenAI), `prompt_builder`, `output_schema` (Pydantic)
  - Returns structured output via LangChain's `with_structured_output()`
  - Wrapped by `LoggedLLMAgent` when logging enabled

- **OutputSchema** - Pydantic models defining LLM response structure
  - **Important constraint:** Avoid `ge`, `le`, `minimum`, `maximum` on int fields
  - Some providers (Anthropic) don't support these constraints
  - Use description text instead: `Field(..., description="Position (0-100)")`

### GameRunner Pattern (src/boardgamepy/core/runner.py)

The `GameRunner` eliminates main.py boilerplate:

**For simple games (single action type):**
```python
GameRunner.main(
    game_class=MyGame,
    prompt_builder_class=MyPromptBuilder,
    output_schema=MoveAction.OutputSchema,
    game_dir=Path(__file__).parent,
    default_num_players=2,
)(). # Invoke immediately
```

**For complex games (multiple action types, custom turn logic):**
```python
class CustomRunner(GameRunner):
    def run_turn(self, game, player, game_logger):
        # Custom logic for role-based actions, etc.
        pass
```

See `examples/codenames/main.py` for complex runner example.

### Logging System (src/boardgamepy/logging/)

Comprehensive MongoDB-based logging that captures:
- Every game action and state transition
- Full LLM prompts and responses
- AI reasoning for each decision
- Game metadata and outcomes

**Key components:**
- `LoggingConfig` - Reads env vars, manages per-player models
- `GameLogger` - Logs turns, manages game sessions
- `LoggedGame` - Decorator wrapping Game with logging
- `LoggedLLMAgent` - Captures LLM calls for logging
- `mongodb_client.py` - MongoDB connection and operations

**Configuration via .env:**
```env
ENABLE_LOGGING=true
MONGO_URI=mongodb://localhost:27017
OPENROUTER_API_KEY=...
DEFAULT_MODEL=google/gemini-2.5-flash
MODEL_PLAYER_1=anthropic/claude-sonnet-4.5  # Override per player
```

## Creating New Games

### Typical File Structure (see examples/)

```
examples/<game-name>/
├── main.py              # Entry point with GameRunner
├── game.py              # Game subclass
├── state.py             # GameState subclass
├── board.py             # Board subclass with get_view()
├── actions.py           # Action subclasses
├── prompts.py           # PromptBuilder subclasses (one per role)
├── config.py            # Game-specific config
├── ui.py                # (optional) Terminal rendering
├── human_agent.py       # (optional) Human interaction
└── .env                 # Per-game LLM config
```

### Implementation Checklist

1. **Define GameState** - Extend with game-specific fields
2. **Define Board** - Implement `get_view(context)` for role-based information hiding
3. **Define Actions** - Create Action subclasses with OutputSchema, validate(), apply()
4. **Define PromptBuilders** - One per role, constructs prompts from game state
5. **Define Game** - Implement `setup()`, `get_current_player()`, `next_turn()`
6. **Create main.py** - Use GameRunner or custom runner
7. **Add .env** - Configure models per-player

### Role-Based Information Hiding Pattern

**Critical pattern for games with hidden information:**

```python
class MyBoard(Board):
    def get_view(self, context: ViewContext) -> str:
        if context.player.role == "Spymaster":
            return self._render_with_hidden_info()
        else:
            return self._render_public_info()
```

The view is automatically passed to the correct player's PromptBuilder.

## Important Patterns & Conventions

### Per-Player Model Configuration

Games support different LLM models per player via env vars:
```env
DEFAULT_MODEL=google/gemini-2.5-flash
MODEL_PLAYER_1=anthropic/claude-sonnet-4.5
MODEL_PLAYER_2=openai/gpt-4o-mini
```

The framework uses OpenRouter API which provides access to multiple LLM providers.

### 3-Strike Auto-Elimination

Actions track `consecutive_invalid_actions` on GameState. After 3 consecutive invalid actions, a player is automatically eliminated. Reset to 0 on successful action.

### LangSmith Integration

When `LANGCHAIN_TRACING_V2=true`, all LLM calls are automatically traced to LangSmith dashboard with no code changes needed.

### Human/AI Hybrid Play

Games can mix human and AI players:
- Set `player.agent = HumanAgent()` for human players
- See `examples/loveletter/main_human.py` for reference implementation

## Code Location Quick Reference

- Core game abstractions: `src/boardgamepy/core/`
- AI/LLM integration: `src/boardgamepy/ai/`
- Logging system: `src/boardgamepy/logging/`
- Board components: `src/boardgamepy/components/`
- Example games: `examples/`
- Framework documentation: `docs/`

## Testing & Validation

The project doesn't currently have a formal test suite. When making changes:

1. Run multiple example games to verify no regressions
2. Test with different models via MODEL_PLAYER_N env vars
3. Verify logging works if touching logging code
4. Check that board views correctly hide/show information

## Dependencies

- **Core:** Python >=3.10, pydantic >=2.0, python-dotenv
- **AI:** langchain-core, langchain-openai (for OpenRouter access)
- **Logging:** pymongo
- **Docs:** mkdocs, mkdocs-material, mkdocstrings[python]

Not published to PyPI - distributed via GitHub releases as wheel files.
