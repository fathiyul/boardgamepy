"""Splendor game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term
from cards import GemType

if TYPE_CHECKING:
    from game import SplendorGame


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def _get_gem_icon(gem: GemType) -> str:
    """Get emoji/icon for gem type."""
    icons = {
        GemType.DIAMOND: "💎",
        GemType.SAPPHIRE: "🔷",
        GemType.EMERALD: "🟢",
        GemType.RUBY: "🔴",
        GemType.ONYX: "⚫",
        GemType.GOLD: "🟡",
    }
    return icons.get(gem, "?")


def render_header(game: "SplendorGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_YELLOW}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}    SPLENDOR{term.RESET}")
    print(f"{term.BOLD}{term.FG_YELLOW}{'=' * 70}{term.RESET}\n")


def render_turn_info(game: "SplendorGame") -> None:
    """Render turn information."""
    current = game.state.current_player_idx
    print(f"{term.BOLD}Turn {game.state.round_number}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}>>> Player {current + 1}'s Turn{term.RESET}")

    if game.state.final_round_triggered:
        print(f"{term.FG_RED}⚠️ FINAL ROUND!{term.RESET}")

    print()


def render_gem_bank(game: "SplendorGame") -> None:
    """Render gem bank."""
    print(f"{term.BOLD}Gem Bank:{term.RESET}")

    gems_display = []
    for gem in [GemType.DIAMOND, GemType.SAPPHIRE, GemType.EMERALD, GemType.RUBY, GemType.ONYX, GemType.GOLD]:
        count = game.board.gem_bank[gem]
        icon = _get_gem_icon(gem)
        gems_display.append(f"{icon}×{count}")

    print(f"  {' '.join(gems_display)}")
    print()


def render_nobles(game: "SplendorGame") -> None:
    """Render available nobles."""
    if not game.board.nobles:
        return

    print(f"{term.BOLD}Nobles (3pts each):{term.RESET}")
    for noble in game.board.nobles:
        req_str = ", ".join(
            f"{_get_gem_icon(gem)}×{count}" for gem, count in noble.requirements.items()
        )
        print(f"  👑 Requires: {req_str}")
    print()


def render_card_display(game: "SplendorGame") -> None:
    """Render card displays."""
    print(f"{term.BOLD}Available Cards:{term.RESET}")

    # Tier 3
    print(f"  {term.FG_MAGENTA}Tier 3:{term.RESET}")
    for card in game.board.tier3_display:
        cost_str = ", ".join(
            f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items()
        )
        bonus_icon = _get_gem_icon(card.bonus)
        print(
            f"    [{card.card_id:3d}] {term.FG_YELLOW}{card.points}pts{term.RESET} {bonus_icon} Cost: {cost_str}"
        )

    # Tier 2
    print(f"  {term.FG_BLUE}Tier 2:{term.RESET}")
    for card in game.board.tier2_display:
        cost_str = ", ".join(
            f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items()
        )
        bonus_icon = _get_gem_icon(card.bonus)
        print(
            f"    [{card.card_id:3d}] {term.FG_YELLOW}{card.points}pts{term.RESET} {bonus_icon} Cost: {cost_str}"
        )

    # Tier 1
    print(f"  {term.FG_GREEN}Tier 1:{term.RESET}")
    for card in game.board.tier1_display:
        cost_str = ", ".join(
            f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items()
        )
        bonus_icon = _get_gem_icon(card.bonus)
        print(
            f"    [{card.card_id:3d}] {term.FG_YELLOW}{card.points}pts{term.RESET} {bonus_icon} Cost: {cost_str}"
        )

    print()


def render_player_status(game: "SplendorGame") -> None:
    """Render all players' status."""
    print(f"{term.BOLD}Players:{term.RESET}")

    for i in range(game.num_players):
        player_name = f"Player {i + 1}"
        color = _get_player_color(i)

        # Calculate score
        card_points = game.board.get_player_points(i)
        nobles = game.state.player_nobles.get(i, [])
        noble_points = len(nobles) * 3
        total = card_points + noble_points

        # Gems
        gems = game.board.player_gems[i]
        gem_count = game.board.get_total_gems(i)

        # Bonuses
        bonuses = game.board.get_player_bonuses(i)
        bonus_str = ", ".join(
            f"{_get_gem_icon(gem)}×{count}" for gem, count in bonuses.items() if count > 0
        )

        # Cards
        num_cards = len(game.board.player_cards[i])
        num_reserved = len(game.board.player_reserved[i])

        info = f"{color}{player_name:10}{term.RESET} "
        info += f"Score: {term.FG_YELLOW}{total}{term.RESET} "
        info += f"({card_points}+{noble_points}) "
        info += f"| Gems: {gem_count}/10 "
        info += f"| Cards: {num_cards} "

        if num_reserved > 0:
            info += f"| Reserved: {num_reserved} "

        if bonus_str:
            info += f"| Bonus: {bonus_str}"

        print(f"  {info}")

    print()


