# Wythoff's Game

A classic combinatorial game theory problem with a fascinating connection to the golden ratio. Implemented using the `boardgamepy` framework.

**Features:**
- ✅ Golden ratio-based strategy
- ✅ Three move types (A, B, both)
- ✅ P-position detection
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

Wythoff's Game is a two-player game with the following rules:

1. The game starts with two piles of objects (Pile A and Pile B)
2. Players take turns making ONE of these three moves:
   - **Remove any number from Pile A only**
   - **Remove any number from Pile B only**
   - **Remove the SAME number from BOTH piles simultaneously**
3. **The player who removes the last object wins**

## The Golden Ratio Connection

Wythoff's Game has a beautiful mathematical property: the winning and losing positions are determined by the **golden ratio** φ = (1 + √5) / 2 ≈ 1.618.

### P-Positions (Losing Positions)

Certain pile configurations are **P-positions** where the player whose turn it is will lose with optimal play:

- (0, 0) - game over
- (1, 2)
- (3, 5)
- (4, 7)
- (6, 10)
- (8, 13) ← **default starting position**
- (9, 15)
- (11, 18)
- (12, 20)
- ...

These positions follow the pattern:
- a_k = floor(k × φ)
- b_k = floor(k × φ²)

where k = 0, 1, 2, 3, ...

### Winning Strategy

- **If you're in a P-position**: Any move you make gives your opponent a winning position
- **If you're NOT in a P-position**: There exists a move to leave your opponent in a P-position
- The key is to always try to leave your opponent in a P-position

## Move Types

The game supports three types of moves:

1. **pile_a**: Remove objects from Pile A only
   - Example: Piles (10, 15) → Remove 3 from A → (7, 15)

2. **pile_b**: Remove objects from Pile B only
   - Example: Piles (10, 15) → Remove 5 from B → (10, 10)

3. **both**: Remove SAME amount from both piles
   - Example: Piles (10, 15) → Remove 7 from both → (3, 8)

## Running the Game

```bash
# Set your API key
export OPENROUTER_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"

# Run the game
python examples/wythoff/main.py
```

## Customizing Starting Position

Edit `config.py` to change the initial pile sizes:

```python
self.pile_a = 8   # Default
self.pile_b = 13  # Default (8, 13) is a P-position

# Try other configurations:
# self.pile_a = 5
# self.pile_b = 8   # (5, 8) is NOT a P-position

# self.pile_a = 10
# self.pile_b = 16  # (10, 16) is NOT a P-position
```

## Implementation Files

- `board.py` - WythoffBoard with two piles and P-position detection
- `state.py` - WythoffState tracking current player and winner
- `actions.py` - Three action types (RemoveFromA, RemoveFromB, RemoveFromBoth)
- `prompts.py` - WythoffPromptBuilder with golden ratio strategy hints
- `game.py` - WythoffGame tying everything together
- `ui.py` - Terminal UI with color-coded piles and position hints
- `main.py` - Entry point with AI agent setup
- `config.py` - Configuration and API keys

## Example Output

```
============================================================
    WYTHOFF'S GAME
============================================================

Current Board:

  Pile A: ●●●●●●●● (8)
  Pile B: ●●●●●●●●●●●●● (13)

  Total objects: 21
  💡 This is a losing position! Any move gives opponent advantage.

Recent Moves:

[Player 1]
  Action: Remove 5 from Pile A
  Reasoning: Trying to create a favorable position for endgame

Current Player: Player 2
```

## Mathematical Background

Wythoff's Game was named after Dutch mathematician Willem Abraham Wythoff (1907). It's studied in:

- **Combinatorial game theory** - as an impartial game
- **Number theory** - for its connection to Beatty sequences
- **The golden ratio** - P-positions are characterized by φ
- **Complementary sequences** - the a_k and b_k sequences are complementary

The game demonstrates how irrational numbers like φ can appear in discrete, finite games.

## Strategy Tips

1. **Recognize P-positions**: (1,2), (3,5), (4,7), (6,10), (8,13)...
2. **If you're in a P-position**: You're at a disadvantage - any legal move helps opponent
3. **If you're NOT in a P-position**: Calculate a move to reach a P-position
4. **The "both" move is powerful**: It can quickly change the game state
5. **Endgame**: When piles are small, enumerate all possibilities

## Interesting Facts

- The a_k sequence: 0, 1, 3, 4, 6, 8, 9, 11, 12, 14, 16, 17, 19, 21...
- The b_k sequence: 0, 2, 5, 7, 10, 13, 15, 18, 20, 23, 26, 28, 31, 34...
- These two sequences partition the non-negative integers (every number appears exactly once)
- This is related to the Beatty sequence theorem
