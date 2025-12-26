# Coup

A bluffing and deduction card game implemented using the `boardgamepy` framework. This showcases the framework's ability to handle hidden information, bluffing mechanics, and character-based abilities.

**Features:**
- ✅ Hidden character cards
- ✅ Bluffing mechanics
- ✅ 5 unique character abilities
- ✅ Coin economy system
- ✅ Player elimination
- ✅ MongoDB & LangSmith logging support

## Logging Support

This example includes full MongoDB logging to capture game states and LLM interactions. Optionally enable LangSmith for LLM observability.

**Enable logging** (edit `.env` in project root):
```env
ENABLE_LOGGING=true
LANGCHAIN_TRACING_V2=true  # Optional: LangSmith tracing
```

See [LOGGING_GUIDE.md](../../LOGGING_GUIDE.md) for complete documentation.

## Game Overview

Coup is a game of manipulation, bluffing, and deduction for 2-6 players. You are head of a family in an Italian city-state, a city run by a weak and corrupt court. You need to manipulate, bluff, and bribe your way to power. Your objective is to destroy the influence of all other families, forcing them into exile. Only one family will survive...

## Game Rules

### Setup
- Each player starts with:
  - 2 **influence** (character cards, hidden from others)
  - 2 **coins**
- 15 character cards total: 3 of each character (Duke, Assassin, Captain, Ambassador, Contessa)
- Last player with influence wins!

### Turn Structure
On your turn, you take ONE action:

### Basic Actions (Always Available)
1. **Income**: Take 1 coin (cannot be challenged or blocked)
2. **Foreign Aid**: Take 2 coins (can be blocked by Duke)
3. **Coup**: Pay 7 coins to force opponent to lose 1 influence (cannot be challenged or blocked)
   - **MANDATORY** if you have 10+ coins

### Character Actions (Can Claim Any Character!)
You can claim to be ANY character and use their ability - even if you don't have that card! But beware: others can challenge you.

**Duke**
- **Tax**: Take 3 coins
- **Block**: Foreign Aid

**Assassin**
- **Assassinate**: Pay 3 coins to force opponent to lose 1 influence (can be blocked by Contessa)

**Captain**
- **Steal**: Take 2 coins from another player (can be blocked by Captain or Ambassador)

**Ambassador**
- **Exchange**: Draw 2 cards from deck, choose which 2 to keep

**Contessa**
- **Block**: Assassination

### Challenges & Blocks (Simplified in This Version)

**Full Game Rules (not fully implemented here):**
- When someone claims a character action, you can **challenge** them
- If they DON'T have the card: they lose 1 influence
- If they DO have the card: you lose 1 influence, and they shuffle it back and draw a new one
- Some actions can be **blocked** by claiming certain characters (which can also be challenged)

**This Implementation:**
- Simplified version without full challenge/block mechanics
- Focus on action execution and coin/influence management
- AI can still strategically claim characters and use their abilities

### Losing Influence
- When you lose influence, you must reveal one of your character cards
- Revealed cards remain visible to all players
- Lose both cards and you're eliminated

### Winning
- Be the last player with at least 1 influence!

## Character Summary

| Character | Action | Effect | Blocks |
|-----------|--------|--------|--------|
| Duke | Tax | Take 3 coins | Foreign Aid |
| Assassin | Assassinate | Pay 3 coins, eliminate influence | - |
| Captain | Steal | Take 2 coins from player | Stealing |
| Ambassador | Exchange | Swap cards with deck | Stealing |
| Contessa | - | No action | Assassination |

## Strategy Tips

1. **Coin Management**
   - Build to 7 coins for Coup
   - Watch for opponents reaching 10 (forced Coup)
   - Tax (Duke) is fastest coin generation

2. **Bluffing**
   - You can claim ANY character, even without the card!
   - Vary your claims to stay unpredictable
   - Track what's been revealed to inform bluffs

3. **Target Selection**
   - Eliminate threats early with Coup/Assassinate
   - Steal from rich opponents to slow them down
   - Watch who's close to 7 coins

4. **Character Priority**
   - Duke is powerful (3 coins/turn)
   - Assassin is cheaper than Coup
   - Contessa protects from assassination
   - Captain disrupts others' economies

