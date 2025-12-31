"""DixiQuote UI - terminal rendering with ANSI colors."""

from typing import TYPE_CHECKING, Optional
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import DixiQuoteGame


def render_phase_status(game: "DixiQuoteGame") -> None:
    """Render current phase and game status."""
    storyteller = game.players[game.state.storyteller_idx]
    phase_name = game.state.phase.replace("_", " ").title()

    print(
        f"{term.BOLD}Round {game.state.round_number}/{game.state.max_rounds}{term.RESET} — "
        f"Phase: {term.FG_CYAN}{phase_name}{term.RESET}"
    )
    print(f"{term.FG_YELLOW}Storyteller:{term.RESET} {storyteller.name}")
    print(f"{term.DIM}Target Score: {game.state.target_score} | Deck: {len(game.deck)} cards{term.RESET}")
    print()


def render_quote(game: "DixiQuoteGame") -> None:
    """Render the storyteller's quote if available."""
    if game.state.storyteller_quote:
        print(f"{term.BOLD}Quote:{term.RESET}")
        print(f'  {term.FG_BRIGHT_YELLOW}"{game.state.storyteller_quote}"{term.RESET}')
        print()


def render_situations(game: "DixiQuoteGame") -> None:
    """Render submitted situations during vote phase."""
    if game.state.phase == "vote" or game.state.phase == "scoring":
        situations = game.state.get_all_submitted_situations()
        if situations:
            print(f"{term.BOLD}Submitted Situations:{term.RESET}")
            for i, situation in enumerate(situations, 1):
                print(f"  {term.FG_CYAN}{i}.{term.RESET} {situation}")
            print()


def render_votes(game: "DixiQuoteGame") -> None:
    """Render votes if voting is complete."""
    if game.state.phase == "scoring":
        if game.state.votes:
            print(f"{term.BOLD}Votes:{term.RESET}")
            vote_counts: dict[str, int] = {}
            for situation in game.state.votes.values():
                vote_counts[situation] = vote_counts.get(situation, 0) + 1

            # Show vote counts for each situation
            situations = game.state.get_all_submitted_situations()
            for i, situation in enumerate(situations, 1):
                votes = vote_counts.get(situation, 0)
                bar = "█" * votes
                print(f"  {i}. {term.FG_BRIGHT_CYAN}{bar}{term.RESET} ({votes} votes)")
            print()


def render_scores(game: "DixiQuoteGame") -> None:
    """Render current scores."""
    print(f"{term.BOLD}Scores:{term.RESET}")
    scores = [(i, score) for i, score in game.state.scores.items()]
    scores.sort(key=lambda x: x[1], reverse=True)

    for player_idx, score in scores:
        player = game.players[player_idx]
        is_storyteller = player_idx == game.state.storyteller_idx
        marker = f"{term.FG_YELLOW}★{term.RESET} " if is_storyteller else "  "
        print(f"{marker}P-{player_idx}: {player.name}: {term.FG_GREEN}{score}{term.RESET}")
    print()


def render_hand(game: "DixiQuoteGame", player_idx: int) -> None:
    """Render a player's hand of situation cards."""
    hand = game.get_player_hand(player_idx)
    if hand:
        player = game.players[player_idx]
        player_label = f"{term.BOLD}{term.FG_BRIGHT_CYAN}P-{player_idx}: {player.name}{term.RESET}"
        print(f"{player_label} Hand:")
        for i, situation in enumerate(hand, 1):
            print(f"  {term.FG_CYAN}{i}.{term.RESET} {term.DIM}{situation}{term.RESET}")
        print()


def render_history(game: "DixiQuoteGame", max_rounds: int = 3) -> None:
    """Render recent round history."""
    if not game.history.rounds:
        return

    print(f"{term.BOLD}Recent Rounds:{term.RESET}")
    rounds_to_show = list(game.history.rounds)[-max_rounds:]

    for round_idx, round_ in enumerate(rounds_to_show):
        round_num = len(game.history.rounds) - max_rounds + round_idx + 1
        if round_num < 1:
            continue

        print(f"{term.DIM}Round {round_num}:{term.RESET}")

        for action in round_.actions:
            action_type = action.get("type")

            if action_type == "choose_situation":
                player_name = action.get("player")
                print(f"  - {player_name} chose a situation")

            elif action_type == "give_quote":
                quote = action.get("quote")
                print(f'  - Quote: "{term.FG_YELLOW}{quote}{term.RESET}"')

            elif action_type == "submit_situation":
                player_name = action.get("player")
                print(f"  - {player_name} submitted a situation")

            elif action_type == "vote":
                player_name = action.get("player")
                print(f"  - {player_name} voted")

    print()


def render_message(text: str, kind: str = "info") -> None:
    """Render a message."""
    prefix = ""
    if kind == "warn":
        prefix = term.FG_YELLOW + "! " + term.RESET
    elif kind == "error":
        prefix = term.FG_RED + "✖ " + term.RESET
    elif kind == "success":
        prefix = term.FG_GREEN + "✔ " + term.RESET

    print(f"{prefix}{text}")


def render_reasoning(text: Optional[str]) -> None:
    """Render AI reasoning."""
    if not text:
        return
    print(f"{term.DIM}Reasoning: {text}{term.RESET}")
    print()


