"""Incan Gold game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import IncanGoldGame



def render_header(game: "IncanGoldGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_YELLOW}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}    INCAN GOLD{term.RESET}")
    print(f"{term.BOLD}{term.FG_YELLOW}{'=' * 70}{term.RESET}\n")


def render_round_info(game: "IncanGoldGame") -> None:
    """Render round information."""
    print(f"{term.BOLD}Round {game.state.current_round}/{game.state.total_rounds}{term.RESET}")
    print()


def render_temple_path(game: "IncanGoldGame") -> None:
    """Render the revealed temple path."""
    print(f"{term.BOLD}Temple Path:{term.RESET}")

    if not game.board.revealed_path:
        print(f"  {term.DIM}(Not yet explored){term.RESET}")
    else:
        for i, card in enumerate(game.board.revealed_path, 1):
            print(f"  {i}. {card}")

    print()

    if game.board.gems_on_path > 0:
        print(f"{term.FG_YELLOW}💎 {game.board.gems_on_path} gems on the path{term.RESET}")
        print()


def render_hazard_status(game: "IncanGoldGame") -> None:
    """Render hazard tracking."""
    print(f"{term.BOLD}Hazards Encountered:{term.RESET}")

    if not game.board.hazards_seen:
        print(f"  {term.FG_GREEN}✅ None yet - safe!{term.RESET}")
    else:
        for hazard_type, count in sorted(game.board.hazards_seen.items(), key=lambda x: x[0].value):
            if count == 1:
                print(f"  {term.FG_YELLOW}⚠️ {hazard_type.value}: {count} (DANGER: 2nd one collapses temple!){term.RESET}")
            else:
                print(f"  {term.FG_RED}💀 {hazard_type.value}: {count} (COLLAPSED!){term.RESET}")

    print()


def render_player_status(game: "IncanGoldGame") -> None:
    """Render all players' status."""
    print(f"{term.BOLD}Players:{term.RESET}")

    in_temple = game.board.in_temple
    explorer_count = len(in_temple)

    for i in range(game.num_players):
        player = game.players[i] if i < len(game.players) else None
        name = player.name if player and player.name else None
        player_label = f"P{i + 1} ({name})" if name else f"Player {i + 1}"
        color = term.get_player_color(i)

        score = game.board.get_total_score(i)
        gems = game.board.player_gems[i]
        temp_gems = game.board.player_temp_gems[i]
        artifacts = len(game.board.player_artifacts[i])

        if i in in_temple:
            status = f"{term.FG_GREEN}🏃 IN TEMPLE{term.RESET}"
            if temp_gems > 0:
                status += f" (carrying {term.FG_YELLOW}{temp_gems} gems{term.RESET})"

            # Show decision status during decision phase
            if game.state.phase == "decide":
                if i in game.state.decisions:
                    decision = game.state.decisions[i]
                    if decision == "continue":
                        status += f" {term.FG_GREEN}▶️ CONTINUING{term.RESET}"
                    else:
                        status += f" {term.FG_BLUE}◀️ RETURNING{term.RESET}"
                else:
                    status += f" {term.DIM}⏳ deciding...{term.RESET}"
        else:
            status = f"{term.FG_BLUE}🏕️ SAFE{term.RESET}"

        info = f"{color}{player_label:25}{term.RESET} {status} Score: {score} ({gems} gems, {artifacts} artifacts)"
        print(f"  {info}")

    print()
    print(f"{term.BOLD}Explorers in temple: {explorer_count}{term.RESET}")
    print()


def render_decision_prompt(game: "IncanGoldGame", player_idx: int) -> None:
    """Render decision prompt for current player."""
    player = game.players[player_idx] if player_idx < len(game.players) else None
    name = player.name if player and player.name else None
    player_label = f"P{player_idx + 1} ({name})" if name else f"Player {player_idx + 1}"
    color = term.get_player_color(player_idx)

    print(f"{term.BOLD}{color}>>> {player_label}'s Decision{term.RESET}")
    print()

    temp_gems = game.board.player_temp_gems[player_idx]
    if temp_gems > 0:
        print(f"  {term.FG_YELLOW}You're carrying {temp_gems} gems!{term.RESET}")
        print(f"  {term.DIM}(These will be lost if temple collapses){term.RESET}")
        print()

    print(f"  {term.FG_GREEN}CONTINUE{term.RESET}: Keep exploring (risky but potentially rewarding)")
    print(f"  {term.FG_BLUE}RETURN{term.RESET}:   Go back to camp (safe, keep what you have)")
    print()


def render_decision(player_name: str, decision: str, reasoning: str | None = None,
                    display_name: str | None = None) -> None:
    """Render a player's decision."""
    player_idx = int(player_name.split()[-1]) - 1
    color = term.get_player_color(player_idx)

    # Use display_name if provided, otherwise use player_name
    shown_name = display_name if display_name else player_name

    if decision == "continue":
        decision_text = f"{term.FG_GREEN}CONTINUES exploring{term.RESET}"
    else:
        decision_text = f"{term.FG_BLUE}RETURNS to camp{term.RESET}"

    print(f"{color}[{shown_name}]{term.RESET} {decision_text}")
    if reasoning:
        print(f"  {term.DIM}Reasoning: {reasoning}{term.RESET}")
    print()


