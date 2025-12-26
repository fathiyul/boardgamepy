# BoardGamePy Examples

This directory contains 12 complete game implementations demonstrating various features of the BoardGamePy framework. All examples include full MongoDB and LangSmith logging support.

## Quick Start

Each game can be run independently:

```bash
cd examples/<game-name>
python main.py
```

## Configuration

All games use hierarchical configuration from `.env` files:

1. **Root `.env`** (project root) - Default settings for all games
2. **Game `.env`** (optional) - Override settings per game

See `.env.example` for all available configuration options.

## Available Games

### 1. TicTacToe
**Complexity:** Beginner
**Players:** 2
**Path:** `examples/tictactoe/`

Classic 3x3 grid game. Perfect starting point for understanding the framework.

**Features:**
- Simple action validation
- Clear win conditions
- Minimal state management

**Run:**
```bash
cd examples/tictactoe
python main.py
```

---

### 2. Codenames
**Complexity:** Advanced
**Players:** 4 (2 teams)
**Path:** `examples/codenames/`

Team-based word association game with role-based information hiding.

**Features:**
- Role-based views (Spymaster vs Operatives)
- Multiple action types (give clues, make guesses, pass)
- Complex team coordination
- Information hiding demonstration

**Run:**
```bash
cd examples/codenames
python main.py
```

---

### 3. Love Letter
**Complexity:** Intermediate
**Players:** 2-4
**Path:** `examples/loveletter/`

Card game with bluffing, deduction, and simultaneous card play.

**Features:**
- Hidden information (hand cards)
- Simultaneous decision-making
- Character abilities
- Player elimination mechanics

**Run:**
```bash
cd examples/loveletter
python main.py
```

---

### 4. Sushi Go
**Complexity:** Intermediate
**Players:** 2-5
**Path:** `examples/sushigo/`

Card drafting game where players simultaneously choose cards and pass hands.

**Features:**
- Simultaneous card selection
- Card drafting mechanics
- Hand rotation system
- Scoring combinations

**Run:**
```bash
cd examples/sushigo
python main.py
```

---

### 5. Wavelength
**Complexity:** Intermediate
**Players:** 4+ (2 teams)
**Path:** `examples/wavelength/`

Cooperative guessing game where teams try to locate a target on a spectrum.

**Features:**
- Team-based gameplay
- Spectrum-based guessing
- Clue-giving mechanics
- Score-based proximity

**Run:**
```bash
cd examples/wavelength
python main.py
```

---

### 6. Splendor
**Complexity:** Advanced
**Players:** 2-4
**Path:** `examples/splendor/`

Engine-building card game with resource management.

**Features:**
- Resource collection and spending
- Card purchasing and reserving
- Noble tile acquisition
- Engine-building strategy

**Run:**
```bash
cd examples/splendor
python main.py
```

---

### 7. Coup
**Complexity:** Intermediate
**Players:** 2-6
**Path:** `examples/coup/`

Bluffing and deduction game with character abilities.

**Features:**
- Hidden character cards
- Bluffing mechanics
- Challenge/block system
- Player elimination

**Run:**
```bash
cd examples/coup
python main.py
```

---

### 8. Incan Gold
**Complexity:** Intermediate
**Players:** 3-8
**Path:** `examples/incangold/`

Push-your-luck exploration game with simultaneous decisions.

**Features:**
- Push-your-luck mechanics
- Simultaneous decision-making
- Risk vs reward choices
- Treasure collection

**Run:**
```bash
cd examples/incangold
python main.py
```

---

### 9. Subtract-a-Square
**Complexity:** Beginner
**Players:** 2
**Path:** `examples/subtract-a-square/`

Mathematical game where players subtract perfect squares from a counter.

**Features:**
- Simple mathematical validation
- Perfect square calculation
- Turn-based strategy

**Run:**
```bash
cd examples/subtract-a-square
python main.py
```

---

### 10. Nim
**Complexity:** Beginner
**Players:** 2
**Path:** `examples/nim/`

Classic pile subtraction game with configurable heaps.

**Features:**
- Multi-heap management
- Configurable starting positions
- Classic game theory example

**Run:**
```bash
cd examples/nim
python main.py
```

---

### 11. Wythoff
**Complexity:** Beginner
**Players:** 2
**Path:** `examples/wythoff/`

Two-pile Nim variant where players can take from one or both piles.

**Features:**
- Dual pile mechanics
- Flexible take options
- Strategy variation on Nim

**Run:**
```bash
cd examples/wythoff
python main.py
```

---

## Framework Features Demonstrated

### Information Hiding
- **Codenames** - Role-based views (Spymaster vs Operatives)
- **Love Letter** - Hidden hand cards
- **Coup** - Hidden character cards
- **Sushi Go** - Hidden hands during drafting

### Simultaneous Decisions
- **Sushi Go** - All players pick cards simultaneously
- **Incan Gold** - Continue/return decisions collected together
- **Love Letter** - Card plays can be simultaneous

### Team Play
- **Codenames** - Two teams with different roles
- **Wavelength** - Cooperative team guessing

### Multiple Action Types
- **Codenames** - Clue giving, guessing, passing
- **Splendor** - Take gems, reserve cards, buy cards
- **Coup** - Income, foreign aid, coup, character actions

### Complex State Management
- **Splendor** - Resources, cards, nobles, discounts
- **Sushi Go** - Hand rotation, card scoring, rounds
- **Codenames** - Grid state, team scores, clue tracking

## Logging Support

All games include:
- **MongoDB logging** - Full game state capture
- **LLM interaction logging** - Prompts, responses, reasoning
- **LangSmith integration** - Optional LLM observability

See [LOGGING_GUIDE.md](../LOGGING_GUIDE.md) for configuration and usage.

## Development Tips

### Adding AI Players

```python
from boardgamepy.logging import LoggingConfig, LoggedLLMAgent
from pathlib import Path

# Load config
config = LoggingConfig.load(Path(__file__).parent)

# Create LLM agent with logging
base_agent = LLMAgent(llm, prompt_builder, output_schema)
player.agent = LoggedLLMAgent(base_agent, model_name=config.openai_model)
```

### Enabling Logging

1. Copy `.env.example` to `.env` in project root
2. Set `ENABLE_LOGGING=true`
3. Start MongoDB: `docker run -d -p 27017:27017 --name mongodb mongo:latest`
4. Run any game - logging happens automatically!

### Viewing Logs

```bash
# List recent games
python view_logs.py list

# View specific game
python view_logs.py details 1

# Export for fine-tuning
python view_logs.py export Codenames 1000
```

## Game Complexity Guide

**Beginner** (Start here):
- TicTacToe
- Nim
- Wythoff
- Subtract-a-Square

**Intermediate** (After understanding basics):
- Love Letter
- Sushi Go
- Wavelength
- Coup
- Incan Gold

**Advanced** (Complex mechanics):
- Codenames
- Splendor

## Contributing

To add a new game example:

1. Create directory: `examples/your-game/`
2. Implement core classes: `game.py`, `state.py`, `board.py`, `actions.py`
3. Add prompts: `prompts.py` (for AI players)
4. Create UI: `ui.py` (optional but recommended)
5. Add main: `main.py` with logging integration
6. Update this README with your game!

## License

All examples are MIT licensed.
