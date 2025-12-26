# Nim Game

A classic mathematical strategy game implemented using the `boardgamepy` framework.

**Features:**
- ✅ Classic Nim strategy game
- ✅ Configurable pile sizes
- ✅ XOR-based optimal strategy
- ✅ MongoDB & LangSmith logging support

## Logging Support

This example includes full MongoDB logging to capture game states and LLM interactions. Optionally enable LangSmith for LLM observability.

**Enable logging** (edit `.env` in project root):
```env
ENABLE_LOGGING=true
LANGCHAIN_TRACING_V2=true  # Optional: LangSmith tracing
```

See [LOGGING_GUIDE.md](../../LOGGING_GUIDE.md) for complete documentation.

## Game Rules

Nim is a two-player game with the following rules:

1. The game starts with multiple piles of objects (stones, sticks, etc.)
2. Players take turns removing objects from exactly one pile
3. On each turn, a player must remove at least 1 object, and can remove as many as they want from that pile
4. **The player who removes the last object wins**

## Default Setup

The classic Nim configuration uses 3 piles: `[3, 5, 7]`

```
Pile 1: ●●● (3)
Pile 2: ●●●●● (5)
Pile 3: ●●●●●●● (7)
```

## Strategy

Nim is a solved game with optimal strategy based on the XOR (nim-sum) of pile sizes:

- A position is a "losing position" if XOR of all pile sizes equals 0
- The winning strategy is to always leave your opponent in a losing position
- If all piles have only 1 object, leave an odd number of piles

## Running the Game

```bash
# Set your API key
export OPENROUTER_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"

# Run the game
python examples/nim/main.py
```

## Customizing Pile Sizes

Edit `config.py` to change the default piles:

```python
default_piles=[3, 5, 7]  # Classic Nim
# or try other configurations:
# default_piles=[1, 3, 5, 7]  # 4 piles
# default_piles=[5, 5, 5]     # Symmetric
```

## Implementation Files

- `board.py` - NimBoard managing piles and object removal
- `state.py` - NimState tracking current player and game status
- `actions.py` - RemoveAction for removing objects from piles
- `prompts.py` - NimPromptBuilder for AI strategy hints
- `game.py` - NimGame tying everything together
- `ui.py` - Terminal UI with colored pile visualization
- `main.py` - Entry point with AI agent setup
- `config.py` - Configuration and API keys

## Example Output

```
==================================================
    NIM GAME
==================================================

Current Board:

  Pile 1: ●●● (3)
  Pile 2: ●●●●● (5)
  Pile 3: ●●●●●●● (7)

Total objects remaining: 15

[Player 1]
  Action: Remove 2 from Pile 3
  Reasoning: Leave opponent in losing position (XOR = 0)
```
