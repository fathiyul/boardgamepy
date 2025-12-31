# BoardGamePy Logging System

Complete MongoDB-based logging system for capturing game actions, states, and LLM interactions for fine-tuning datasets.

## Features

✅ **Zero Core Changes** - Game, Action, LLMAgent classes unchanged
✅ **Opt-In** - Games work without logging by default
✅ **Complete Capture** - Every action, state transition, LLM prompt/response
✅ **Polymorphic Storage** - Handles any game type automatically
✅ **Hierarchical Config** - Root .env + per-game overrides
✅ **Fine-Tuning Ready** - Direct export of LLM interactions
✅ **LangSmith Integration** - Optional LLM observability with automatic tracing
✅ **CLI Tool** - Easy querying and analysis with `view_logs.py`

## Quick Start

### 1. Configure Environment

Copy `.env.example` to `.env` and configure:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=boardgamepy_logs

# Logging Configuration
ENABLE_LOGGING=false
LOG_LEVEL=INFO

# OpenRouter API Key (required)
OPENROUTER_API_KEY=your-openrouter-api-key-here

# LLM Model Configuration
# DEFAULT_MODEL is used for all players unless overridden per-player
DEFAULT_MODEL=google/gemini-2.5-flash

# Per-player model overrides (optional)
# If not set, uses DEFAULT_MODEL
# MODEL_PLAYER_1=google/gemini-2.5-flash
# MODEL_PLAYER_2=anthropic/claude-sonnet-4.5
# MODEL_PLAYER_3=openai/gpt-4o-mini
# MODEL_PLAYER_4=x-ai/grok-4.1-fast

# LangSmith Tracing
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=boardgamepy
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### 2. Start MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB locally
```

### 3. Run a Game

```bash
cd examples/tictactoe
python3 main.py
```

Game data will be automatically logged to MongoDB!

## Integration Pattern

Minimal changes needed to add logging to any game:

```python
import copy
from pathlib import Path
from boardgamepy.logging import LoggedLLMAgent, LoggingConfig, GameLogger

# 1. Load configuration
logging_config = LoggingConfig.load(Path(__file__).parent)

# 2. Create game logger
game_logger = GameLogger(logging_config)

# 3. Log game start
if game_logger.enabled:
    game_logger.start_game(game, {"num_players": 2})

# 4. Wrap LLM agents with model name
base_agent = LLMAgent(llm, prompt_builder, output_schema)
player.agent = LoggedLLMAgent(base_agent, model_name=logging_config.openai_model)

# 5. In game loop - capture state before/after each action
state_before = copy.deepcopy(game.state)
# ... player makes move ...
state_after = copy.deepcopy(game.state)

# 6. Log each turn
if game_logger.enabled:
    llm_call_data = getattr(player.agent, '_last_llm_call', None)
    if llm_call_data:
        player.agent._last_llm_call = None

    game_logger.log_turn(
        player=player,
        state_before=state_before,
        state_after=state_after,
        board_before="",
        board_after="",
        action=action,
        action_params={"position": 5},
        action_valid=True,
        llm_call_data=llm_call_data
    )

# 7. Log game end
if game_logger.enabled:
    game_logger.end_game(game)
```

All 12 included game examples have been updated with this pattern!

## MongoDB Schema

### Games Collection

```javascript
{
  game_id: "uuid-string",
  game_name: "TicTacToe",
  timestamp_start: ISODate("2025-01-15T10:30:00Z"),
  timestamp_end: ISODate("2025-01-15T10:32:15Z"),
  config: { initial_count: 20 },
  players: [
    { name: "X", team: "X", role: null, agent_type: "ai" },
    { name: "O", team: "O", role: null, agent_type: "ai" }
  ],
  final_state: { current_player: "O", is_over: true, winner: "X" },
  outcome: {
    winner: "X",
    total_turns: 5,
    duration_seconds: 12.5
  }
}
```

### Turns Collection

```javascript
{
  game_id: "uuid-string",
  turn_number: 1,
  timestamp: ISODate("2025-01-15T10:30:02Z"),
  player: { name: "X", team: "X", role: null },

  state_before: { current_player: "X", is_over: false, winner: null },
  state_after: { current_player: "O", is_over: false, winner: null },

  board_before: "1. _ | 2. _ | 3. _\n...",
  board_after: "1. X | 2. _ | 3. _\n...",

  action: {
    type: "move",
    display_name: "Place Mark",
    params: { position: 1 },
    valid: true,
    history_record: { type: "move", player: "X", position: 1 }
  },

  llm_call: {
    messages: [
      { role: "system", content: "You are playing Tic-Tac-Toe..." },
      { role: "user", content: "Current board:\n..." }
    ],
    response: {
      position: 1,
      reasoning: "I'll take the center for strategic advantage..."
    },
    model: "gpt-4o-mini",
    timestamp: ISODate("2025-01-15T10:30:02Z"),
    metadata: {
      latency_ms: 850.5,
      usage: null
    }
  }
}
```

## Configuration Hierarchy

### Root .env (Default)
`/home/fathiyul/01-project/boardgame/.env`
- Used by all games as default
- Contains MongoDB settings, model names, API keys

### Game-Specific .env (Override)
`/home/fathiyul/01-project/boardgame/examples/tictactoe/.env`
- Optional per-game overrides
- Example: Use gpt-4o for complex games, gpt-4o-mini for simple ones

```env
# Override model for this specific game
OPENAI_MODEL=gpt-4o
```

## Viewing Logged Games

### CLI Tool (`view_logs.py`)

Easy-to-use command-line interface for querying logged games:

```bash
# List recent games (shows numbered index)
python view_logs.py list
python view_logs.py list Codenames 5    # Last 5 Codenames games

