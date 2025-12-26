# Sushi Go!

A fast-paced card drafting game implemented using the `boardgamepy` framework. Pick and pass sushi cards to build the best meal and score the most points!

**Features:**
- ✅ Card drafting mechanics
- ✅ Simultaneous play
- ✅ Complex scoring rules
- ✅ Set collection
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

Sushi Go! is a card drafting game for 2-5 players. Players simultaneously choose cards from their hands, then pass the remaining cards to their neighbor. Cards you pick go into your collection and score points based on set collection and majority scoring. After 3 rounds, the player with the highest score wins!

## Game Rules

### Setup
- 2-5 players (default: 4)
- Each player starts with a hand of cards (varies by player count)
- Play 3 rounds total

### Round Structure

**Each Turn:**
1. Look at the cards in your hand
2. Pick ONE card to keep (add to your collection)
3. Pass remaining cards to the next player
4. Repeat until all cards are played

**End of Round:**
- Score your collected cards
- Add pudding cards to your pudding total (scored at game end)
- Start a new round with fresh hands

### Card Types and Scoring

**Maki Rolls** 🍙 (1, 2, or 3 icons)
- Count total maki icons across all your maki cards
- Most maki: **6 points**
- Second most: **3 points**
- Ties split the points

**Tempura** 🍤
- Collect **2 Tempura** = **5 points**
- Incomplete sets worth 0

**Sashimi** 🍣
- Collect **3 Sashimi** = **10 points**
- Very valuable! Incomplete sets worth 0

**Dumpling** 🥟
- More is better!
- 1 = 1 pt, 2 = 3 pts, 3 = 6 pts, 4 = 10 pts, 5+ = 15 pts

**Nigiri** 🍱
- **Egg Nigiri**: 1 point
- **Salmon Nigiri**: 2 points
- **Squid Nigiri**: 3 points
- Immediate scoring, can be tripled with Wasabi

**Wasabi** 🌱
- Next nigiri you play is **tripled** in value
- Egg (1) → 3, Salmon (2) → 6, Squid (3) → 9
- Wasabi without nigiri = 0 points

**Chopsticks** 🥢
- Special! Lets you take **2 cards** on a future turn
- Exchange chopsticks for 2 cards later in the round

**Pudding** 🍮
- Scored at **end of game** (not each round)
- Most pudding: **+6 points**
- Least pudding: **-6 points** (3+ players)
- 2 players: Only most pudding gets points

## Strategy Guide

### Early Round (Full Hands)
- **Start sets**: Grab Sashimi or Tempura to begin combos
- **Grab Wasabi**: Set up for triple nigiri later
- **High Maki**: 3-maki cards are valuable
- **Deny opponents**: Block their sets if possible

### Mid Round (Medium Hands)
- **Complete sets**: Finish Sashimi (10 pts!) or Tempura (5 pts)
- **Wasabi + Nigiri**: Complete the combo
- **Watch opponents**: See what they're collecting
- **Maki race**: Assess if you can compete for 6/3 bonus

### Late Round (Few Cards)
- **Finish what you started**: Complete partial sets
- **Maki sniping**: Secure 1st or 2nd place
- **Deny opponents**: Block their final set completions
- **Pudding balance**: Don't ignore dessert!

### Key Strategic Concepts

**Set Prioritization:**
1. **Sashimi** (10 pts for 3 cards = 3.33 pts/card) - Best value!
2. **Tempura** (5 pts for 2 cards = 2.5 pts/card)
3. **Wasabi + Squid** (9 pts for 2 cards = 4.5 pts/card) - If you can get both!
4. **Dumplings** (Scales up, great for 3+)
5. **Maki** (Depends on competition)

**Card Drafting:**
- Pick cards that **complete YOUR sets**
- Deny cards that **complete OPPONENT sets**
- Balance between **immediate points** and **set building**
- Don't ignore **pudding** entirely (end-game swing of ±6 pts per player!)

**Maki Competition:**
- With 3-maki cards, you can quickly dominate
- Watch what others are collecting
- Sometimes better to let opponents fight over maki while you build sets

**Pudding Strategy:**
- Early rounds: Pudding is low priority (focus on round points)
- Mid rounds: Start accumulating if behind
- Late rounds: Balance pudding with final round scoring

## Running the Game

```bash
# Set your API key
export OPENROUTER_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"

# Run the game (default 4 players)
python examples/sushigo/main.py
```

## Customizing Player Count

Edit `config.py` to change the number of players:

```python
self.num_players = 4  # Default (2-5 players)
# Try:
# self.num_players = 2  # Heads-up duel
# self.num_players = 5  # Maximum chaos
```

**Cards per hand** (varies by player count):
- 2 players: 10 cards
- 3 players: 9 cards
- 4 players: 8 cards
- 5 players: 7 cards

