# Getting Started: Building Rock Paper Scissors

This guide will walk you through building a game with **BoardGamePy** from scratch. We'll start with a simple AI vs AI Rock-Paper-Scissors (RPS) and evolve it into a strategic version with health points and special effects.

## Level 0: Hello World (Single Round RPS)

Let's build the absolute simplest version: **one round**, two players, no score tracking. Just pure Rock-Paper-Scissors.

A game in BoardGamePy requires four core components:

1. **State** - Holds all mutable game data
2. **Board** - Renders the state for players to see
3. **Actions** - What players can do
4. **Game** - Ties everything together

### 1. Define the State (`state.py`)

The `GameState` holds all mutable data. For a single round, we just need to track each player's choice and whether the game is over.

```python
# state.py
from dataclasses import dataclass
from boardgamepy import GameState

@dataclass
class RPSState(GameState):
    player1_choice: str | None = None  # Stores P1's choice (rock/paper/scissors)
    player2_choice: str | None = None  # Stores P2's choice
    game_over: bool = False            # Tracks if the game has ended
    
    def is_terminal(self) -> bool:
        """Returns True when the game should end."""
        return self.game_over
    
    def get_winner(self) -> str | None:
        """Determines the winner based on RPS rules."""
        if not self.is_terminal():
            return None
        
        p1, p2 = self.player1_choice, self.player2_choice
        
        if p1 == p2:
            return None  # Draw
        elif (p1 == "rock" and p2 == "scissors") or \
             (p1 == "paper" and p2 == "rock") or \
             (p1 == "scissors" and p2 == "paper"):
            return "Player 1"
        else:
            return "Player 2"
```

**Key concepts:**

- `@dataclass` - Python decorator that auto-generates `__init__` and other methods
- `GameState` - Base class from BoardGamePy that all game states must inherit
- `is_terminal()` - Required method that tells the engine when the game ends
- `get_winner()` - Optional method to determine who won

### 2. Define the Board (`board.py`)

The `Board` renders the state into a string that players (including AI/LLMs) can read.

```python
# board.py
from boardgamepy import Board
from boardgamepy.protocols import ViewContext

class RPSBoard(Board):
    def get_view(self, context: ViewContext) -> str:
        """Returns a string representation of the current game state."""
        state = context.game_state
        
        if state.game_over:
            winner = state.get_winner()
            result = f"Winner: {winner}" if winner else "It's a Draw!"
            return f"{state.player1_choice} vs {state.player2_choice} -> {result}"
        
        return "Make your choice: rock, paper, or scissors"
```

**Key concepts:**

- `Board` - Base class for rendering game state
- `ViewContext` - Contains the current player and game state
- `get_view()` - Returns what players see; LLMs use this to understand the game

### 3. Define Actions (`actions.py`)

Actions define what players can do. Here, players can choose rock, paper, or scissors.

```python
# actions.py
from boardgamepy import Action
from pydantic import BaseModel, Field

class ChoiceOutput(BaseModel):
    """Schema for LLM output."""
    choice: str = Field(..., description="Your choice: rock, paper, or scissors")
    reasoning: str | None = None

class ChooseAction(Action):
    name = "choose"              # Unique identifier for this action
    OutputSchema = ChoiceOutput  # Links to the Pydantic schema above

    def validate(self, game, player, choice: str) -> bool:
        """Returns True if the choice is valid."""
        return choice.lower() in ["rock", "paper", "scissors"]

    def apply(self, game, player, choice: str):
        """Executes the action and updates game state."""
        state = game.state
        choice = choice.lower()
        
        # Store choice for the correct player
        if player.player_idx == 0:
            state.player1_choice = choice
        else:
            state.player2_choice = choice
        
        # If both players have chosen, end the game
        if state.player1_choice and state.player2_choice:
            state.game_over = True
            p1, p2 = state.player1_choice, state.player2_choice
            winner = state.get_winner()
            result = f"{winner} wins!" if winner else "It's a tie!"
            print(f"{p1} vs {p2} -> {result}")

    def to_history_record(self, player, choice: str, **params):
        return {"type": "choose", "player": player.name, "choice": choice}
```

**Key concepts:**