def render_scoring_results(game: "DixiQuoteGame", situation_scores: dict[str, int]) -> None:
    """Render scoring results after a round."""
    print(f"{term.BOLD}{term.FG_GREEN}Round Scoring:{term.RESET}")
    print()

    # Show which situations scored what
    situations = game.state.get_all_submitted_situations()

    # Build vote count and voter mapping
    vote_counts: dict[str, int] = {}
    voters_per_situation: dict[str, list[str]] = {}

    for voter_idx, situation in game.state.votes.items():
        vote_counts[situation] = vote_counts.get(situation, 0) + 1
        if situation not in voters_per_situation:
            voters_per_situation[situation] = []
        voter_name = f"P-{voter_idx}: {game.players[voter_idx].name}"
        voters_per_situation[situation].append(voter_name)

    for situation in situations:
        votes = vote_counts.get(situation, 0)
        points = situation_scores.get(situation, 0)

        # Find who submitted this
        submitter_idx = None
        submitter_name = None
        if situation == game.state.storyteller_situation:
            submitter_idx = game.state.storyteller_idx
            submitter_name = f"P-{submitter_idx}: {game.players[submitter_idx].name} {term.FG_YELLOW}(Storyteller){term.RESET}"
        else:
            for player_idx, sub_situation in game.state.submitted_situations.items():
                if sub_situation == situation:
                    submitter_idx = player_idx
                    submitter_name = f"P-{player_idx}: {game.players[player_idx].name}"
                    break

        # Colorize vote count
        if votes == 0:
            vote_str = f"{term.DIM}{votes} votes{term.RESET}"
        elif votes == len(game.players) - 1:  # All votes
            vote_str = f"{term.FG_RED}{votes} votes (ALL){term.RESET}"
        else:
            vote_str = f"{term.FG_CYAN}{votes} vote{'s' if votes != 1 else ''}{term.RESET}"

        # Colorize points
        if points == 0:
            point_str = f"{term.DIM}+{points} pts{term.RESET}"
        elif points == 1:
            point_str = f"{term.FG_YELLOW}+{points} pt{term.RESET}"
        elif points == 2:
            point_str = f"{term.FG_GREEN}{term.BOLD}+{points} pts{term.RESET}"
        else:  # 3 points (storyteller bonus)
            point_str = f"{term.FG_BRIGHT_GREEN}{term.BOLD}+{points} pts{term.RESET}"

        # Show situation (truncated)
        print(f"  {term.DIM}{situation[:70]}...{term.RESET}")
        print(f"    Submitted by: {submitter_name}")
        print(f"    Votes: {vote_str} → {point_str}")

        # Show who voted for this situation
        if votes > 0:
            voters = voters_per_situation.get(situation, [])
            voters_str = ", ".join(voters)
            print(f"    {term.DIM}Voted by: {voters_str}{term.RESET}")

        print()

    # Show skipped players (penalties)
    if game.state.skipped_players:
        print(f"{term.BOLD}Penalties:{term.RESET}")
        for player_idx in game.state.skipped_players:
            player_name = f"P-{player_idx}: {game.players[player_idx].name}"
            print(f"  {player_name} {term.FG_RED}-1 pt{term.RESET} (3 invalid actions)")
        print()

    # Show storyteller bonus info
    storyteller_idx = game.state.storyteller_idx
    storyteller_name = f"P-{storyteller_idx}: {game.players[storyteller_idx].name}"

    # Check if storyteller got the bonus
    num_non_storyteller = len(game.players) - 1
    num_skipped_non_storyteller = sum(
        1 for idx in game.state.skipped_players if idx != storyteller_idx
    )

    print(f"{term.BOLD}Storyteller Bonus:{term.RESET}")
    if num_skipped_non_storyteller >= num_non_storyteller:
        bonus_pts = 3
        print(f"  {storyteller_name} {term.FG_BRIGHT_GREEN}{term.BOLD}+{bonus_pts} pts{term.RESET} (All other players skipped)")
    else:
        cards_with_votes = sum(1 for v in vote_counts.values() if v > 0)
        no_card_has_all = all(v < len(game.players) - 1 for v in vote_counts.values())

        if cards_with_votes >= 2 and no_card_has_all:
            bonus_pts = 3
            print(f"  {storyteller_name} {term.FG_BRIGHT_GREEN}{term.BOLD}+{bonus_pts} pts{term.RESET} (Good ambiguity!)")
        else:
            print(f"  {storyteller_name} {term.DIM}+0 pts{term.RESET} (Too obvious or too obscure)")
    print()


def refresh(game: "DixiQuoteGame", show_hand: bool = False, player_idx: int | None = None) -> None:
    """Full UI refresh - clear and redraw everything."""
    term.clear()
    term.render_header("DIXIQUOTE")
    print(f"{term.DIM}A game about how moments are remembered{term.RESET}")
    print()

    render_phase_status(game)
    render_quote(game)
    render_situations(game)
    render_votes(game)
    render_scores(game)

    if show_hand and player_idx is not None:
        render_hand(game, player_idx)

    # render_history(game, max_rounds=2)
