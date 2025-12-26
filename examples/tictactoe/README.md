# Tic-Tac-Toe - BoardGamePy Example

The **simplest** example of using BoardGamePy! A classic 3x3 Tic-Tac-Toe game with AI players.

## Features

- ✅ Simple rules everyone knows
- ✅ No hidden information (unlike Codenames)
- ✅ AI vs AI gameplay
- ✅ Quick games (~9 moves max)
- ✅ Clean terminal UI with colors
- ✅ MongoDB & LangSmith logging support

## Logging Support

This example includes full MongoDB logging to capture game states and LLM interactions. Optionally enable LangSmith for LLM observability.

**Enable logging** (edit `.env` in project root):
```env
ENABLE_LOGGING=true
LANGCHAIN_TRACING_V2=true  # Optional: LangSmith tracing
```

See [LOGGING_GUIDE.md](../../LOGGING_GUIDE.md) for complete documentation.

## Quick Start

### Run with your API key

```bash
cd examples/tictactoe

# Option 1: Use OpenRouter
export OPENROUTER_API_KEY="your_key_here"
python main.py

# Option 2: Use OpenAI
export OPENAI_API_KEY="your_key_here"
python main.py
```

### What You'll See

```
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                   TIC-TAC-TOE                                      ║
╚════════════════════════════════════════════════════════════════════════════════════╝

Current Player: X

   |   |
-----------
   |   |
-----------
   |   |

X → Position 5
Reasoning: Taking center position gives maximum strategic advantage

   |   |
-----------
   | X |
-----------
   |   |

O → Position 1
Reasoning: Take corner to set up multiple winning paths
...
```

## How It Works

This example demonstrates **all core BoardGamePy features** in the simplest way:

### 1. Board with State
```python
class TicTacToeBoard(Board):
    def __init__(self):
        self.grid = {i: " " for i in range(1, 10)}  # Positions 1-9
```

### 2. Game State
```python
class TicTacToeState(GameState):
    current_player: Literal["X", "O"] = "X"
    winner: Literal["X", "O", "Draw"] | None = None
```

### 3. Actions
```python
class MoveAction(Action):
    def validate(self, game, player, position: int) -> bool:
        return game.board.is_position_empty(position)

    def apply(self, game, player, position: int):
        game.board.place_mark(position, game.state.current_player)
        # Check winner, switch player
```

### 4. AI Prompts
```python
class TicTacToePromptBuilder(PromptBuilder):
    def build_user_prompt(self, game, player) -> str:
        return f"""
        Current board: {game.board.get_view()}
        Available positions: {game.board.get_empty_positions()}
        Choose best move...
        """
```

### 5. Game Loop
```python
game = TicTacToeGame()
game.setup()

while not game.state.is_terminal():
    player = game.get_current_player()
    move = player.agent.get_action(game, player)
    action.apply(game, player, position=move.position)
```

## Comparison to Codenames

| Feature | Tic-Tac-Toe | Codenames |
|---------|-------------|-----------|
| **Complexity** | ⭐ Simple | ⭐⭐⭐ Complex |
| **Hidden Info** | ❌ None | ✅ Role-based |
| **Game Length** | ~9 moves | ~30+ turns |
| **State Size** | 9 positions | 25 cards + history |
| **Actions** | 1 type (Move) | 3 types (Clue/Guess/Pass) |
| **Players** | 2 | 4 (2 teams, 2 roles) |

Tic-Tac-Toe is **perfect for learning** the framework basics!

## Code Structure

- `board.py` - 3x3 grid with win detection
- `state.py` - Current player and game status
- `actions.py` - MoveAction for placing X or O
- `prompts.py` - AI prompt builder
- `game.py` - TicTacToeGame class
- `ui.py` - Simple terminal rendering
- `main.py` - Entry point

Total: ~250 lines of code for a complete AI-playable game! 🎮

## Extending This Example

Want to modify it?

- **Add human player**: Replace `agent_type="ai"` with `agent_type="human"` and implement input
- **Different AI difficulty**: Use different models or adjust prompts
- **4x4 board**: Change grid size and win condition
- **Tournament mode**: Play multiple games and track scores

## Next Steps

After understanding Tic-Tac-Toe, try:
1. **Codenames** (`examples/codenames/`) - More complex with hidden information
2. **Your own game** - Use this as a template!

## License

MIT - Same as BoardGamePy framework
