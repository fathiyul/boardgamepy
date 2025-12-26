"""Codenames UI - terminal rendering with ANSI colors."""

from typing import Literal, Optional, TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import CodenamesGame


def _pad(text: str, width: int) -> str:
    """Pad text to width."""
    t = text[:width]
    return t + (" " * (width - len(t)))


def _team_bg(team: Optional[str]) -> str:
    """Get background color for team."""
    if team == "Red":
        return term.BG_RED + term.FG_WHITE
    if team == "Blue":
        return term.BG_BLUE + term.FG_WHITE
    return term.BG_GRAY + term.FG_WHITE


def _type_bg(card_type: str) -> tuple[str, str]:
    """Return (bg, fg) for revealed tiles by card type."""
    if card_type == "Red":
        return term.BG_RED, term.FG_WHITE
    if card_type == "Blue":
        return term.BG_BLUE, term.FG_WHITE
    if card_type == "Civilian":
        return term.BG_GRAY, term.FG_WHITE
    if card_type == "Assassin":
        return term.BG_MAGENTA, term.FG_WHITE
    return "", term.FG_WHITE


def _type_fg_hint(card_type: str) -> str:
    """High-contrast foreground for hidden tiles in spymaster view."""
    if card_type == "Red":
        return term.FG_BRIGHT_RED
    if card_type == "Blue":
        return term.FG_BRIGHT_CYAN
    if card_type == "Civilian":
        return term.FG_BRIGHT_YELLOW
    if card_type == "Assassin":
        return term.FG_BRIGHT_MAGENTA
    return term.FG_BRIGHT_WHITE


def _team_fg(team: Optional[str]) -> str:
    """Get foreground color for team."""
    if team == "Red":
        return term.FG_BRIGHT_RED
    if team == "Blue":
        return term.FG_BRIGHT_CYAN
    return term.FG_BRIGHT_WHITE


def _codename_fg_for_type(card_type: str) -> str:
    """Get foreground color for codename based on type."""
    if card_type == "Red":
        return term.FG_BRIGHT_RED
    if card_type == "Blue":
        return term.FG_BRIGHT_CYAN
    if card_type == "Civilian":
        return term.FG_BRIGHT_YELLOW
    if card_type == "Assassin":
        return term.FG_BRIGHT_MAGENTA
    return term.FG_BRIGHT_WHITE


def _result_emoji(card_type: str, team: Optional[str]) -> str:
    """Get emoji for guess result."""
    if card_type == "Assassin":
        return "☠️"
    if card_type == "Civilian":
        return "🫥"
    if team and card_type == team:
        return "❇️"
    return "💥"


def _latest_clue_for_team(game: "CodenamesGame", team: str) -> tuple[str | None, int | None]:
    """Get most recent clue for team."""
    for round_ in reversed(game.history.rounds):
        for action in reversed(round_.actions):
            if action.get("type") == "clue" and action.get("team") == team:
                return action.get("clue"), action.get("count")
    return None, None


def render_status(game: "CodenamesGame", mode: Literal["operatives", "spymaster"]) -> None:
    """Render game status line."""
    team = game.state.current_team
    tag = f"[{team} {mode.capitalize()}]"
    counts = f"Red {game.state.red_remaining} | Blue {game.state.blue_remaining}"
    clue, count = _latest_clue_for_team(game, team)

    if clue:
        if mode == "spymaster":
            colored = f"{_team_fg(team)}{clue} {count}{term.RESET}"
            clue_txt = f"Clue: {colored}"
        else:
            clue_txt = f"Clue: {clue} {count}"
    else:
        clue_txt = "Clue: —"

    line1 = f"{_team_bg(team)} {tag} {term.RESET}  Guesses: {term.BOLD}{game.state.guesses_remaining}{term.RESET}  |  {counts}"
    print(line1)
    print(f"{term.FG_BRIGHT_WHITE}{clue_txt}{term.RESET}")


