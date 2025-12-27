# Strategic Rock Paper Scissors (AI vs AI)

Rock Paper Scissors with **randomized risk/reward effects each round!**

**Run:**
```bash
python main.py
```

**Game Rules:**

### How It Works

- **3 choices**: Rock, Paper, Scissors (standard RPS rules)
- **5 effect levels**: Each round, 3 random effects are assigned to the 3 choices
- **Strategic depth**: AIs see the effects BEFORE choosing, but don't know what opponent will pick!
- **AI vs AI** - Watch two AI agents make strategic decisions!

### Effect Levels (randomly assigned each round)

| Win Reward | Loss Penalty       |
|------------|-------------------|
| +1 point   | None (0)          |
| +2 points  | -1 point          |
| +3 points  | -2 points         |
| +4 points  | -1 health         |
| +5 points  | -2 health         |

### Example Round

```
THIS ROUND'S EFFECTS:
  Rock     → +3/-2pt
  Paper    → +1/0
  Scissors → +4/-1♥
```

Strategic decisions:
- Scissors: Big reward (+4) but lose health if you fail
- Rock: Medium reward (+3) with point penalty risk
- Paper: Safe choice (+1) with no penalty

### Win Conditions

- First to **10 points** wins
- If opponent reaches **0 health**, you win
- After **15 rounds**, player with higher score wins

### Starting Conditions

- 3 health each
- 0 points each
- 15 rounds maximum

## Key Concepts Demonstrated

This example demonstrates BoardGamePy's core patterns:
- **GameState** - Holding game data (scores, health, effects)
- **Board** - Displaying game view to players
- **Action** - Defining player moves with validation
- **Game** - Orchestrating everything together
- **Complex game logic** - Multiple win conditions, risk/reward mechanics
- **Data-driven design** - Effect configurations and randomization
- **Resource management** - Player health and points

## Files

- `strategy_game.py` - Strategic RPS game, state, and board
- `actions.py` - Actions for the game
- `main.py` - Main game runner
- `prompts_strategy.py` - AI prompts for strategic decision-making
- `ui.py` - Terminal UI rendering

## Tutorial

See the full tutorial in the documentation:
- [Getting Started Tutorial](../../docs/getting-started/tutorial.md)