- `Action` - Base class for player actions
- `name` - Unique identifier used by the framework to match actions (required)
- `OutputSchema` - Pydantic model that defines how LLMs should structure their response
- `validate()` - Checks if the action is legal
- `apply()` - Executes the action and modifies game state
- `player.player_idx` - Index (0 or 1) to identify which player is acting

### 4. The Game Class (`game.py`)

The `Game` class ties all components together.

```python
# game.py
from boardgamepy import Game, Player, GameHistory
from state import RPSState
from board import RPSBoard
from actions import ChooseAction

class RPSGame(Game):
    name = "Rock Paper Scissors"

    def setup(self, **config):
        self.state = RPSState()
        self.board = RPSBoard()
        self.players = [
            Player(name="P1", team="1", player_idx=0),
            Player(name="P2", team="2", player_idx=1)
        ]
        self.actions = [ChooseAction()]
        self.history = GameHistory()

    def get_current_player(self):
        if self.state.player1_choice is None:
            return self.players[0]
        if self.state.player2_choice is None:
            return self.players[1]
        return None

    def next_turn(self):
        pass
```

**Key concepts:**

- `Game` - Base class that orchestrates gameplay
- `setup()` - Called once to initialize the game
- `get_current_player()` - Determines whose turn it is
- `Player` - Represents a player with name, team, and index

### 5. Define Prompt Builder (`prompts.py`)

AI agents need instructions. The `PromptBuilder` creates prompts from game state.

```python
# prompts.py
from boardgamepy.ai import PromptBuilder
from boardgamepy import SimpleViewContext

class RPSPromptBuilder(PromptBuilder):
    def build_system_prompt(self) -> str:
        """System prompt that sets the AI's role."""
        return "You are an AI playing Rock Paper Scissors. Choose wisely to beat your opponent."
    
    def build_user_prompt(self, game, player) -> str:
        """Create view context for board rendering."""
        context = SimpleViewContext(player=player, game_state=game.state)
        view = game.board.get_view(context)
        
        return f"""
Current Game State:
{view}

Rules:
- Rock beats Scissors
- Scissors beats Paper
- Paper beats Rock

Make your choice: rock, paper, or scissors.
"""
```

**Key concepts:**

- `PromptBuilder` - Base class for constructing LLM prompts
- `build_system_prompt()` - Sets the AI's persona/role
- `build_user_prompt()` - Provides game-specific context for each turn
- `SimpleViewContext` - Helper to create view context for board rendering

### 6. Running It (`main.py`)

Use `GameRunner` to run the game with AI agents.

```python
# main.py
from boardgamepy.core.runner import GameRunner
from actions import ChooseAction, ChoiceOutput
from game import RPSGame
from prompts import RPSPromptBuilder

if __name__ == "__main__":
    import boardgamepy

    print(f"Boardgamepy version: {boardgamepy.__version__}")
    print("Hello from try-bg!")
    print("Starting game...")
    
    GameRunner.main(
        game_class=RPSGame,
        prompt_builder_class=RPSPromptBuilder,
        output_schema=ChoiceOutput,
        action_class=ChooseAction,
        default_num_players=2,
    )()
```

**Key concepts:**

- `GameRunner.main()` - Factor method that creates a CLI runner for your game. It handles:
    - The main game loop (checking `is_terminal`)
    - Prompting players (AI or Human)
    - Validating and applying actions
    - Managing the turn order
- `output_schema` - The Pydantic model (`ChoiceOutput`) that forces the LLM to reply with structured JSON.


That's it! You now have a working single-round RPS game. 🎉

---

## Level 1: Adding Multiple Rounds

Now let's extend our game to play **3 rounds** and keep score. This builds on Level 0 by adding round tracking and scoring.

### Changes from Level 0

We're adding these new fields to `RPSState`:

- `current_round` - Tracks which round we're on
- `max_rounds` - Total rounds to play (default: 3)
- `player1_score` / `player2_score` - Track each player's wins

> [!NOTE]
> **Why do `is_terminal()` and `get_winner()` change?**
>
> In **Level 0**, we had a single round, so:
> - `is_terminal()` just checked a `game_over` boolean (game ends when both players choose)
> - `get_winner()` compared the two choices directly to determine the single-round winner
>
> In **Level 1**, we play multiple rounds, so:
> - `is_terminal()` now checks `current_round >= max_rounds` (game continues until all rounds are played)
> - `get_winner()` compares accumulated **scores** instead of choices (winner is whoever won the most rounds)
>
> The RPS comparison logic moves from `get_winner()` into `ChooseAction.apply()`, where we update scores each round.

