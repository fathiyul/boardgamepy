# Wavelength

A creative party game of communication and deduction implemented using the `boardgamepy` framework. This showcases the framework's ability to handle abstract concepts, creative AI prompts, and spectrum-based gameplay.

**Features:**
- ✅ 50+ spectrum cards
- ✅ Creative clue generation
- ✅ Team-based gameplay
- ✅ Spectrum-based scoring
- ✅ Multi-phase rounds
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

Wavelength is a social guessing game where players work together to read each other's minds. One player, the Psychic, gives a clue to help their team guess where a hidden target falls on a spectrum between two extremes. The opposing team then predicts whether the guess is to the left or right of the actual target.

## Game Rules

### Setup
- Players divided into 2 teams (even number of players, 4-12)
- First team to reach 10 points wins
- Each round has 4 phases

### Phases

**1. Psychic Gives Clue**
- A random spectrum card is drawn (e.g., "Cold ← → Hot")
- The Psychic sees a hidden target position (0-100 on the spectrum)
- The Psychic gives a creative clue that hints at the target position
  - Example: For "Cold ← → Hot" with target at 15, clue might be "Antarctica"

**2. Team Guesses Position**
- The Psychic's team discusses the clue
- They guess where on the spectrum (0-100) the target is
- 0 = far left extreme, 50 = middle, 100 = far right extreme

**3. Opponent Predicts Direction**
- The opposing team sees the clue and the guess
- They predict if the guess is to the LEFT or RIGHT of the actual target

**4. Reveal & Scoring**
- The hidden target is revealed
- Points awarded based on accuracy:
  - **Bulls-eye (±5)**: 4 points
  - **Close (±10)**: 3 points
  - **Medium (±20)**: 2 points
  - **Far**: 0 points
- If opponent's prediction was correct: -1 point
- Minimum 0 points per round

### Winning
- First team to 10 points wins!

## Example Round