def render_board(game: "CodenamesGame", mode: Literal["operatives", "spymaster"]) -> None:
    """Render the 5x5 game board."""
    cards = [game.board.cards[i] for i in range(1, 26)]
    cell_w = 16

    # Top border
    horiz = "+" + "+".join(["-" * cell_w] * 5) + "+"
    print(horiz)

    for r in range(5):
        row_cards = cards[r * 5 : (r + 1) * 5]
        line = "|"
        for c in row_cards:
            label = _pad(f"{c.id:2d} {c.code}", cell_w)
            if c.state == "Revealed":
                bg, fg = _type_bg(c.type)
                line += f"{bg}{fg}{label}{term.RESET}|"
            else:
                if mode == "spymaster":
                    # High-contrast type hint for spymaster
                    fg = _type_fg_hint(c.type)
                    line += f"{fg}{label}{term.RESET}|"
                else:
                    line += f"{label}|"
        print(line)
        print(horiz)


def render_history(game: "CodenamesGame", max_lines: int = 8) -> None:
    """Render recent action history."""
    lines: list[str] = []

    for rnd_idx, round_ in enumerate(game.history.rounds, start=1):
        for action in round_.actions:
            action_type = action.get("type")
            team = action.get("team")

            if action_type == "clue":
                team_fg = _team_fg(team)
                clue = action.get("clue")
                count = action.get("count")
                clue_text = f"{team_fg}{clue} {count}{term.RESET}"
                lines.append(f"R{rnd_idx}: {team} Spymaster → {clue_text}")

            elif action_type == "guess":
                team_label = f"{_team_fg(team)}{team}{term.RESET}"
                codename = action.get("codename")
                card_type = action.get("card_type")
                code_fg = _codename_fg_for_type(card_type)
                code = f"{code_fg}{codename}{term.RESET}"
                emoji = _result_emoji(card_type, team)
                lines.append(f"R{rnd_idx}: {team_label} Operatives guessed {code} {emoji}")

            elif action_type == "pass":
                lines.append(f"R{rnd_idx}: {team} Operatives PASSED")

    if not lines:
        return

    print(f"{term.BOLD}Recent actions:{term.RESET}")
    for l in lines[-max_lines:]:
        print(f"- {l}")


def render_message(
    team: Optional[str],
    role: str,
    text: str,
    kind: Literal["info", "warn", "error", "success"] = "info",
) -> None:
    """Render a message."""
    prefix = ""
    if kind == "warn":
        prefix = term.FG_YELLOW + "! " + term.RESET
    elif kind == "error":
        prefix = term.FG_RED + "✖ " + term.RESET
    elif kind == "success":
        prefix = term.FG_GREEN + "✔ " + term.RESET

    if team is None:
        headline = f"{term.FG_BRIGHT_WHITE}{term.BOLD}{role}{term.RESET}"
        print(f"{headline} {prefix}{text}")
        return

    tag = f"[{team} {role}]"
    bg = _team_bg(team)
    print(f"{bg} {tag} {term.RESET} {prefix}{text}")


def render_guess_result(team: str, codename: str, card_type: str) -> None:
    """Render guess result with colors."""
    team_label = f"{_team_fg(team)}{team}{term.RESET}"
    tag = f"[{team_label} Operatives]"
    code_fg = _codename_fg_for_type(card_type)
    code = f"{code_fg}{codename}{term.RESET}"
    emoji = _result_emoji(card_type, team)
    print(f"{tag} {code} {emoji}")


def render_reasoning(text: Optional[str]) -> None:
    """Render AI reasoning."""
    if not text:
        return
    print(f"{term.DIM}Reasoning: {text}{term.RESET}")


def refresh(
    game: "CodenamesGame",
    mode: Literal["operatives", "spymaster"],
    show_history: bool = False,
) -> None:
    """Full UI refresh - clear and redraw everything."""
    term.clear()
    term.render_header("CODENAMES")
    print()
    render_status(game, mode)
    print()
    render_board(game, mode)
    if show_history:
        print()
        render_history(game, max_lines=8)
        print()