def render_player_details(game: "SplendorGame", player_idx: int) -> None:
    """Render detailed view for current player."""
    player_name = f"Player {player_idx + 1}"
    color = _get_player_color(player_idx)

    print(f"{term.BOLD}{color}>>> {player_name}'s Turn{term.RESET}")
    print()

    # Your gems
    gems = game.board.player_gems[player_idx]
    print(f"  {term.BOLD}Your Gems:{term.RESET}")
    gem_display = []
    for gem in [GemType.DIAMOND, GemType.SAPPHIRE, GemType.EMERALD, GemType.RUBY, GemType.ONYX, GemType.GOLD]:
        count = gems[gem]
        if count > 0:
            icon = _get_gem_icon(gem)
            gem_display.append(f"{icon}×{count}")
    print(f"    {' '.join(gem_display) if gem_display else 'None'}")
    print()

    # Your bonuses
    bonuses = game.board.get_player_bonuses(player_idx)
    print(f"  {term.BOLD}Your Bonuses:{term.RESET}")
    bonus_display = []
    for gem in [GemType.DIAMOND, GemType.SAPPHIRE, GemType.EMERALD, GemType.RUBY, GemType.ONYX]:
        count = bonuses[gem]
        if count > 0:
            icon = _get_gem_icon(gem)
            bonus_display.append(f"{icon}×{count}")
    print(f"    {' '.join(bonus_display) if bonus_display else 'None'}")
    print()

    # Your reserved cards
    if game.board.player_reserved[player_idx]:
        print(f"  {term.BOLD}Your Reserved Cards:{term.RESET}")
        for card in game.board.player_reserved[player_idx]:
            cost_str = ", ".join(
                f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items()
            )
            bonus_icon = _get_gem_icon(card.bonus)
            can_afford = "✅" if game.board.can_afford_card(player_idx, card) else "❌"
            print(
                f"    [{card.card_id:3d}] {can_afford} {card.points}pts {bonus_icon} Cost: {cost_str}"
            )
        print()

    # Affordable cards
    affordable = []
    for card in (
        game.board.tier1_display + game.board.tier2_display + game.board.tier3_display
    ):
        if game.board.can_afford_card(player_idx, card):
            affordable.append(card)

    if affordable:
        print(f"  {term.FG_GREEN}💰 You can afford:{term.RESET}")
        for card in affordable[:5]:  # Show first 5
            cost_str = ", ".join(
                f"{_get_gem_icon(gem)}×{count}" for gem, count in card.cost.items()
            )
            bonus_icon = _get_gem_icon(card.bonus)
            print(f"    [{card.card_id:3d}] {card.points}pts {bonus_icon} Cost: {cost_str}")
        print()


def render_action(action_type: str, details: str) -> None:
    """Render an action taken."""
    print(f"{term.FG_CYAN}▶{term.RESET} {action_type}: {details}")
    print()


def render_noble_claim(player_name: str, noble) -> None:
    """Render noble claim."""
    print(f"\n{term.BOLD}{term.FG_YELLOW}👑 {player_name} is visited by a Noble! (+3 points){term.RESET}")
    print()


def render_game_end(game: "SplendorGame") -> None:
    """Render game end screen."""
    if not game.state.is_over:
        return

    print(f"\n{term.BOLD}{term.FG_YELLOW}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_YELLOW}GAME OVER!{term.RESET}")
    print()

    # Final scores
    print(f"{term.BOLD}Final Scores:{term.RESET}")

    scores = []
    for i in range(game.num_players):
        card_points = game.board.get_player_points(i)
        noble_points = len(game.state.player_nobles.get(i, [])) * 3
        total = card_points + noble_points
        card_count = len(game.board.player_cards[i])
        scores.append((i, total, card_count, card_points, noble_points))

    # Sort by score (desc), then by card count (asc)
    scores.sort(key=lambda x: (-x[1], x[2]))

    for rank, (player_idx, total, card_count, card_pts, noble_pts) in enumerate(scores, 1):
        player_name = f"Player {player_idx + 1}"
        color = _get_player_color(player_idx)

        if rank == 1:
            print(
                f"  {term.FG_YELLOW}🏆 {rank}. {color}{player_name:10}{term.RESET} "
                f"{total} points ({card_pts}+{noble_pts}), {card_count} cards"
            )
        else:
            print(
                f"     {rank}. {color}{player_name:10}{term.RESET} "
                f"{total} points ({card_pts}+{noble_pts}), {card_count} cards"
            )

    if game.state.winner is not None:
        winner_name = f"Player {game.state.winner + 1}"
        print(f"\n{term.BOLD}{term.FG_YELLOW}Winner: {winner_name}!{term.RESET}")

    print(f"{term.BOLD}{term.FG_YELLOW}{'=' * 70}{term.RESET}\n")


def refresh(game: "SplendorGame") -> None:
    """Refresh the entire UI."""
    clear_screen()
    render_header(game)
    render_turn_info(game)
    render_gem_bank(game)
    render_nobles(game)
    render_card_display(game)
    render_player_status(game)


def _get_player_color(player_idx: int) -> str:
    """Get color for player."""
    colors = [
        term.FG_BLUE,
        term.FG_MAGENTA,
        term.FG_GREEN,
        term.FG_CYAN,
    ]
    return colors[player_idx % len(colors)]
