# BoardGamePy Quick Start

## 🎮 Run a Game

```bash
# TicTacToe (simple, fast)
cd examples/tictactoe
python3 main.py

# Subtract-a-Square (mathematical strategy)
cd examples/subtract-a-square
python3 main.py

# Codenames (complex, team-based)
cd examples/codenames
python3 main.py
```

## 📊 View Game Logs

```bash
# Go to project root first
cd /home/fathiyul/01-project/boardgame

# List all recent games
python view_logs.py list

# List last 5 TicTacToe games
python view_logs.py list TicTacToe 5

# Show detailed game info (copy game_id from list command)
python view_logs.py details abc-123-uuid-here

# Show statistics
python view_logs.py stats
python view_logs.py stats Codenames

# Export for fine-tuning (creates training_data.json)
python view_logs.py export TicTacToe 1000
```

## ⚙️ Configuration

Edit `.env` in project root:

```env
# Enable/disable logging
ENABLE_LOGGING=true

# MongoDB connection
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=boardgamepy_logs

# AI model defaults (used by all games)
OPENAI_MODEL=gpt-4o-mini
OPENROUTER_MODEL=google/gemini-2.5-flash

# Your API keys
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-v1-...
```

## 🗄️ MongoDB Setup

```bash
# Start MongoDB with Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Check if running
docker ps | grep mongodb

# Stop MongoDB
docker stop mongodb

# Start again later
docker start mongodb
```

## 📚 Documentation

- **README.md** - Full framework documentation
- **LOGGING_GUIDE.md** - Complete logging system guide
- **examples/*/README.md** - Game-specific documentation

## 🔍 Direct MongoDB Queries

```python
from pymongo import MongoClient

c = MongoClient('mongodb://localhost:27017')
db = c['boardgamepy_logs']

# Count games
print(f"Total games: {db.games.count_documents({})}")

# List all game types
for game in db.games.distinct('game_name'):
    print(game)

# See recent games
for game in db.games.find().sort('timestamp_start', -1).limit(5):
    print(f"{game['game_name']}: {game['outcome']}")
```

## 🎯 Common Tasks

### Change AI Model for a Specific Game

Create `examples/tictactoe/.env`:
```env
OPENAI_MODEL=gpt-4o  # Override root config
```

### Disable Logging Temporarily

Edit root `.env`:
```env
ENABLE_LOGGING=false
```

### Export Training Data

```bash
# Export all TicTacToe games
python view_logs.py export TicTacToe

# Export with limit
python view_logs.py export Codenames 500

# Output: training_data.json
```

### View LLM Reasoning

```bash
# Show detailed game (includes AI reasoning for each turn)
python view_logs.py details <game-id>
```

## 🚀 Next Steps

1. Run a few games with logging enabled
2. Use `python view_logs.py list` to see your games
3. Export data for fine-tuning
4. Build your own game using the framework!