### 1. Update the State (`state.py`)

```python
# state.py
from dataclasses import dataclass
from boardgamepy import GameState

@dataclass
class RPSState(GameState):
    current_round: int = 0
    max_rounds: int = 3
    player1_choice: str | None = None
    player2_choice: str | None = None
    player1_score: int = 0
    player2_score: int = 0
    
    def is_terminal(self) -> bool:
        """Returns True when the game should end."""
        return self.current_round >= self.max_rounds
    
    def get_winner(self) -> str | None:
        """Determines the winner based on RPS rules."""
        if not self.is_terminal():
            return None
        if self.player1_score > self.player2_score:
            return "Player 1"
        elif self.player2_score > self.player1_score:
            return "Player 2"
        return None # Draw
```

### 2. Update the Board (`board.py`)

The `Board` now shows round progress and scores.

```python
# board.py
from boardgamepy import Board
from boardgamepy.protocols import ViewContext

class RPSBoard(Board):
    def get_view(self, context: ViewContext) -> str:
        """Returns a string representation of the current game state."""
        state = context.game_state
        return f"Round {state.current_round + 1}/{state.max_rounds} | Score: P1={state.player1_score}, P2={state.player2_score}"
```

### 3. Update Actions (`actions.py`)

The key change: RPS comparison logic moves here. After each round, we update scores and reset choices for the next round.

```python
# actions.py
from boardgamepy import Action
from pydantic import BaseModel, Field

class ChoiceOutput(BaseModel):
    """Schema for LLM output."""
    choice: str = Field(..., description="Your choice: rock, paper, or scissors")
    reasoning: str | None = None

class ChooseAction(Action):
    name = "choose"
    OutputSchema = ChoiceOutput

    def validate(self, game, player, choice: str) -> bool:
        """Returns True if the choice is valid."""
        return choice.lower() in ["rock", "paper", "scissors"]

    def apply(self, game, player, choice: str):
        """Executes the action and updates game state."""
        state = game.state
        choice = choice.lower()
        
        # Store choice for the correct player
        if player.player_idx == 0:
            state.player1_choice = choice
        else:
            state.player2_choice = choice
        
        # If both picked, resolve round
        if state.player1_choice and state.player2_choice:
            p1, p2 = state.player1_choice, state.player2_choice
            
            # Determine winner
            if p1 == p2:
                result = "Tie!"
            elif (p1 == "rock" and p2 == "scissors") or \
                 (p1 == "paper" and p2 == "rock") or \
                 (p1 == "scissors" and p2 == "paper"):
                state.player1_score += 1
                result = "P1 wins!"
            else:
                state.player2_score += 1
                result = "P2 wins!"
            
            print(f"Round {state.current_round + 1}: {p1} vs {p2} -> {result}")
            
            # Reset for next round
            state.current_round += 1
            state.player1_choice = None
            state.player2_choice = None
    
    def to_history_record(self, player, choice: str, **params):
        return {"type": "choose", "player": player.name, "choice": choice}
```

### 4. The Game Class (`game.py`)

Same as Level 0.

### 5. Prompt Builder (`prompts.py`)

Same as Level 0.

### 6. Terminal UI (`ui.py`)

Add a simple terminal UI to display player names (including AI model names) with colors.