## Implementation Files

- `cards.py` - Card type definitions and deck (108 cards total)
- `board.py` - Board managing hands, collections, and scoring
- `state.py` - Game state with round tracking and scores
- `actions.py` - PlayCardAction for card drafting
- `prompts.py` - AI prompts with strategic guidance
- `game.py` - SushiGoGame with round management
- `ui.py` - Terminal UI with collection display
- `main.py` - Entry point with game loop
- `config.py` - Configuration

## Framework Features Demonstrated

### 1. Card Drafting Mechanic
```python
def pass_hands(self) -> None:
    """Pass hands to the next player (card drafting)."""
    temp_hands = {}
    for i in range(self.num_players):
        next_player = (i + 1) % self.num_players
        temp_hands[next_player] = self.hands[i]
    self.hands = temp_hands
```

### 2. Complex Scoring Rules
```python
# Sashimi: 3 = 10 points
scores[player_idx] += (sashimi_count // 3) * 10

# Dumpling: 1,3,6,10,15
dumpling_points = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}
scores[player_idx] += dumpling_points.get(dumpling_count, 15)

# Maki: Most and second most
# (Complex majority scoring logic)
```

### 3. Multi-Round Structure
```python
# 3 rounds with persistent pudding tracking
self.state.total_rounds = 3
self.pudding_counts: dict[int, int]  # Persists across rounds
```

### 4. Set Collection
```python
# Cards have different point values and combinations
- Tempura (pairs)
- Sashimi (triplets)
- Dumplings (more is better)
- Nigiri with Wasabi multiplier
```

### 5. Simultaneous Play Simulation
```python
# All players "simultaneously" choose cards
self.state.waiting_for_players = set(range(num_players))
# Once all played, pass hands
```

## Card Distribution

**Total: 108 cards**

| Card | Count | Scoring |
|------|-------|---------|
| Maki Roll (1) | 6 | Part of maki majority |
| Maki Roll (2) | 12 | Part of maki majority |
| Maki Roll (3) | 8 | Part of maki majority |
| Tempura | 14 | 2 = 5 pts |
| Sashimi | 14 | 3 = 10 pts |
| Dumpling | 14 | 1/2/3/4/5+ = 1/3/6/10/15 pts |
| Egg Nigiri | 5 | 1 pt (3 with wasabi) |
| Salmon Nigiri | 10 | 2 pts (6 with wasabi) |
| Squid Nigiri | 5 | 3 pts (9 with wasabi) |
| Wasabi | 6 | Triples next nigiri |
| Chopsticks | 4 | Take 2 cards next turn |
| Pudding | 10 | Most/least at game end |

## Example Output

```
======================================================================
    SUSHI GO!
======================================================================

Round 2/3

Current Scores:
  Player 1    18 pts  (7 + 11)  🍮×2
  Player 2    15 pts  (8 + 7)   🍮×1
  Player 3    21 pts  (9 + 12)  🍮×3
  Player 4    14 pts  (6 + 8)   🍮×0

Collections This Round:

Player 1's Collection:
  Sashimi ×3
  Maki Roll (2) ×2
  Pudding

Player 2's Collection:
  Tempura ×2
  Egg Nigiri
  Dumpling ×2

[Player 3] played: Squid Nigiri
  Reasoning: I have Wasabi, so this Squid is worth 9 points!

---

ROUND 2 RESULTS

Round Scores:
  Player 1   earned 11 pts  (Total: 18)
  Player 2   earned  7 pts  (Total: 15)
  Player 3   earned 12 pts  (Total: 21)
  Player 4   earned  8 pts  (Total: 14)

======================================================================
```

## Why Sushi Go!?

Sushi Go! demonstrates several excellent game design concepts:

- **Simple rules, deep strategy**: Easy to learn, hard to master
- **Card drafting**: Classic "pick and pass" mechanic
- **Simultaneous play**: No downtime, everyone plays at once
- **Set collection**: Multiple paths to victory
- **Push your luck**: Go for big combos or play it safe?
- **Reading opponents**: Watch what they're collecting
- **Long-term planning**: Pudding scoring rewards thinking ahead

The boardgamepy implementation handles complex scoring rules, card drafting mechanics, and multi-round gameplay with persistent state!

## Advanced Variants

**Party Mode**: Play 5 players for maximum chaos
**Quick Game**: Play 2 rounds instead of 3
**Expert Challenge**: Add house rules or custom cards

## Tips for AI Performance

The AI agents are guided to:
- Prioritize high-value sets (Sashimi, Wasabi+Nigiri)
- Complete partial sets rather than starting new ones
- Compete for maki when feasible
- Balance pudding with round scoring
- Adapt strategy based on hand size and round number

Watch the AI make strategic decisions in real-time!
