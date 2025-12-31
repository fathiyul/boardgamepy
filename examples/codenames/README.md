# Codenames - BoardGamePy Example

This is a complete Codenames implementation using the BoardGamePy framework, demonstrating:

- Role-based information hiding (Spymaster vs Operatives views)
- Multiple action types with validation
- AI prompt generation for different roles
- LLM agent configuration
- Game history tracking
- MongoDB & LangSmith logging support

## Logging Support

This example includes full MongoDB logging to capture game states and LLM interactions. Optionally enable LangSmith for LLM observability.

**Enable logging** (edit `.env` in project root):
```env
ENABLE_LOGGING=true
LANGCHAIN_TRACING_V2=true  # Optional: LangSmith tracing
```

See [LOGGING_GUIDE.md](../../LOGGING_GUIDE.md) for complete documentation.

## Quick Start

### 1. Set up API keys

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

You need:
- `OPENROUTER_API_KEY` - Your OpenRouter API key

### 2. Run the game

**Option A: Play as a human (Interactive with Rich UI)**

```bash
cd examples/codenames
python main_human.py
```

Features the same beautiful terminal UI as the AI version! You'll be prompted to choose which roles to play as human vs AI:
- Red Spymaster
- Red Operatives
- Blue Spymaster
- Blue Operatives

Mix and match! For example:
- Play as Red Spymaster + Operatives vs AI Blue team
- Play all 4 roles yourself for a full manual game
- Play as one Spymaster and watch AI Operatives follow your clues

**Option B: Watch AI vs AI (Original)**

```bash
cd examples/codenames
python main.py
```

This runs a fully automated AI vs AI game with rich terminal UI.

**Option C: Using the helper script**

```bash
cd examples/codenames
./run.sh
```

## What to Expect

The game will:
1. Create a random 5x5 board with codenames
2. Start with Red team
3. Run AI vs AI gameplay
4. Show each turn with:
   - Current player (team + role)
   - Action taken (clue or guess)
   - AI reasoning
   - Result
5. Display the winner at the end

Example output:
```
=== Codenames - BoardGamePy Framework Demo ===

Board created with 25 cards
Starting team: Red
Red: 9 agents
Blue: 8 agents

--- Turn 1: Red Spymaster ---
Valid actions: ['clue']
Clue: Animal (3)
Reasoning: Connects DOG, CAT, BIRD - all are animals
State: Red 9 | Blue 8

--- Turn 2: Red Operatives ---
Valid actions: ['guess', 'pass']
Guess: DOG
Reasoning: Most obvious animal on the board
Result: Red
State: Red 8 | Blue 8
...
```

## Code Structure

- `game.py` - Main `CodenamesGame` class
- `board.py` - Board with role-based views
- `state.py` - Game state tracking
- `actions.py` - ClueAction, GuessAction, PassAction
- `prompts.py` - AI prompt builders for each role
- `data.py` - Codename word list loader
- `config.py` - Configuration and API key loading
- `main.py` - Entry point and game loop

## How It Uses BoardGamePy

This example demonstrates the framework's key features:

### 1. Declarative Game Definition

```python
class CodenamesGame(Game):
    name = "Codenames"
    min_players = 4
    max_players = 4
    actions = [ClueAction, GuessAction, PassAction]
```

### 2. Role-Based Information Hiding

```python
class CodenamesBoard(Board):
    def get_view(self, context: ViewContext) -> str:
        if context.player.role == "Spymaster":
            return self._spymaster_view()  # Shows card types
        return self._operatives_view()     # Hides card types
```

### 3. Actions with Validation

```python
class ClueAction(Action):
    def validate(self, game, player, clue: str, count: int) -> bool:
        # Check if clue is legal

    def apply(self, game, player, clue: str, count: int):
        # Update game state and history
```

### 4. AI Integration

```python
class SpymasterPromptBuilder(PromptBuilder):
    def build_user_prompt(self, game, player) -> str:
        # Automatically includes board view, history, state
```

## Extending This Example

To add new features:

1. **New action types** - Create new `Action` subclasses
2. **Different AI models** - Change the LLM configuration in `setup_ai_agents()`
3. **Human players** - See `human_agent.py` and `main_human.py` for implementation example
4. **Custom UI** - Extend `UIRenderer` to add terminal colors or web interface

## Human Player Implementation

The `main_human.py` demonstrates how to implement human players:

1. **Custom Agent Class** (`human_agent.py`):
```python
class CodenamesHumanAgent:
    def get_action(self, game, player):
        # Show board, get console input, return action
```

2. **Player Configuration**:
```python
# In your game setup
player.agent = CodenamesHumanAgent()
player.agent_type = "human"
```

The human agent shows the appropriate board view, prompts for input, validates it, and returns the action in the same format as AI agents. This allows seamless mixing of human and AI players!

## Troubleshooting

**Module not found errors:**
- Make sure you're running from the correct directory
- The `main.py` adds parent directories to Python path automatically

**API key errors:**
- Check that `.env` file exists and has valid keys
- Verify keys have proper permissions for the models being used

**Game crashes or infinite loops:**
- Check the turn limit (currently 100 turns max)
- Review AI reasoning in output to see if agents are stuck

## License

MIT - Same as BoardGamePy framework
