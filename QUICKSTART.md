# BoardGamePy Quick Start

## 🎮 Run a Game

```bash
# RPS (simple, fast)
cd examples/rps
python3 main.py

# Wythoff (mathematical strategy)
cd examples/wythoff
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

# List last 5 Coup games
python view_logs.py list Coup 5

# Show detailed game info (copy game_id from list command)
python view_logs.py details abc-123-uuid-here

# Show statistics
python view_logs.py stats
python view_logs.py stats Codenames

# Export for fine-tuning (creates training_data.json)
python view_logs.py export Coup 1000
```

## ⚙️ Configuration

Edit `.env` in project root:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=boardgamepy_logs

# Logging Configuration
ENABLE_LOGGING=false
LOG_LEVEL=INFO

# OpenRouter API Key (required)
OPENROUTER_API_KEY=your-openrouter-api-key-here

# LLM Model Configuration
# DEFAULT_MODEL is used for all players unless overridden per-player
DEFAULT_MODEL=google/gemini-2.5-flash

# Per-player model overrides (optional)
# If not set, uses DEFAULT_MODEL
# MODEL_PLAYER_1=google/gemini-2.5-flash
# MODEL_PLAYER_2=anthropic/claude-sonnet-4.5
# MODEL_PLAYER_3=openai/gpt-4o-mini
# MODEL_PLAYER_4=x-ai/grok-4.1-fast

# LangSmith Tracing
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=boardgamepy
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
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

Create `examples/coup/.env`:
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
# Export all Coup games
python view_logs.py export Coup

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
