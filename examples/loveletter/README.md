# Love Letter

A classic card game of deduction, risk, and luck implemented using the `boardgamepy` framework. This showcases the framework's ability to handle hidden information, card effects, and player elimination.

**Features:**
- ✅ Hidden card hands
- ✅ 8 unique card effects
- ✅ Player elimination mechanics
- ✅ Multi-round structure
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

Love Letter is a game of risk, deduction, and luck for 2-4 players. Players attempt to deliver their love letter to the Princess while eliminating opponents from the round. The last player standing (or highest card when the deck runs out) wins the round and earns a token of affection!

## Game Rules

### Setup
- 16 cards with 8 different types (Guard, Priest, Baron, Handmaid, Prince, King, Countess, Princess)
- Each player starts with 1 card
- One card is removed from play face-down
- First player to win the target number of tokens wins the game:
  - 2 players: 7 tokens
  - 3 players: 5 tokens
  - 4 players: 4 tokens

### Turn Structure
1. Draw 1 card (now you have 2 cards)
2. Play 1 card and execute its effect
3. If you're the last player standing or the deck is empty, round ends

### Card Types and Effects

**Guard (1) - 5 cards**
- Guess another player's card (not Guard)
- If correct, they're eliminated

**Priest (2) - 2 cards**
- Look at another player's hand
- Gain secret information

**Baron (3) - 2 cards**
- Compare hands with another player
- Lower value is eliminated (tie = nothing happens)

**Handmaid (4) - 2 cards**
- Protection until your next turn
- Cannot be targeted by other players

**Prince (5) - 2 cards**
- Choose any player (including yourself) to discard and draw
- If they discard Princess, they're eliminated

**King (6) - 1 card**
- Trade hands with another player

**Countess (7) - 1 card**
- **MUST** be played if you have King or Prince
- No effect otherwise

**Princess (8) - 1 card**
- **Highest value card**
- If you play or discard this, you're immediately eliminated
- Win the round if you still have this at the end!

### Special Rules

1. **Countess Rule**: If you have Countess and (King OR Prince), you MUST play Countess
2. **Protection**: Protected players (Handmaid) cannot be targeted
3. **Self-targeting**: Prince can target yourself
4. **Elimination**: Eliminated players are out for the round but can win future rounds

## Strategy Tips

1. **Track Discarded Cards**: Pay attention to what's been played to deduce possibilities
2. **Use Priest Wisely**: Information is power - use it to make better Guard guesses
3. **Baron Timing**: Only use Baron when you have a high card or know opponent has low
4. **Handmaid Safety**: Use when you have Princess or want to avoid Baron/Prince
5. **Guard Deduction**: Count cards to narrow down possibilities before guessing
6. **Prince Strategy**: Can force high-value cards to be discarded (risky!)
7. **Protect the Princess**: Never willingly discard the Princess!

## Running the Game

```bash
# Set your API key
export OPENROUTER_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"

# Run the game
python examples/loveletter/main.py
```

## Customizing Player Count

Edit `config.py` to change the number of players:

```python
self.num_players = 2  # Default (2-4 players supported)
# Try:
# self.num_players = 3
# self.num_players = 4
```

## Implementation Files

- `cards.py` - Card type definitions and deck creation
- `board.py` - Board managing deck, hands, eliminations, and hidden information
- `state.py` - Game state tracking rounds and scores
- `actions.py` - PlayCardAction with all 8 card effects implemented
- `prompts.py` - AI prompts with card effects and strategy hints
- `game.py` - LoveLetterGame with round management
- `ui.py` - Terminal UI with player status and move history
- `main.py` - Entry point with multi-round game loop
- `config.py` - Configuration and API keys

## Framework Features Demonstrated

This implementation showcases several advanced boardgamepy features:

### 1. Hidden Information
```python
def get_view(self, context: ViewContext) -> str:
    # Players only see their own hand
    # Other hands are hidden (unless revealed by Priest)
    player_idx = player.player_idx
    hand_str = ", ".join(str(card) for card in self.hands[player_idx])
```

### 2. Knowledge Tracking
```python
# Board tracks what each player knows about others
self.known_cards: dict[int, dict[int, CardType | None]]
# Updated by Priest card effect
```

### 3. Multiple Action Effects
Each card type has unique logic in `actions.py`:
- Guard: Guess and elimination
- Priest: Knowledge revelation
- Baron: Comparison and conditional elimination
- Handmaid: Protection flag
- Prince: Forced discard/draw
- King: Hand swap
- Countess: Forced play rule
- Princess: Auto-elimination

### 4. Player Elimination
```python
self.eliminated: set[int]  # Track eliminated players
# Eliminated players skip turns but stay in game for future rounds
```

### 5. Round-based Structure
```python
def start_new_round(self):
    # Reset board state
    # Clear eliminations
    # Reshuffle deck
    # Award token to winner
```

## Example Output

```
============================================================
    LOVE LETTER
============================================================

Round 1
Score:
  Player 1: (0/7)
  Player 2: (0/7)

Players:
  Player 1 [ACTIVE]
  Player 2 [PROTECTED]

Discarded: Guard(1)×2, Priest(2)×1
Cards in deck: 11

Recent Moves:
  Player 2: Handmaid

>>> Player 1's Turn

[Player 1]
  Played: Guard
  Target: Player 2
  Guess: Baron
  Reasoning: Player 2 is protected, but trying anyway
```

## Card Distribution

Total: 16 cards
- Guard (1): 5 cards
- Priest (2): 2 cards
- Baron (3): 2 cards
- Handmaid (4): 2 cards
- Prince (5): 2 cards
- King (6): 1 card
- Countess (7): 1 card
- Princess (8): 1 card

## Why Love Letter?

Love Letter is a perfect example of a game with:
- **Simple rules** but **deep strategy**
- **Hidden information** - you don't know what opponents have
- **Deduction** - track played cards to narrow possibilities
- **Risk management** - when to play aggressive vs. defensive
- **Multiple rounds** - lose a battle, win the war

The boardgamepy implementation handles all these complexities while keeping the code clean and extensible!
