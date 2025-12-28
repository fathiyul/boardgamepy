"""Sushi Go! game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import SushiGoGame



def render_header(game: "SushiGoGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_MAGENTA}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}    SUSHI GO!{term.RESET}")
    print(f"{term.BOLD}{term.FG_MAGENTA}{'=' * 70}{term.RESET}\n")


def render_round_info(game: "SushiGoGame") -> None:
    """Render round and score information."""
    print(f"{term.BOLD}Round {game.state.current_round}/{game.state.total_rounds}{term.RESET}")
    print()

    print(f"{term.BOLD}Current Scores:{term.RESET}")
    for i in range(game.num_players):
        total = game.state.total_scores.get(i, 0)
        pudding = game.board.pudding_counts[i]

        player_name = f"Player {i + 1}"
        color = term.get_player_color(i)

        # Show round breakdown if available
        round_scores = game.state.round_scores.get(i, [])
        if round_scores:
            breakdown = " + ".join(str(s) for s in round_scores)
            print(f"  {color}{player_name:10}{term.RESET} {total:3} pts  ({breakdown})  🍮×{pudding}")
        else:
            print(f"  {color}{player_name:10}{term.RESET} {total:3} pts  🍮×{pudding}")

    print()


def render_player_collection(game: "SushiGoGame", player_idx: int) -> None:
    """Render a specific player's collection with visual effect cues."""
    collection = game.board.collections[player_idx]
    if not collection:
        return

    player_name = f"Player {player_idx + 1}"
    color = term.get_player_color(player_idx)

    print(f"{term.BOLD}{color}{player_name}'s Collection:{term.RESET}")

    from cards import CardType

    # Track wasabi-nigiri pairings
    wasabi_cards = [c for c in collection if c.type == CardType.WASABI]
    nigiri_cards = [c for c in collection if c.is_nigiri]

    # Match nigiri with wasabi (in order they were played)
    wasabi_paired = []
    nigiri_paired = []
    wasabi_count = 0

    for card in collection:
        if card.is_nigiri and wasabi_count < len(wasabi_cards):
            wasabi_paired.append(wasabi_cards[wasabi_count])
            nigiri_paired.append(card)
            wasabi_count += 1

    # Show Wasabi-Nigiri combos first (with visual indicator)
    for wasabi, nigiri in zip(wasabi_paired, nigiri_paired):
        points = nigiri.type.points * 3
        print(f"  {term.FG_GREEN}🌱 Wasabi + {nigiri.name} = {points} pts{term.RESET}")

    # Group remaining cards by type
    card_counts = {}
    shown_card_ids = set()
    for card in wasabi_paired + nigiri_paired:
        shown_card_ids.add(card.id)

    for card in collection:
        if card.id in shown_card_ids:
            continue
        name = card.name
        card_counts[name] = card_counts.get(name, 0) + 1

    # Display remaining cards with special indicators
    for card_name, count in sorted(card_counts.items()):
        # Add visual indicators for special cards
        display_name = card_name
        if "Chopsticks" in card_name:
            display_name = f"{term.FG_CYAN}🥢 {card_name} (Can swap for 2 cards!){term.RESET}"
        elif "Wasabi" in card_name:
            # Unpaired wasabi
            display_name = f"{term.FG_YELLOW}🌱 {card_name} (Waiting for Nigiri...){term.RESET}"
        elif "Pudding" in card_name:
            display_name = f"🍮 {card_name}"

        if count > 1:
            print(f"  {display_name} ×{count}")
        else:
            print(f"  {display_name}")

    print()


def render_all_collections(game: "SushiGoGame") -> None:
    """Render all players' collections."""
    print(f"{term.BOLD}Collections This Round:{term.RESET}")
    print()

    for i in range(game.num_players):
        render_player_collection(game, i)


def render_current_turn(game: "SushiGoGame") -> None:
    """Render information about current turn."""
    if game.board.is_round_over():
        print(f"{term.BOLD}{term.FG_YELLOW}Round is over! Calculating scores...{term.RESET}")
        print()
        return

    waiting = len(game.state.waiting_for_players)
    if waiting > 0:
        print(f"{term.BOLD}Waiting for {waiting} player(s) to play a card...{term.RESET}")
        print()


