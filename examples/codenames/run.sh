#!/bin/bash
# Helper script to run Codenames example

cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "Please create a .env file with your API keys:"
    echo ""
    echo "cp .env.example .env"
    echo ""
    echo "Then edit .env and add your keys:"
    echo "  OPENAI_API_KEY=your_key_here"
    echo "  OPENROUTER_API_KEY=your_key_here"
    echo ""
    exit 1
fi

# Run the game
python main.py "$@"