```python
# ui.py
"""Terminal UI for RPS game."""
from boardgamepy.ui import terminal as term

def render_status(game) -> None:
    """Render game status with player names and scores."""
    state = game.state
    
    # Get player names (includes model names when using AI)
    p1 = game.players[0]
    p2 = game.players[1]
    p1_label = f"P1 ({p1.name})" if p1.name else "Player 1"
    p2_label = f"P2 ({p2.name})" if p2.name else "Player 2"
    
    print(
        f"{term.BOLD}Round {min(state.current_round + 1, state.max_rounds)}/{state.max_rounds}{term.RESET}"
    )
    print()
    print(f"{term.FG_BRIGHT_CYAN}{term.BOLD}{p1_label}{term.RESET}  Score: {state.player1_score}")
    print(f"{term.FG_BRIGHT_YELLOW}{term.BOLD}{p2_label}{term.RESET}  Score: {state.player2_score}")

def render_turn_prompt(player_name: str, player_num: int) -> None:
    """Show whose turn it is."""
    color = term.FG_BRIGHT_CYAN if player_num == 1 else term.FG_BRIGHT_YELLOW
    print(f"\n🤖 {color}{term.BOLD}{player_name}'s turn...{term.RESET}")

def render_ai_choice(choice: str, reasoning: str | None = None) -> None:
    """Show the AI's choice."""
    print(f"   {term.BOLD}Choice:{term.RESET} {choice}")
    if reasoning:
        print(f"   {term.DIM}Reasoning: {reasoning[:100]}...{term.RESET}")

def render_game_over(game) -> None:
    """Show final results."""
    state = game.state
    winner = state.get_winner()
    
    print("\n" + "═" * 40)
    if winner:
        print(f"  🏆 {term.BOLD}{winner} WINS!{term.RESET}")
    else:
        print(f"  {term.BOLD}TIE GAME!{term.RESET}")
    print(f"  Final: P1={state.player1_score} | P2={state.player2_score}")
    print("═" * 40)

def refresh(game) -> None:
    """Clear and redraw the UI."""
    term.clear()
    term.render_header("ROCK PAPER SCISSORS", width=40)
    print()
    render_status(game)
```

> [!NOTE]
> **Why add a UI module?**
>
> The `ui_module` is optional but recommended for multi-round games. It:
> - Displays **AI model names** as player names (e.g., "P1 (gpt-4)")
> - Shows **round progress** and scores with colors
> - Provides a **refresh()** function called by the runner to redraw the screen
>
> Without it, you'll only see the basic `print()` output from the action.

**Key concepts:**

- `boardgamepy.ui.terminal` - Provides ANSI color codes and terminal helpers
- `player.name` - Contains the model name when using AI agents
- `refresh()` - Called by the runner to update the display each turn

### 7. Running It (`main.py`)

```python
# main.py
from boardgamepy.core.runner import GameRunner
from actions import ChooseAction, ChoiceOutput
from game import RPSGame
from prompts import RPSPromptBuilder
import ui

if __name__ == "__main__":
    import boardgamepy

    print(f"Boardgamepy version: {boardgamepy.__version__}")
    print("Hello from try-bg!")
    print("Starting game...")

    GameRunner.main(
        game_class=RPSGame,
        prompt_builder_class=RPSPromptBuilder,
        output_schema=ChoiceOutput,
        action_class=ChooseAction,
        default_num_players=2,
        ui_module=ui,  # NEW: enables the terminal UI
    )()
```

---

## Level 2: Strategic Depth

Currently, the AI just picks randomly because there's no incentive or strategy. Rock always beats Scissors. But what if Rock was "High Risk, High Reward" this round?

In **Level 2**, we introduce sophisticated mechanics to force the AI to "think":

1.  **Health Points (HP)**: Start with 3 HP. If you lose a "High Risk" round, you might lose HP. Reach 0 HP and you lose immediately.
2.  **Victory Points (VP)**: First to 10 points wins.
3.  **Randomized Effects**: Each round, the choices (Rock/Paper/Scissors) are assigned random properties (e.g., "Safe (+1 pt)" vs "Risky (+5 pts / -2 HP)").

This requires the AI to read the board, understand the current round's unique risks, and choose accordingly.

### 1. The Strategy State (`strategy_game.py`)

We need a richer state to track health, points, and the current round's special effects.