# View game details (use index from list OR game_id)
python view_logs.py details 1           # Latest game by index
python view_logs.py details abc-123-def # Specific game by ID

# Show statistics
python view_logs.py stats
python view_logs.py stats Codenames     # Game-specific stats

# Export for fine-tuning
python view_logs.py export Codenames 1000
```

**Output includes:**
- Game metadata and configuration
- All turns with actions and LLM reasoning
- Final outcome and duration
- Easy index-based access (no need to copy UUIDs!)

### Python API

```python
from boardgamepy.logging.query import GameDataQuery

query = GameDataQuery()

# Get recent games
recent = query.get_recent_games(game_name="TicTacToe", limit=10)

# Get specific game
game = query.get_game("game-uuid")
turns = query.get_turns("game-uuid")

# Export for fine-tuning
training_data = query.export_for_finetuning(
    game_name="TicTacToe",
    limit=1000
)
# Returns: [{ messages: [...], response: {...}, metadata: {...} }, ...]

# Get statistics
stats = query.get_game_stats("TicTacToe")
# Returns: { total_games: 50, avg_turns: 5.2, avg_duration: 12.5, ... }
```

## Error Handling

### Strict Mode (ENABLE_LOGGING=true)
- MongoDB connection failure → **RuntimeError** (game stops)
- Document insert failure → **RuntimeError** (game stops)
- Ensures data integrity for production logging

### Disabled Mode (ENABLE_LOGGING=false)
- All logging operations are no-ops
- Game runs normally without MongoDB
- Perfect for development/testing

## LangSmith Integration

BoardGamePy automatically integrates with LangSmith for LLM observability when enabled.

### Setup

1. Sign up at https://smith.langchain.com/
2. Get your API key
3. Enable in `.env`:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=boardgamepy
```

### Features

When enabled, **all LLM calls are automatically traced** to LangSmith:
- View full prompts and responses in the dashboard
- Monitor token usage and costs
- Track latency and performance
- Debug prompt issues
- Compare different models

**No code changes needed** - LangChain detects the environment variables and automatically instruments all `.invoke()` calls!

### Dual Logging

You can use both MongoDB and LangSmith simultaneously:
- **MongoDB**: Complete game state, actions, and LLM interactions
- **LangSmith**: LLM-focused observability with nice UI

Both are optional and independent - enable either or both as needed.

## Example: Enable Logging

```bash
# Edit root .env
nano .env
# Set: ENABLE_LOGGING=true

# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Run game
cd examples/tictactoe
python3 main.py
```

## Example: Query MongoDB

```bash
# Connect to MongoDB
mongosh

# Switch to database
use boardgamepy_logs

# View games
db.games.find().pretty()

# View turns for specific game
db.turns.find({ game_id: "your-game-uuid" }).sort({ turn_number: 1 })

# Count total games
db.games.countDocuments()

# Find winning games
db.games.find({ "outcome.winner": { $ne: null } })
```

## File Structure

```
boardgame/
├── .env                          # Root configuration
├── src/boardgamepy/
│   └── logging/                  # Logging module
│       ├── __init__.py           # Public API
│       ├── config.py             # LoggingConfig
│       ├── mongodb_client.py     # MongoDB connection
│       ├── game_logger.py        # Core logger
│       ├── logged_game.py        # Game wrapper
│       ├── logged_llm_agent.py   # LLM agent wrapper
│       ├── serializers.py        # State serialization
│       └── query.py              # Query utilities
└── examples/
    ├── tictactoe/
    │   ├── .env                  # Optional game overrides
    │   └── main.py               # Updated with logging
    └── subtract-a-square/
        └── main.py               # Updated with logging
```

## Updated Examples

All 12 game examples now have full logging support:

✅ **TicTacToe** - Classic game
✅ **Codenames** - Team word-guessing game
✅ **Love Letter** - Card game with simultaneous decisions
✅ **Sushi Go** - Card drafting game
✅ **Wavelength** - Team cooperative guessing game
✅ **Splendor** - Engine-building card game
✅ **Coup** - Bluffing and deduction game
✅ **Incan Gold** - Push-your-luck exploration game
✅ **Subtract-a-Square** - Mathematical game
✅ **Nim** - Classic subtraction game
✅ **Wythoff** - Two-pile Nim variant
✅ **More examples coming soon!**

See `examples/` for complete implementations.

## Benefits

1. **Complete Game Replay** - Every state transition captured
2. **LLM Training Data** - Full prompts + responses for fine-tuning
3. **Performance Analysis** - Track game duration, turn counts
4. **Model Comparison** - Compare different models across games
5. **Bug Debugging** - Full state history for reproducing issues

## Next Steps

1. Start MongoDB
2. Enable logging in .env
3. Run games
4. Query data for analysis
5. Export for fine-tuning

Happy logging! 🎮📊