def render_card_reveal(card, game: "IncanGoldGame") -> None:
    """Render revealed card."""
    print(f"\n{term.BOLD}{term.FG_YELLOW}{'─' * 70}{term.RESET}")
    print(f"{term.BOLD}Card Revealed: {card}{term.RESET}")

    if card.is_hazard:
        count = game.board.hazards_seen[card.hazard]
        if count >= 2:
            print(f"{term.FG_RED}💀 TEMPLE COLLAPSED! Same hazard appeared twice!{term.RESET}")
            print(f"{term.FG_RED}All explorers lose their carried gems!{term.RESET}")
    elif card.is_treasure:
        explorers = len(game.board.in_temple)
        if explorers > 0:
            share = card.value // explorers
            print(f"  Each of {explorers} explorers gets {share} gems")
    elif card.is_artifact:
        print(f"  Worth {card.value} points if you're the sole returner!")

    print(f"{term.BOLD}{term.FG_YELLOW}{'─' * 70}{term.RESET}\n")


def render_distribution(game: "IncanGoldGame", returners: set[int]) -> None:
    """Render gem distribution to returners."""
    if returners and game.board.gems_on_path > 0:
        gems = game.board.gems_on_path
        count = len(returners)
        each = gems // count

        print(f"{term.BOLD}Returners collect gems from path:{term.RESET}")
        for player_idx in returners:
            player = game.players[player_idx] if player_idx < len(game.players) else None
            name = player.name if player and player.name else None
            player_label = f"P{player_idx + 1} ({name})" if name else f"Player {player_idx + 1}"
            color = term.get_player_color(player_idx)
            print(f"  {color}{player_label}{term.RESET} receives {term.FG_YELLOW}{each} gems{term.RESET}")
        print()


def render_round_end(game: "IncanGoldGame") -> None:
    """Render round end summary."""
    print(f"\n{term.BOLD}{term.FG_GREEN}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_GREEN}ROUND {game.state.current_round} COMPLETE{term.RESET}")
    print()

    # Show scores
    print(f"{term.BOLD}Scores:{term.RESET}")
    sorted_players = sorted(
        range(game.num_players),
        key=lambda i: game.board.get_total_score(i),
        reverse=True,
    )

    for rank, player_idx in enumerate(sorted_players, 1):
        player = game.players[player_idx] if player_idx < len(game.players) else None
        name = player.name if player and player.name else None
        player_label = f"P{player_idx + 1} ({name})" if name else f"Player {player_idx + 1}"
        color = term.get_player_color(player_idx)
        score = game.board.get_total_score(player_idx)
        gems = game.board.player_gems[player_idx]
        artifacts = game.board.player_artifacts[player_idx]

        artifact_str = ""
        if artifacts:
            artifact_pts = sum(a.value for a in artifacts)
            artifact_str = f" ({len(artifacts)} artifacts: {artifact_pts} pts)"

        if rank == 1:
            print(f"  {term.FG_YELLOW}🏆 {rank}. {color}{player_label:25}{term.RESET} {score} points ({gems} gems{artifact_str})")
        else:
            print(f"     {rank}. {color}{player_label:25}{term.RESET} {score} points ({gems} gems{artifact_str})")

    print(f"{term.BOLD}{term.FG_GREEN}{'=' * 70}{term.RESET}\n")


def render_game_end(game: "IncanGoldGame") -> None:
    """Render game end screen."""
    if not game.state.is_over:
        return

    print(f"\n{term.BOLD}{term.FG_YELLOW}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_YELLOW}GAME OVER!{term.RESET}")
    print()

    # Final scores
    print(f"{term.BOLD}Final Scores:{term.RESET}")
    sorted_players = sorted(
        range(game.num_players),
        key=lambda i: game.board.get_total_score(i),
        reverse=True,
    )

    for rank, player_idx in enumerate(sorted_players, 1):
        player = game.players[player_idx] if player_idx < len(game.players) else None
        name = player.name if player and player.name else None
        player_label = f"P{player_idx + 1} ({name})" if name else f"Player {player_idx + 1}"
        color = term.get_player_color(player_idx)
        score = game.board.get_total_score(player_idx)

        if rank == 1:
            print(f"  {term.FG_YELLOW}🏆 {rank}. {color}{player_label:25}{term.RESET} {score} points{term.RESET}")
        else:
            print(f"     {rank}. {color}{player_label:25}{term.RESET} {score} points")

    if game.state.winner is not None:
        winner_idx = game.state.winner
        winner_player = game.players[winner_idx] if winner_idx < len(game.players) else None
        winner_name = winner_player.name if winner_player and winner_player.name else None
        winner_label = f"P{winner_idx + 1} ({winner_name})" if winner_name else f"Player {winner_idx + 1}"
        print(f"\n{term.BOLD}{term.FG_YELLOW}Winner: {winner_label}!{term.RESET}")

    print(f"{term.BOLD}{term.FG_YELLOW}{'=' * 70}{term.RESET}\n")


def refresh(game: "IncanGoldGame") -> None:
    """Refresh the entire UI."""
    term.clear()
    render_header(game)
    render_round_info(game)
    render_temple_path(game)
    render_hazard_status(game)
    render_player_status(game)


