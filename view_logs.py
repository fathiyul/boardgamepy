"""View logged games from MongoDB."""

import sys
from datetime import datetime
from boardgamepy.logging.query import GameDataQuery


def print_recent_games(game_name=None, limit=10):
    """
    Print recent games (newest first).

    Note: This function is now mostly replaced by the inline logic in main()
    which supports slicing. Kept for backwards compatibility.
    """
    query = GameDataQuery()
    games = query.get_recent_games(game_name=game_name, limit=limit)

    if not games:
        print("No games found!")
        return

    print(f"\n{'=' * 80}")
    print(f"Recent Games ({len(games)} found, newest first)")
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

    print(f"Tip: Use 'python view_logs.py details 1' to view the most recent game")
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

    # Display initial board if available
    if game.get("initial_board"):
        print(f"\nInitial Board Setup:")
        initial_board = game["initial_board"]

        # Filter out __objclass__ (internal Python metadata)
        def clean_board(obj):
            if isinstance(obj, dict):
                return {k: clean_board(v) for k, v in obj.items() if k != "__objclass__"}
            elif isinstance(obj, list):
                return [clean_board(item) for item in obj]
            return obj

        initial_board = clean_board(initial_board)

        # Pretty print the board structure
        import json

        board_str = json.dumps(initial_board, indent=2, default=str)

        # For large boards, show summary
        if len(board_str) > 1000:
            print(f"  (Board data: {len(board_str)} chars - showing summary)")
            # Try to show key stats
            if "cards" in initial_board:
                print(f"  Total cards: {len(initial_board['cards'])}")
            print(f"  Use MongoDB viewer or export to see full details")
        else:
            # Show full board for smaller boards
            for line in board_str.split("\n"):
                print(f"  {line}")

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

        # Show board state (per-round configuration)
        if turn.get("board_before"):
            board = turn["board_before"]

            # Smart display based on board content
            if isinstance(board, dict):
                # RPS - show current effects
                if "current_effects" in board:
                    print(f"  Round Effects:")
                    for choice, effect in board["current_effects"].items():
                        win_pts = effect.get("win_points", 0)
                        loss_pts = effect.get("loss_penalty_points", 0)
                        loss_hp = effect.get("loss_penalty_health", 0)
                        penalty = (
                            f"{loss_pts}pt"
                            if loss_pts
                            else (f"{loss_hp}hp" if loss_hp else "0")
                        )
                        print(f"    {choice}: +{win_pts}/{penalty}")

                # Wavelength - show target and spectrum
                elif "target_center" in board and "current_spectrum" in board:
                    spectrum = board.get("current_spectrum", {})
                    target = board.get("target_center")
                    dial = board.get("dial_position")
                    print(
                        f"  Spectrum: [{spectrum.get('left')}] ←→ [{spectrum.get('right')}]"
                    )
                    print(f"  Target: {target}" + (f", Dial: {dial}" if dial else ""))

                # Coup - show private influence cards
                elif "influence" in board and "coins" in board:
                    print(f"  Private Cards:")
                    for player_idx, cards in board["influence"].items():
                        if cards:
                            card_names = []
                            for card in cards:
                                char_name = card.get("type", {}).get("char_name", "?")
                                revealed = card.get("revealed", False)
                                status = "(revealed)" if revealed else ""
                                card_names.append(f"{char_name}{status}")
                            coins = board["coins"].get(player_idx, 0)
                            print(f"    Player {int(player_idx)+1}: {', '.join(card_names)} | {coins} coins")

                # Love Letter - show private hands
                elif "hands" in board and "deck" in board and "eliminated" in board:
                    print(f"  Private Cards:")
                    for player_idx, cards in board["hands"].items():
                        if cards:
                            card_names = [c.get("type", {}).get("name", "?") for c in cards]
                            eliminated = int(player_idx) in board.get("eliminated", [])
                            status = " (eliminated)" if eliminated else ""
                            print(f"    Player {int(player_idx)+1}: {', '.join(card_names)}{status}")
                    deck_size = len(board.get("deck", []))
                    print(f"  Deck: {deck_size} cards remaining")

                # Incan Gold - show temple path
                elif "temple_path" in board and "player_gems" in board:
                    current = board.get("current_card")
                    if current:
                        card_type = current.get("type", "?")
                        value = current.get("value", 0)
                        print(f"  Current Card: {card_type} ({value})")
                    in_players = sum(1 for p in board.get("in_temple", []) if p)
                    print(f"  In Temple: {in_players} players")

                # Sushi Go - show private hands
                elif "player_hands" in board:
                    print(f"  Private Hands:")
                    for player_idx, cards in board["player_hands"].items():
                        if cards:
                            card_names = [c.get("type", "?") for c in cards]
                            print(f"    Player {int(player_idx)+1}: {', '.join(card_names)}")

                # Codenames - show card count summary
                elif "cards" in board:
                    cards = board["cards"]
                    hidden = sum(
                        1 for c in cards.values() if c.get("state") == "Hidden"
                    )
                    revealed = len(cards) - hidden
                    print(f"  Cards: {hidden} hidden, {revealed} revealed")

                # Generic - show compact JSON for small boards
                elif len(str(board)) < 200:
                    import json

                    print(f"  Board: {json.dumps(board, default=str)}")

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
            "  python view_logs.py list [limit|game_name] [limit] - List recent games"
        )
        print(
            "  python view_logs.py details <index|game_id>        - Show game details"
        )
        print("  python view_logs.py stats [game_name]              - Show statistics")
        print(
            "  python view_logs.py export [game_name] [limit]     - Export for fine-tuning"
        )
        print("\nExamples:")
        print(
            "  python view_logs.py list                           - Last 10 games (newest first)"
        )
        print("  python view_logs.py list 50                        - Last 50 games")
        print("  python view_logs.py list 10:30                     - Games 10-30")
        print("  python view_logs.py list 20:                       - Games 20 to end")
        print("  python view_logs.py list :-10                      - Last 10 games")
        print("  python view_logs.py list -5:                       - Last 5 games")
        print(
            "  python view_logs.py list Codenames                 - Last 10 Codenames games"
        )
        print(
            "  python view_logs.py list Codenames 50              - Last 50 Codenames games"
        )
        print(
            "  python view_logs.py list Codenames :-10            - Last 10 Codenames games"
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
            # Parse arguments intelligently:
            # list -> last 10 games (newest first)
            # list 50 -> last 50 games (newest first)
            # list 10:30 -> games 10 to 30 (newest first, 1-indexed)
            # list -10: -> last 10 games
            # list :-10 -> all except last 10
            # list Codenames -> last 10 Codenames games
            # list Codenames 50 -> last 50 Codenames games
            # list Codenames 10:30 -> Codenames games 10 to 30
            game_name = None
            limit = 10
            start_idx = None
            end_idx = None

            if len(sys.argv) > 2:
                arg = sys.argv[2]

                # Check if it's a slice (contains ':')
                if ":" in arg:
                    parts = arg.split(":")
                    start_idx = int(parts[0]) if parts[0] else None
                    end_idx = int(parts[1]) if parts[1] else None
                    # Fetch enough to cover the range (estimate)
                    # For negative indices, we need to fetch more
                    if start_idx and start_idx < 0:
                        limit = abs(start_idx) + 100
                    elif end_idx and end_idx < 0:
                        limit = abs(end_idx) + 100
                    elif end_idx:
                        limit = end_idx
                    else:
                        limit = 1000  # Fetch a lot for open-ended ranges
                else:
                    # Check if first arg is a number
                    try:
                        limit = int(arg)
                        # It's a number, so just a limit with no game name
                    except ValueError:
                        # It's not a number, so it's a game name
                        game_name = arg
                        # Check for limit or slice as third arg
                        if len(sys.argv) > 3:
                            arg3 = sys.argv[3]
                            if ":" in arg3:
                                parts = arg3.split(":")
                                start_idx = int(parts[0]) if parts[0] else None
                                end_idx = int(parts[1]) if parts[1] else None
                                # Same logic for limit estimation
                                if start_idx and start_idx < 0:
                                    limit = abs(start_idx) + 100
                                elif end_idx and end_idx < 0:
                                    limit = abs(end_idx) + 100
                                elif end_idx:
                                    limit = end_idx
                                else:
                                    limit = 1000
                            else:
                                limit = int(arg3)

            # Fetch games (already sorted newest first)
            query = GameDataQuery()
            games = query.get_recent_games(game_name=game_name, limit=limit)

            # Apply slice if specified
            if start_idx is not None or end_idx is not None:
                # Convert to Python slice (0-indexed)
                # User indices are 1-indexed, so convert: 1 -> 0, 10 -> 9, etc.
                start = (start_idx - 1) if (start_idx and start_idx > 0) else start_idx
                end = end_idx if (end_idx is None or end_idx < 0) else end_idx

                games = games[start:end]

                # Figure out what the actual starting index is for display
                if start_idx and start_idx > 0:
                    display_start = start_idx
                elif start_idx and start_idx < 0:
                    # Negative index - calculate actual position
                    display_start = len(games) + start_idx + 1 if games else 1
                else:
                    display_start = 1
            else:
                display_start = 1

            # Print the games
            if not games:
                print("No games found!")
            else:
                print(f"\n{'=' * 80}")
                print(f"Recent Games ({len(games)} found, newest first)")
                if start_idx is not None or end_idx is not None:
                    range_str = f"{start_idx or ''}:{end_idx or ''}"
                    print(f"Showing slice: [{range_str}]")
                print(f"{'=' * 80}\n")

                for idx, game in enumerate(games, display_start):
                    print(f"[{idx}] Game ID: {game['game_id']}")
                    print(f"    Name: {game['game_name']}")
                    print(f"    Started: {game['timestamp_start']}")
                    if game.get("outcome"):
                        outcome = game["outcome"]
                        print(f"    Winner: {outcome.get('winner', 'N/A')}")
                        print(f"    Turns: {outcome.get('total_turns', 'N/A')}")
                        print(
                            f"    Duration: {outcome.get('duration_seconds', 'N/A'):.1f}s"
                        )
                    print()

                print(
                    f"Tip: Use 'python view_logs.py details 1' to view the most recent game"
                )
                print()

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