```python
# strategy_game.py
from dataclasses import dataclass, field
import random
from boardgamepy import Game, GameState, Board, Player, GameHistory, Action
from boardgamepy.protocols import ViewContext
# We will define this action in the next step
from actions import StrategyChooseAction

# Configurations for our effects
EFFECT_LEVELS = [
    {"win_points": 1, "lose_effect": 0, "lose_type": "none", "name": "Safe (+1/0)"},
    {"win_points": 3, "lose_effect": 1, "lose_type": "points", "name": "Medium Risk (+3/-1pt)"},
    {"win_points": 5, "lose_effect": 2, "lose_type": "health", "name": "Extreme Risk (+5/-2♥)"},
]

def randomize_effects() -> dict[str, dict]:
    """Randomly assign effects to rock/paper/scissors for the round."""
    choices = ["rock", "paper", "scissors"]
    # Pick 3 random effects
    selected = random.choices(EFFECT_LEVELS, k=3) 
    return {c: effect for c, effect in zip(choices, selected)}

@dataclass
class StrategyRPSState(GameState):
    current_round: int = 0
    max_rounds: int = 15
    player1_choice: str | None = None
    player2_choice: str | None = None
    
    # New stats: Score and Health
    player1_score: int = 0
    player2_score: int = 0
    player1_health: int = 3
    player2_health: int = 3
    
    game_over: bool = False
    winner: str | None = None
    
    # Maps "rock"/"paper"/"scissors" to their effect dict for this round
    effect_mapping: dict[str, dict] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return self.game_over
    
    def get_winner(self) -> str | None:
        return self.winner
```

### 2. The Strategic Board (`strategy_game.py`)

The board must now display the **risk/reward info** so the AI can make informed decisions. Add this `StrategyRPSBoard` class to `strategy_game.py`.

```python
class StrategyRPSBoard(Board):
    def get_view(self, context: ViewContext) -> str:
        state = context.game_state
        
        # Build the view string
        view = [
            "--- STRATEGIC RPS ---",
            f"Round: {state.current_round + 1}",
            f"P1: Score={state.player1_score} HP={state.player1_health}",
            f"P2: Score={state.player2_score} HP={state.player2_health}",
            "",
            "THIS ROUND'S EFFECTS:"
        ]
        
        # Show effects so the AI knows what's at stake
        for choice, effect in state.effect_mapping.items():
            win = effect['win_points']
            lose = f"{effect['lose_effect']} ({effect['lose_type']})"
            view.append(f"  {choice.upper()}: Win=+{win} | Lose=-{lose}")
            
        return "\n".join(view)
```

### 3. The Game Class (`strategy_game.py`)

Finally, the Game class initializes the state and randomizes the first round. Add this to `strategy_game.py`.

```python
class StrategyRPSGame(Game):
    name = "Strategic RPS"
    
    def setup(self, **config):
        self.state = StrategyRPSState()
        self.board = StrategyRPSBoard()
        self.history = GameHistory()
        self.players = [
            Player(name="P1", team="1", player_idx=0),
            Player(name="P2", team="2", player_idx=1)
        ]
        self.actions = [StrategyChooseAction()] # We'll create this next
        
        # INIT: Randomize effects for the very first round
        self.state.effect_mapping = randomize_effects()

    def get_current_player(self):
        if self.state.game_over: return None
        if self.state.player1_choice is None: return self.players[0]
        if self.state.player2_choice is None: return self.players[1]
        return None

    def next_turn(self):
        pass
```

### 4. Smart Actions (`actions.py`)

The action logic is where the magic happens. We need to apply the specific effects of the chosen move. Update `actions.py` to include `StrategyChooseAction`.