**Spectrum**: "Bad ← → Good"
**Hidden Target**: 75
**Psychic's Clue**: "Getting a compliment"
**Team's Guess**: 72
**Opponent Predicts**: "right" (thinks they're to the right of target)

**Result**:
- Target was at 75, guess was at 72
- Distance: 3 units (bulls-eye!)
- Base points: 4
- Opponent predicted "right" but guess was to the LEFT (incorrect)
- **Final Score**: 4 points

## Strategy Tips

### For Psychics
- Be creative but clear
- Give examples that precisely match the target position
- Don't be too obvious (e.g., "middle" for position 50)
- Think about what's relatable and universal

**Good Clues**:
- "Cold ← → Hot" target 85: "Desert" or "Hot chocolate"
- "Overrated ← → Underrated" target 25: "Avengers movies"
- "Boring ← → Exciting" target 60: "Mini golf"

### For Guessers
- Think about where the clue naturally falls
- Consider the extremes and what's between them
- Use intuition - don't overthink!
- Remember bulls-eye is only ±5 units

### For Opponents
- Analyze where the clue SHOULD be
- Compare to where they guessed
- If their guess seems off, predict the direction
- Even wrong guesses can earn points if you're strategic

## Running the Game

```bash
# Set your API key
export OPENROUTER_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"

# Run the game
python examples/wavelength/main.py
```

## Customizing Player Count

Edit `config.py` to change the number of players:

```python
self.num_players = 4  # Default (must be even, 4-12)
# Try:
# self.num_players = 6  # 3 vs 3
# self.num_players = 8  # 4 vs 4
```

## Implementation Files

- `spectrums.py` - 50+ spectrum cards (Cold↔Hot, Bad↔Good, etc.)
- `board.py` - Board managing spectrum, target, dial, and scoring
- `state.py` - Game state with phases and team scores
- `actions.py` - Three actions (GiveClue, GuessPosition, PredictDirection)
- `prompts.py` - Three role-specific prompt builders (Psychic, Guesser, Opponent)
- `game.py` - WavelengthGame with team and role management
- `ui.py` - Terminal UI with spectrum visualization
- `main.py` - Entry point with phase-based game loop
- `config.py` - Configuration and API keys

## Framework Features Demonstrated

### 1. Abstract Spectrum Representation
```python
@dataclass
class Spectrum:
    left: str  # Left extreme (0)
    right: str  # Right extreme (100)

# 50+ pre-defined spectrums
SPECTRUM_CARDS = [
    Spectrum("Cold", "Hot"),
    Spectrum("Bad", "Good"),
    # ...
]
```

### 2. Role-Based Information Hiding
```python
def get_view(self, context: ViewContext) -> str:
    # Psychic sees: target position
    # Guessers see: clue only
    # Opponents see: clue + guess
    # After reveal: everyone sees everything
```

### 3. Phase-Based Gameplay
```python
Phase = Literal["psychic_clue", "team_guess", "opponent_predict", "reveal"]

# Different prompts and actions per phase
```

### 4. Creative AI Prompts
```python
# Psychic prompt encourages creativity
"Give an example that falls at the target position on the spectrum"

# Guesser prompt encourages interpretation
"Think about where the clue falls on the spectrum"

# Opponent prompt encourages strategic prediction
"Predict if their guess is too high or too low"
```

### 5. Spectrum Visualization
```ascii
Spectrum: Cold ← → Hot
0───────────────🎯──────────📍───────────────100
    🎯 = Target   📍 = Your Guess
```

## Spectrum Cards

The game includes 50+ spectrum cards across categories:

**Temperature & Physical**: Cold↔Hot, Soft↔Hard, Slow↔Fast
**Quality & Opinion**: Bad↔Good, Boring↔Exciting, Overrated↔Underrated
**Morality & Ethics**: Evil↔Good, Selfish↔Selfless
**Time**: Old↔New, Past↔Future, Ancient↔Modern
**Complexity**: Simple↔Complex, Easy↔Difficult
**Cost & Value**: Cheap↔Expensive, Worthless↔Valuable
**Social**: Introverted↔Extroverted, Private↔Public
**Emotion**: Sad↔Happy, Calm↔Angry, Fearful↔Brave
**Aesthetics**: Ugly↔Beautiful, Messy↔Neat
**Food & Taste**: Bland↔Flavorful, Bitter↔Sweet

## Example Output

```
======================================================================
    WAVELENGTH
======================================================================

Round 3
Scores:
  ► Team 1   ⭐⭐⭐⭐ (4/10)
  Team 2     ⭐⭐⭐ (3/10)

Spectrum:
  Cold                         ← → Hot
  0                            50                            100

Phase: PSYCHIC GIVES CLUE
  Team 1's Psychic is giving a clue...

[Psychic] Giving clue...
  Clue: "Ice cream"
  Reasoning: Target is at 25, which is moderately cold. Ice cream is a perfect example.

---

Phase: TEAM GUESSES POSITION
  Team 1 is interpreting the clue...
  Clue: "Ice cream"

[Team] Making guess...
  Position: 28
  Reasoning: Ice cream is cold but not freezing. Around 25-30 feels right.

---

Phase: OPPONENT PREDICTS
  Team 2 is predicting left or right...
  Clue: "Ice cream"
  Team 1's Guess: 28

[Opponent] Predicting...
  Prediction: RIGHT
  Reasoning: Ice cream is pretty cold, probably around 20-25. Guess of 28 might be slightly high.

---

ROUND RESULT

Spectrum Visualization:
  Cold                         | Hot
  0─────────🎯──📍──────────────────────────────────────────100
  🎯 = Target Position    📍 = Team's Guess

Scoring:
  Target was at: 25
  Team 1 guessed: 28
  Distance: 3 units

  Base points: 4 (Bulls-eye!)
  Team 2 predicted correctly: -1 point
  Final points for Team 1: 3
```

## Why Wavelength?

Wavelength demonstrates several interesting aspects of boardgamepy:

- **Creative AI Interaction**: Psychics give creative clues, guessers interpret them
- **Abstract Concepts**: Spectrums represent abstract ideas (good/bad, hot/cold)
- **Multi-Phase Gameplay**: Different roles and actions per phase
- **Continuous Spectrum**: Not discrete positions, but 0-100 scale
- **Team Dynamics**: Cooperation within teams, competition between teams
- **Strategic Prediction**: Opponents try to outsmart the guessing team

The AI agents demonstrate impressive creativity in giving and interpreting clues for abstract concepts!

## Mathematical Details

**Scoring Zones**:
- Bulls-eye: distance ≤ 5 (4 points)
- Close: distance ≤ 10 (3 points)
- Medium: distance ≤ 20 (2 points)
- Far: distance > 20 (0 points)

**Opponent Bonus**:
- Correct prediction: -1 from team's score
- Incorrect prediction: no effect
- Minimum score per round: 0 (can't go negative)

**Target Generation**:
- Random position between 10-90 (avoids extreme edges)
- Target range: ±5 from center (bulls-eye zone)