def render_card_selection(game: "SushiGoGame", player_idx: int) -> None:
    """Render available cards for current player to choose from."""
    hand = game.board.hands[player_idx]
    if not hand:
        return

    player_name = f"Player {player_idx + 1}"
    color = term.get_player_color(player_idx)

    print(f"{term.BOLD}{color}>>> {player_name}'s Turn{term.RESET}")
    print(f"{term.BOLD}Available Cards to Play:{term.RESET}")
    print()

    # Display each card with its details
    for i, card in enumerate(hand, 1):
        from cards import CardType, CARD_DESCRIPTIONS

        # Add visual icons for special cards
        icon = ""
        if card.type == CardType.CHOPSTICKS:
            icon = "🥢 "
        elif card.type == CardType.WASABI:
            icon = "🌱 "
        elif card.type == CardType.PUDDING:
            icon = "🍮 "
        elif card.is_nigiri:
            icon = "🍱 "
        elif card.is_maki:
            icon = "🍙 "

        card_name = f"{term.FG_YELLOW}{icon}{card.name}{term.RESET}"
        description = CARD_DESCRIPTIONS.get(card.type, "")

        print(f"  {i}. {card_name}")
        print(f"     {term.DIM}{description}{term.RESET}")

    print()


def render_play_action(player_name: str, card_name: str, reasoning: str | None = None) -> None:
    """Render a card being played."""
    player_idx = int(player_name.split()[-1]) - 1
    color = term.get_player_color(player_idx)

    print(f"{term.BOLD}{color}[{player_name}]{term.RESET} played: {term.FG_YELLOW}{card_name}{term.RESET}")
    if reasoning:
        print(f"  {term.DIM}Reasoning: {reasoning}{term.RESET}")
    print()


def render_round_end(game: "SushiGoGame") -> None:
    """Render round end scoring."""
    if game.state.current_round > len(game.state.round_scores.get(0, [])):
        return  # Not ended yet

    print(f"\n{term.BOLD}{term.FG_GREEN}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_GREEN}ROUND {game.state.current_round} RESULTS{term.RESET}")
    print()

    # Show round scores
    print(f"{term.BOLD}Round Scores:{term.RESET}")
    for i in range(game.num_players):
        player_name = f"Player {i + 1}"
        color = term.get_player_color(i)

        round_scores = game.state.round_scores[i]
        if round_scores:
            last_score = round_scores[-1]
            total = game.state.total_scores[i]

            print(f"  {color}{player_name:10}{term.RESET} earned {term.FG_YELLOW}{last_score:2}{term.RESET} pts  (Total: {total})")

    print(f"{term.BOLD}{term.FG_GREEN}{'=' * 70}{term.RESET}\n")


def render_game_end(game: "SushiGoGame") -> None:
    """Render game end screen."""
    if not game.state.is_over:
        return

    print(f"\n{term.BOLD}{term.FG_MAGENTA}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_MAGENTA}GAME OVER!{term.RESET}")
    print()

    # Show pudding scoring
    pudding_scores = game.board.calculate_pudding_scores()
    print(f"{term.BOLD}Pudding Scoring:{term.RESET}")
    for i in range(game.num_players):
        player_name = f"Player {i + 1}"
        pudding_count = game.board.pudding_counts[i]
        pudding_pts = pudding_scores[i]
        color = term.get_player_color(i)

        if pudding_pts != 0:
            print(f"  {color}{player_name:10}{term.RESET} {pudding_count} puddings = {pudding_pts:+3} pts")
        else:
            print(f"  {color}{player_name:10}{term.RESET} {pudding_count} puddings = {pudding_pts:3} pts")

    print()

    # Show final scores
    print(f"{term.BOLD}Final Scores:{term.RESET}")
    sorted_players = sorted(
        game.state.total_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for rank, (player_idx, score) in enumerate(sorted_players, 1):
        player_name = f"Player {player_idx + 1}"
        color = term.get_player_color(player_idx)

        if rank == 1:
            print(f"  {term.FG_YELLOW}🏆 {rank}. {color}{player_name:10}{term.RESET} {score} points{term.RESET}")
        else:
            print(f"     {rank}. {color}{player_name:10}{term.RESET} {score} points")

    if game.state.winner is not None:
        winner_name = f"Player {game.state.winner + 1}"
        print(f"\n{term.BOLD}{term.FG_YELLOW}Winner: {winner_name}!{term.RESET}")

    print(f"{term.BOLD}{term.FG_MAGENTA}{'=' * 70}{term.RESET}\n")


def refresh(game: "SushiGoGame") -> None:
    """Refresh the entire UI."""
    term.clear()
    render_header(game)
    render_round_info(game)
    render_all_collections(game)
    render_current_turn(game)