5. **Timing**
   - Early game: Build coins with Tax/Income
   - Mid game: Steal/Assassinate to control board
   - Late game: Coup to finish off survivors

## Running the Game

```bash
# Set your API key
export OPENROUTER_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"

# Run the game
python examples/coup/main.py
```

## Customizing Player Count

Edit `config.py` to change the number of players:

```python
self.num_players = 3  # Default (2-6 players supported)
# Try:
# self.num_players = 2  # Heads-up intense duels
# self.num_players = 4  # Classic 4-player
# self.num_players = 6  # Maximum chaos
```

## Implementation Files

- `characters.py` - Character type definitions and deck creation
- `board.py` - Board managing influence, coins, and hidden information
- `state.py` - Game state tracking current player and pending actions
- `actions.py` - TakeTurnAction with all actions (income, coup, tax, assassinate, steal, exchange)
- `prompts.py` - AI prompts with character abilities and strategy hints
- `game.py` - CoupGame with player elimination
- `ui.py` - Terminal UI with influence tracking and coin display
- `main.py` - Entry point with game loop
- `config.py` - Configuration and API keys

## Framework Features Demonstrated

### 1. Hidden Information
```python
def get_view(self, context: ViewContext) -> str:
    # Players see their own cards
    # Others' cards are hidden (only revealed ones visible)
    unrevealed = [card for card in your_cards if not card.revealed]
```

### 2. Character Cards
```python
class CharacterType(Enum):
    DUKE = ("Duke", 3)
    ASSASSIN = ("Assassin", 3)
    # ... 5 character types, 3 of each
```

### 3. Influence System
```python
def reveal_influence(self, player_idx: int, character_type: CharacterType):
    # Lose influence by revealing a card
    for card in self.influence[player_idx]:
        if not card.revealed and card.type == character_type:
            card.revealed = True
```

### 4. Resource Management
```python
# Coins for economy and Coup/Assassinate costs
self.coins: dict[int, int] = {i: 2 for i in range(num_players)}
```

### 5. Player Elimination
```python
def has_influence(self, player_idx: int) -> bool:
    # Eliminated when both cards revealed
    return any(not card.revealed for card in self.influence[player_idx])
```

## Example Output

```
============================================================
    COUP
============================================================

Players:

  Player 1   [2 INFLUENCE]                💰💰💰💰💰 (5)
  Player 2   [1 INFLUENCE]                💰💰 (2)
    Revealed: Duke
  Player 3   [2 INFLUENCE]                💰💰💰💰 (4)

Recent Actions:
  Player 1: tax (Duke)
  Player 2: steal (Captain) → Player 1 (2 coins)
  Player 3: income

>>> Player 1's Turn
Your Cards: Assassin, Captain
Your Coins: 5

[Player 1]
  Action: ASSASSINATE (claims Assassin)
  Target: Player 2
  Reasoning: Eliminate weakened opponent with only 1 influence left
```

## Implementation Notes

### Simplified Version

This implementation is a simplified version of Coup that focuses on:
- ✅ Core action mechanics
- ✅ Character abilities
- ✅ Coin economy
- ✅ Influence management
- ✅ Player elimination
- ⚠️ Challenges and blocks (simplified)

**Future Enhancements:**
- Full challenge/counter-challenge system
- Block mechanics with challenges
- Card exchange on successful challenge defense
- Interactive challenge prompts

### Why Simplified?

Full Coup with challenges requires:
1. Interrupt-based action system
2. Multi-step challenge resolution
3. Bluff detection and counter-bluffs
4. Complex state machine for action phases

The current implementation demonstrates the core game mechanics while keeping the codebase manageable. The boardgamepy framework can support full challenge mechanics with additional action types and state management.

## Card Distribution

Total: 15 cards
- Duke: 3 cards
- Assassin: 3 cards
- Captain: 3 cards
- Ambassador: 3 cards
- Contessa: 3 cards

## Why Coup?

Coup is an excellent example of:
- **Bluffing mechanics** - Claim characters you don't have
- **Hidden information** - Your cards are secret
- **Risk/reward** - Bluff for advantage or play it safe
- **Economic strategy** - Build coins efficiently
- **Player elimination** - Lose influence, lose the game
- **Deduction** - Track revealed cards to catch bluffs

The boardgamepy implementation handles hidden information, character abilities, and strategic AI decision-making!
