# Subtract-a-Square

A mathematical strategy game implemented using the `boardgamepy` framework. This is a variant of combinatorial game theory problems where players can only subtract perfect squares.

**Features:**
- ✅ Perfect square subtraction mechanics
- ✅ Losing position strategy
- ✅ Combinatorial game theory example
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

Subtract-a-Square is a two-player game with the following rules:

1. The game starts with a single pile of N objects (default: 20)
2. Players take turns removing objects from the pile
3. On each turn, a player **must remove a perfect square number** of objects (1, 4, 9, 16, 25, 36, 49, ...)
4. The amount removed cannot exceed the current pile count
5. **The player who removes the last object wins**

## Perfect Squares

Valid moves are perfect square numbers:
- 1 = 1×1
- 4 = 2×2
- 9 = 3×3
- 16 = 4×4
- 25 = 5×5
- 36 = 6×6
- 49 = 7×7
- ... and so on

## Strategy

Subtract-a-Square is a solved game with interesting mathematical properties:

### Losing Positions
Certain pile counts are **losing positions** - if you're left with these, you cannot win with optimal play:
- 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, ...

### Winning Strategy
- Try to leave your opponent with a losing position
- If the current count is a losing position, any move you make gives your opponent a winning position
- Key losing positions to aim for: 2, 3, 5, 6, 7, 8

### Example
Starting with 20 objects:
- Remove 4 → leaves 16 (opponent can remove 16 and win)
- Remove 9 → leaves 11 (losing position for opponent!)
- Remove 16 → leaves 4 (opponent can remove 4 and win)

The optimal move is to remove 9, leaving opponent with 11.

## Running the Game

```bash
# Set your API key
export OPENROUTER_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"

# Run the game
python examples/subtract-a-square/main.py
```

## Customizing Initial Count

Edit `config.py` to change the starting pile size:

```python
self.initial_count = 20  # Default
# Try other values:
# self.initial_count = 15
# self.initial_count = 30
# self.initial_count = 50
```

## Implementation Files

- `board.py` - SubtractASquareBoard managing single pile
- `state.py` - SubtractASquareState tracking current player and winner
- `actions.py` - RemoveAction for removing perfect squares
- `prompts.py` - SubtractASquarePromptBuilder with strategy hints for AI
- `game.py` - SubtractASquareGame tying everything together
- `ui.py` - Terminal UI with pile visualization and valid moves
- `main.py` - Entry point with AI agent setup
- `config.py` - Configuration and API keys

## Example Output

```
============================================================
    SUBTRACT-A-SQUARE
============================================================

Current Pile:

  ●●●●●●●●●●●●●●●●●●●●
  Count: 20

  Valid moves: 1, 4, 9, 16

Recent Moves:

[Player 1]
  Action: Remove 9 objects
  Reasoning: Leave opponent with 11, a losing position

Current Player: Player 2
```

## Mathematical Background

This game is studied in **combinatorial game theory** as an impartial game (both players have the same moves available). It's related to the Sprague-Grundy theorem and has connections to:

- Nim and Nim-like games
- The Beatty sequence
- Discrete mathematics and number theory

The losing positions follow a pattern but require computation to determine for larger numbers.
