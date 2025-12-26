"""View logged games from MongoDB."""

import sys
from datetime import datetime
from boardgamepy.logging.query import GameDataQuery


def print_recent_games(game_name=None, limit=10):
    """Print recent games."""
    query = GameDataQuery()
    games = query.get_recent_games(game_name=game_name, limit=limit)

    if not games:
        print("No games found!")
        return

    print(f"\n{'=' * 80}")
    print(f"Recent Games ({len(games)} found)")
    print(f"{'=' * 80}\n")

    for idx, game in enumerate(games, 1):
        print(f"[{idx}] Game ID: {game['game_id']}")
        print(f"    Name: {game['game_name']}")
        print(f"    Started: {game['timestamp_start']}")
        if game.get("outcome"):
            outcome = game["outcome"]
            print(f"    Winner: {outcome.get('winner', 'N/A')}")
            print(f"    Turns: {outcome.get('total_turns', 'N/A')}")
            print(f"    Duration: {outcome.get('duration_seconds', 'N/A'):.1f}s")
        print()

    print(f"Tip: Use 'python view_logs.py details {len(games)}' to view the last game")
    print()


def print_game_details(game_id_or_index):
    """Print detailed game information.

    Args:
        game_id_or_index: Either a game_id string or an integer index from list
    """
    query = GameDataQuery()

    # Check if it's an index (integer)
    try:
        index = int(game_id_or_index)
        # It's an index - get recent games and select by index
        games = query.get_recent_games(limit=100)  # Get more to ensure we have enough
        if index < 1 or index > len(games):
            print(f"Index {index} out of range! (1-{len(games)} available)")
            return
        game_id = games[index - 1]["game_id"]
        print(f"Using game at index [{index}]: {game_id}\n")
    except ValueError:
        # It's a game_id string
        game_id = game_id_or_index

    # Get game
    game = query.get_game(game_id)
    if not game:
        print(f"Game {game_id} not found!")
        return

    # Get turns
    turns = query.get_turns(game_id)

    print(f"\n{'=' * 80}")
    print(f"Game Details: {game['game_name']}")
    print(f"{'=' * 80}\n")

    print(f"Game ID: {game['game_id']}")
    print(f"Started: {game['timestamp_start']}")
    print(f"Players: {len(game['players'])}")
    for p in game["players"]:
        print(f"  - {p['name']} ({p['team']}, {p['agent_type']})")

    if game.get("outcome"):
        outcome = game["outcome"]
        print(f"\nOutcome:")
        print(f"  Winner: {outcome.get('winner', 'N/A')}")
        print(f"  Total Turns: {outcome.get('total_turns', 'N/A')}")
        print(f"  Duration: {outcome.get('duration_seconds', 'N/A'):.1f}s")

    print(f"\n{'=' * 80}")
    print(f"Turns ({len(turns)} total)")
    print(f"{'=' * 80}\n")

    for turn in turns:
        print(f"Turn {turn['turn_number']}: {turn['player']['name']}")
        print(f"  Action: {turn['action']['type']}")
        print(f"  Params: {turn['action']['params']}")

        if turn.get("llm_call") and turn["llm_call"].get("response"):
            response = turn["llm_call"]["response"]
            if "reasoning" in response:
                print(f"  Reasoning: {response['reasoning'][:100]}...")
            print(f"  Latency: {turn['llm_call']['metadata']['latency_ms']:.0f}ms")
        print()


def print_stats(game_name=None):
    """Print game statistics."""
    query = GameDataQuery()
    stats = query.get_game_stats(game_name=game_name)

    print(f"\n{'=' * 80}")
    print(f"Game Statistics" + (f" - {game_name}" if game_name else ""))
    print(f"{'=' * 80}\n")

    print(f"Total Games: {stats['total_games']}")
    print(f"Average Turns: {stats['avg_turns']:.1f}")
    print(f"Average Duration: {stats['avg_duration']:.1f}s")
    print(f"Max Turns: {stats['max_turns']}")
    print(f"Min Turns: {stats['min_turns']}")
    print()


def export_for_finetuning(game_name=None, limit=100, output_file="training_data.json"):
    """Export LLM interactions for fine-tuning."""
    import json

    query = GameDataQuery()
    data = query.export_for_finetuning(game_name=game_name, limit=limit)

    if not data:
        print("No LLM interaction data found!")
        return

    # Convert datetime objects to strings for JSON serialization
    def serialize_dates(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2, default=serialize_dates)

    print(f"\nExported {len(data)} LLM interactions to {output_file}")
    print(f"Format: [{{ messages: [...], response: {{...}}, metadata: {{...}} }}, ...]")


def main():
    """Main CLI."""
    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "  python view_logs.py list [game_name] [limit]       - List recent games"
        )
        print(
            "  python view_logs.py details <index|game_id>        - Show game details"
        )
        print("  python view_logs.py stats [game_name]              - Show statistics")
        print(
            "  python view_logs.py export [game_name] [limit]     - Export for fine-tuning"
        )
        print("\nExamples:")
        print("  python view_logs.py list                           - Last 10 games")
        print(
            "  python view_logs.py list Codenames 5               - Last 5 Codenames games"
        )
        print(
            "  python view_logs.py details 1                      - Latest game (by index)"
        )
        print(
            "  python view_logs.py details abc-123-uuid           - Specific game (by ID)"
        )
        print("  python view_logs.py stats Codenames                - Codenames stats")
        print(
            "  python view_logs.py export Codenames 1000          - Export 1000 turns"
        )
        return

    command = sys.argv[1]

    try:
        if command == "list":
            game_name = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            print_recent_games(game_name, limit)

        elif command == "details":
            if len(sys.argv) < 3:
                print("Error: game_id or index required")
                print("Example: python view_logs.py details 1")
                print("Example: python view_logs.py details abc-123-uuid")
                return
            game_id_or_index = sys.argv[2]
            print_game_details(game_id_or_index)

        elif command == "stats":
            game_name = sys.argv[2] if len(sys.argv) > 2 else None
            print_stats(game_name)

        elif command == "export":
            game_name = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
            export_for_finetuning(game_name, limit)

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