```python
# actions.py (append this class)

# ... imports ...
from pydantic import BaseModel, Field

# We can reuse ChoiceOutput or make a new one to encourage reasoning
class StrategyChoiceOutput(BaseModel):
    choice: str = Field(..., description="rock, paper, or scissors")
    reasoning: str = Field(..., description="Strategic reasoning based on risk/reward")

class StrategyChooseAction(Action):
    name = "choose"
    OutputSchema = StrategyChoiceOutput

    def validate(self, game, player, choice: str) -> bool:
        return choice.lower() in ["rock", "paper", "scissors"]

    def apply(self, game, player, choice: str):
        state = game.state
        choice = choice.lower()
        
        if player.player_idx == 0:
            state.player1_choice = choice
        else:
            state.player2_choice = choice
            
        # If both chose, resolve the round
        if state.player1_choice and state.player2_choice:
            self._resolve_round(game)
            
    def _resolve_round(self, game):
        state = game.state
        p1 = state.player1_choice
        p2 = state.player2_choice
        
        # 1. Determine Winner of the clash
        if p1 == p2:
            winner = None # Tie
        elif (p1 == "rock" and p2 == "scissors") or \
             (p1 == "paper" and p2 == "rock") or \
             (p1 == "scissors" and p2 == "paper"):
            winner = 0 # Player 1
        else:
            winner = 1 # Player 2
            
        # 2. Apply Effects
        if winner is not None:
            w_choice = p1 if winner == 0 else p2
            l_choice = p2 if winner == 0 else p1
            
            # Get effects for this round
            w_effect = state.effect_mapping[w_choice]
            l_effect = state.effect_mapping[l_choice]
            
            # Apply Win Bonus
            if winner == 0:
                state.player1_score += w_effect['win_points']
            else:
                state.player2_score += w_effect['win_points']
                
            # Apply Loss Penalty
            penalty_val = l_effect['lose_effect']
            if l_effect['lose_type'] == 'points':
                if winner == 0: state.player2_score = max(0, state.player2_score - penalty_val)
                else: state.player1_score = max(0, state.player1_score - penalty_val)
            elif l_effect['lose_type'] == 'health':
                if winner == 0: state.player2_health -= penalty_val
                else: state.player1_health -= penalty_val

        # 3. Check Game Over
        if state.player1_score >= 10:
            state.winner = "Player 1"
            state.game_over = True
        elif state.player2_score >= 10:
            state.winner = "Player 2"
            state.game_over = True
        elif state.player1_health <= 0:
            state.winner = "Player 2" # P1 died
            state.game_over = True
        elif state.player2_health <= 0:
            state.winner = "Player 1" # P2 died
            state.game_over = True
        elif state.current_round >= state.max_rounds:
            state.winner = "Tie" if state.player1_score == state.player2_score else \
                           ("Player 1" if state.player1_score > state.player2_score else "Player 2")
            state.game_over = True

        # 4. Reset for next round
        if not state.game_over:
            from strategy_game import randomize_effects
            state.current_round += 1
            state.player1_choice = None
            state.player2_choice = None
            state.effect_mapping = randomize_effects()
            
    def to_history_record(self, player, choice: str, **params):
        return {"type": "choose", "player": player.name, "choice": choice}
```

### 5. Strategic Prompting (`prompts_strategy.py`)

We need to tell the AI *how* to think. It needs to know that reading the "Effects" section is crucial.

```python
# prompts_strategy.py
from boardgamepy.ai import PromptBuilder
from boardgamepy import SimpleViewContext

class StrategyRPSPromptBuilder(PromptBuilder):
    def build_system_prompt(self) -> str:
        return "You are an expert Strategic Rock Paper Scissors player. Analyze the risk/reward of each choice based on the current round's effects."

    def build_user_prompt(self, game, player) -> str:
        context = SimpleViewContext(player=player, game_state=game.state)
        view = game.board.get_view(context)
        
        return f"""
Current Game Board:
{view}

Rules:
1. Standard RPS rules apply (Rock > Scissors, etc).
2. Look at "THIS ROUND'S EFFECTS".
   - If you WIN, you gain 'Win' points.
   - If you LOSE, you suffer the 'Lose' penalty (Points or Health).
3. First to 10 Points wins.
4. If Health drops to 0, you LOSE immediately.

Strategy:
- If you are low on health, avoid moves with high health penalties.
- If you need points, take risks.

Make your choice provided in the schema.
"""
```

### 6. Running It

Create a new runner script, say `main_strategy.py`, to run this advanced version.

```python
# main_strategy.py
from boardgamepy.core.runner import GameRunner
from strategy_game import StrategyRPSGame
from prompts_strategy import StrategyRPSPromptBuilder
from actions import StrategyChooseAction, StrategyChoiceOutput
import ui # You can reuse the UI from Level 1!

if __name__ == "__main__":
    GameRunner.main(
        game_class=StrategyRPSGame,
        prompt_builder_class=StrategyRPSPromptBuilder,
        output_schema=StrategyChoiceOutput,
        action_class=StrategyChooseAction,
        default_num_players=2,
        ui_module=ui
    )()
```

Now you have a game where the AI isn't just picking randomly—it's evaluating complex trade-offs!

## Next Steps

Explore the full example in `examples/rps/` to see more advanced features like:

- **Rich Console UI**: Using box-drawing characters for a better look.
- **Complex Matchmaking**: Playing against different types of AI agents.
- **Tournaments**: Running automated battles between models.
