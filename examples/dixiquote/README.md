# DixiQuote

*A storytelling game about how moments are remembered, not how they happened.*

**Game designed by Fathiyul Fahmi**

---

## Overview

**DixiQuote** is a word-based storytelling game inspired by **Dixit**. Instead of images, players use **situation cards**—short narrative descriptions of events. One player (the Storyteller) provides a **poetic, quote-like clue**, and the others try to match that quote to a situation in a way that is suggestive, but not obvious.

The goal is not to be correct, but to be *interpretable*.

---

## Game Components

This implementation includes:

- **80 Situation Cards** spanning fantasy, sci-fi, surreal, and historical themes
- **Phase-based gameplay** with automated turn management
- **AI players** using LLM agents to make strategic decisions
- **Scoring system** that rewards interpretable ambiguity

---

## How to Play

### Setup

- 3–8 players
- Each player starts with 6 situation cards
- One player is chosen as the Storyteller

### Round Structure

Each round consists of five phases:

1. **Choose a Situation** — The Storyteller secretly selects one situation card from their hand
2. **Give a Quote** — The Storyteller writes a quote-like clue inspired by the chosen situation
3. **Submit Situations** — All other players select one situation card from their hand that fits the clue
4. **Reveal and Vote** — All submitted situations (including the Storyteller's) are shuffled and revealed. Each non-Storyteller player votes for the situation they believe best matches the quote. Players may not vote for their own card.
5. **Scoring** — Points are awarded based on voting results

### Scoring

**For Situation Cards:**
- **1 point** if the card receives some but not all votes
- **0 points** if the card receives zero votes
- **-1 point** if the card receives all votes (too obvious - penalty)

**For Voting:**
- **+1 bonus point** for each player who correctly votes for the Storyteller's card

**For the Storyteller:**
- **1 point** if at least two different cards receive votes, including the Storyteller's own card
- **0 points** otherwise

### End of Round

- Each player draws one card to return to 6 cards in hand
- The Storyteller role passes clockwise
- A new round begins

### Invalid Action Penalty

To keep the game moving when playing with AI agents:
- Players track consecutive invalid actions during each phase
- After **3 consecutive invalid actions**:
  - Player loses **1 point** (minimum score 0)
  - Turn is automatically skipped for that phase
- Counter resets on valid action or new phase
- If all other players are skipped, Storyteller gets the 3-point bonus automatically

### End of Game

The game ends when **any** of these conditions are met:
- A player reaches the **target score** (default: 20 points)
- The **maximum number of rounds** is reached (default: 15 rounds)
- The situation deck runs out

The player with the highest score wins.

---

## Implementation Details

This implementation uses the `boardgamepy` framework with:

- **State Management** (`state.py`) — Tracks game phase, submissions, votes, scores, and penalties
- **Actions** (`actions.py`) — Four main actions: ChooseSituation, GiveQuote, SubmitSituation, Vote
- **Game Logic** (`game.py`) — Manages player hands, deck, scoring calculations, and win conditions
- **AI Prompts** (`prompts.py`) — Role-specific prompts for Storyteller and other players
- **Terminal UI** (`ui.py`) — Colorful terminal rendering with:
  - Player index tracking (P-0, P-1, etc.)
  - Color-coded vote counts and points
  - Detailed voting breakdown (who voted for whom)
  - Penalty notifications
  - Phase-aware hand display
- **Game Runner** (`main.py`) — Custom runner with phase-based agent switching and CLI argument support
- **Invalid Action Handling** — Automatic penalty and skip system to prevent game stalls

---

## Running the Game

### Prerequisites

```bash
# Install boardgamepy
pip install boardgamepy

# Set up your .env file with API keys
cp ../.env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Run

Default settings (4 players, target 20, max 15 rounds):
```bash
python main.py
```

Custom game settings via CLI:
```bash
# Quick game: first to 5 points or 4 rounds
python main.py --target 5 --max-rounds 4

# 6 players, first to 30 points
python main.py --num-players 6 --target 30

# Full options
python main.py --num-players 4 --target-score 20 --max-rounds 15
```

### Configuration

Default settings in `config.py`:
- `num_players` = 4 (3-8 players supported)
- `target_score` = 20 (score to win)
- `max_rounds` = 15 (maximum rounds)
- API keys: `OPENROUTER_API_KEY`

**CLI arguments override `config.py` defaults.**

---

## Game Design Philosophy

DixiQuote rewards players who understand how others interpret language:

- **Overly literal clues** result in all votes going to one card, causing that card to lose a point
- **Too obscure clues** result in zero points for everyone
- **The most successful quotes** create multiple plausible readings, earning points for the storyteller and several situation cards

The game is about the distance between what happens and how it is remembered.

---

## Files

```
dixiquote/
├── README.md                                    # This file
├── dixiquote_rulebook.md                        # Original game rules
├── dixiquote_situation_deck_revised_80_cards.md # Situation card deck
├── data.py                                      # Load situation cards
├── state.py                                     # Game state
├── actions.py                                   # Game actions
├── game.py                                      # Core game logic
├── prompts.py                                   # AI prompt builders
├── ui.py                                        # Terminal UI
├── config.py                                    # Configuration
└── main.py                                      # Game runner
```

---

## Example Round

**Storyteller's Situation:**
> "The dragon circles once, then leaves without attacking."

**Quote:**
> "Power does not always need to be proven."

**Submitted Situations:**
- "The crowd cheers as the wrong name is announced."
- "The throne remains empty during the celebration."
- "A sword that has never been drawn is finally removed from its sheath."

**Votes:**
- Dragon situation → 2 votes
- Throne situation → 1 vote
- Sword situation → 0 votes

**Scoring:**
- Dragon card scores **1 point** (2 votes)
- Throne card scores **1 point** (1 vote)
- Sword card scores **0 points** (0 votes)
- Players who voted for Dragon card earn **+1 bonus point** for correct guess
- Storyteller scores **1 point** (at least 2 cards voted, including their own)

---

## Credits

- **Game Design**: Fathiyul Fahmi
- **Inspired by**: Dixit (Jean-Louis Roubira)
- **Implementation**: boardgamepy framework

---

*DixiQuote is a game about the distance between what happens and how it is remembered.*
