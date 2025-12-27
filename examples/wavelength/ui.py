"""Wavelength game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import WavelengthGame


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def render_header(game: "WavelengthGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_MAGENTA}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}    WAVELENGTH{term.RESET}")
    print(f"{term.BOLD}{term.FG_MAGENTA}{'=' * 70}{term.RESET}\n")


def render_scores(game: "WavelengthGame") -> None:
    """Render team scores."""
    print(f"{term.BOLD}Round {game.state.round_number}{term.RESET}")
    print(f"{term.BOLD}Scores:{term.RESET}")

    for team_idx in [0, 1]:
        score = game.state.team_scores[team_idx]
        target = game.state.target_score
        bar = "⭐" * score
        team_name = f"Team {team_idx + 1}"
        color = term.FG_BLUE if team_idx == 0 else term.FG_GREEN

        # Highlight current team
        if team_idx == game.state.current_team:
            print(f"  {color}{term.BOLD}► {team_name:8}{term.RESET} {bar} ({score}/{target})")
        else:
            print(f"  {color}{team_name:10}{term.RESET} {bar} ({score}/{target})")

    print()


def render_spectrum(game: "WavelengthGame") -> None:
    """Render the current spectrum."""
    if not game.board.current_spectrum:
        return

    spectrum = game.board.current_spectrum

    print(f"{term.BOLD}Current Spectrum:{term.RESET}")

    # Calculate arrow length to match scale line below
    # Scale line format: "0" + 40 spaces + "50" + 40 spaces + "100" = 86 chars
    scale_width = 86

    # Fixed parts of arrow line: "[" + "]" + " " + "←" + "→" + " " + "[" + "]" = 8 chars
    # Variable parts: spectrum.left and spectrum.right text
    fixed_chars = 8  # Brackets, spaces, and arrow ends
    text_length = len(spectrum.left) + len(spectrum.right)
    arrow_dashes_needed = scale_width - fixed_chars - text_length

    # Ensure minimum arrow length
    arrow_dashes = max(arrow_dashes_needed, 10)
    arrow = "─" * arrow_dashes

    print(f"  {term.FG_CYAN}[{spectrum.left}]{term.RESET} ←{arrow}→ {term.FG_MAGENTA}[{spectrum.right}]{term.RESET}")
    print(f"  {term.DIM}0{'':^40}50{'':^40}100{term.RESET}")

    # Show actual target position (for viewers - hidden from players in real game)
    if game.board.target_center is not None:
        if game.state.phase == "reveal":
            print(f"  {term.BOLD}Target: {game.board.target_center}{term.RESET}")
        else:
            # Show during other phases but mark as hidden
            print(f"  {term.DIM}(Target: {game.board.target_center} - hidden from players){term.RESET}")

    # Show guess if made
    if game.board.dial_position is not None:
        print(f"  {term.BOLD}Team's Guess: {game.board.dial_position}{term.RESET}")

    print()


def render_phase_info(game: "WavelengthGame") -> None:
    """Render current phase information."""
    phase = game.state.phase
    current_team = f"Team {game.state.current_team + 1}"

    if phase == "psychic_clue":
        psychic = [p for p in game.players if p.role == "Psychic"][0]
        print(f"{term.BOLD}{term.FG_YELLOW}Phase: PSYCHIC GIVES CLUE{term.RESET}")
        print(f"  {current_team}'s Psychic ({psychic.team}) is giving a clue...")
        print()

    elif phase == "team_guess":
        print(f"{term.BOLD}{term.FG_YELLOW}Phase: TEAM GUESSES POSITION{term.RESET}")
        print(f"  {current_team} is interpreting the clue...")
        if game.board.psychic_clue:
            print(f"  {term.BOLD}Clue:{term.RESET} \"{term.FG_CYAN}{game.board.psychic_clue}{term.RESET}\"")
        print()

    elif phase == "opponent_predict":
        opponent_team = f"Team {(1 - game.state.current_team) + 1}"
        print(f"{term.BOLD}{term.FG_YELLOW}Phase: OPPONENT PREDICTS{term.RESET}")
        print(f"  {opponent_team} is predicting left or right...")
        if game.board.psychic_clue:
            print(f"  {term.BOLD}Clue:{term.RESET} \"{term.FG_CYAN}{game.board.psychic_clue}{term.RESET}\"")
        if game.board.dial_position is not None:
            print(f"  {term.BOLD}{current_team}'s Guess:{term.RESET} {game.board.dial_position}")
        print()

    elif phase == "reveal":
        print(f"{term.BOLD}{term.FG_GREEN}Phase: REVEAL{term.RESET}")
        print()


def render_result(game: "WavelengthGame") -> None:
    """Render round result after reveal."""
    if game.state.phase != "reveal":
        return

    if game.board.dial_position is None:
        return

    print(f"\n{term.BOLD}{term.FG_GREEN}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_GREEN}ROUND RESULT{term.RESET}")
    print(f"{term.BOLD}{term.FG_GREEN}{'=' * 70}{term.RESET}\n")

    # Show clue that was given
    if game.board.psychic_clue:
        print(f"{term.BOLD}Clue:{term.RESET} \"{term.FG_CYAN}{game.board.psychic_clue}{term.RESET}\"")

    # Show scoring
    base_points, opponent_correct = game.board.calculate_score()
    final_points = base_points - (1 if opponent_correct else 0)
    final_points = max(0, final_points)

    current_team = f"Team {game.state.current_team + 1}"
    opponent_team = f"Team {(1 - game.state.current_team) + 1}"

    distance = abs(game.board.dial_position - game.board.target_center)

    print(f"{term.BOLD}Target:{term.RESET} {game.board.target_center}")
    print(f"{term.BOLD}{current_team} guessed:{term.RESET} {game.board.dial_position} (distance: {distance})")
    print(f"{term.BOLD}Points earned:{term.RESET} {base_points}")

    if game.board.opponent_prediction:
        prediction = game.board.opponent_prediction
        actual_side = "left" if game.board.dial_position < game.board.target_center else "right"
        if opponent_correct:
            print(f"{opponent_team} predicted {term.FG_YELLOW}{prediction}{term.RESET} correctly → -1 point")
        else:
            print(f"{opponent_team} predicted {term.FG_YELLOW}{prediction}{term.RESET} incorrectly (was {actual_side})")

    print(f"\n{term.BOLD}Total for {current_team}: {term.FG_GREEN}{final_points} points{term.RESET}")
    print(f"{term.BOLD}{term.FG_GREEN}{'=' * 70}{term.RESET}\n")


def render_game_end(game: "WavelengthGame") -> None:
    """Render game end screen."""
    if not game.state.is_over:
        return

    print(f"\n{term.BOLD}{term.FG_MAGENTA}{'=' * 70}{term.RESET}")
    print(f"{term.BOLD}{term.FG_MAGENTA}GAME OVER!{term.RESET}")

    if game.state.winner is not None:
        winner_name = f"Team {game.state.winner + 1}"
        print(f"{term.BOLD}{term.FG_YELLOW}🏆 {winner_name} WINS! 🏆{term.RESET}")

    print(f"\n{term.BOLD}Final Scores:{term.RESET}")
    for team_idx in [0, 1]:
        score = game.state.team_scores[team_idx]
        bar = "⭐" * score
        team_name = f"Team {team_idx + 1}"
        print(f"  {team_name:10} {bar} ({score})")

    print(f"{term.BOLD}{term.FG_MAGENTA}{'=' * 70}{term.RESET}\n")


def refresh(game: "WavelengthGame") -> None:
    """Refresh the entire UI."""
    clear_screen()
    render_header(game)
    render_scores(game)
    render_spectrum(game)
    render_phase_info(game)
