"""Strategic RPS UI - terminal rendering with ANSI colors."""

from typing import TYPE_CHECKING, Optional
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from strategy_game import StrategyRPSGame


def _player_color(player_num: int) -> str:
    """Get color for player number."""
    if player_num == 1:
        return term.FG_BRIGHT_CYAN
    return term.FG_BRIGHT_YELLOW


def _effect_color(effect_type: str) -> str:
    """Get color for effect type."""
    if effect_type == "none":
        return term.FG_BRIGHT_GREEN  # Safe - green
    elif effect_type == "points":
        return term.FG_BRIGHT_YELLOW  # Points penalty - yellow
    elif effect_type == "health":
        return term.FG_BRIGHT_RED  # Health penalty - red
    return term.FG_WHITE


def render_status(game: "StrategyRPSGame") -> None:
    """Render game status line."""
    state = game.state
    p1_color = _player_color(1)
    p2_color = _player_color(2)

    # Round info
    round_info = f"{term.BOLD}Round {state.current_round + 1}/15{term.RESET}"

    # Player 1 stats
    p1_name = f"{p1_color}{term.BOLD}Player 1{term.RESET}"
    p1_stats = f"Score: {term.BOLD}{state.player1_score}{term.RESET}/10  Health: "
    if state.player1_health <= 1:
        p1_stats += f"{term.FG_BRIGHT_RED}{term.BOLD}{state.player1_health}♥{term.RESET}"
    else:
        p1_stats += f"{term.BOLD}{state.player1_health}♥{term.RESET}"

    # Player 2 stats
    p2_name = f"{p2_color}{term.BOLD}Player 2{term.RESET}"
    p2_stats = f"Score: {term.BOLD}{state.player2_score}{term.RESET}/10  Health: "
    if state.player2_health <= 1:
        p2_stats += f"{term.FG_BRIGHT_RED}{term.BOLD}{state.player2_health}♥{term.RESET}"
    else:
        p2_stats += f"{term.BOLD}{state.player2_health}♥{term.RESET}"

    print(f"{round_info}")
    print()
    print(f"{p1_name}  {p1_stats}")
    print(f"{p2_name}  {p2_stats}")


def render_effects(game: "StrategyRPSGame") -> None:
    """Render current round's effect mapping."""
    state = game.state

    if not state.effect_mapping:
        return

    print()
    print(f"{term.BOLD}This Round's Effects:{term.RESET}")
    print()

    for choice in ["rock", "paper", "scissors"]:
        effect = state.effect_mapping.get(choice)
        if effect:
            # Format the effect display
            win_text = f"{term.FG_BRIGHT_GREEN}+{effect['win_points']}{term.RESET}"

            if effect['lose_type'] == 'none':
                lose_text = f"{term.FG_BRIGHT_GREEN}0{term.RESET}"
            elif effect['lose_type'] == 'points':
                lose_text = f"{term.FG_BRIGHT_YELLOW}-{effect['lose_effect']}pt{term.RESET}"
            elif effect['lose_type'] == 'health':
                lose_text = f"{term.FG_BRIGHT_RED}-{effect['lose_effect']}♥{term.RESET}"

            choice_text = f"{term.BOLD}{choice.capitalize():8}{term.RESET}"
            print(f"  {choice_text} → {win_text} / {lose_text}")


def render_last_round(game: "StrategyRPSGame") -> None:
    """Render last round result."""
    state = game.state

    if state.current_round == 0:
        return

    if not state.last_player1_choice or not state.last_player2_choice:
        return

    print()
    print(f"{term.BOLD}Last Round:{term.RESET}")

    p1_color = _player_color(1)
    p2_color = _player_color(2)

    p1_choice = f"{p1_color}{state.last_player1_choice}{term.RESET}"
    p2_choice = f"{p2_color}{state.last_player2_choice}{term.RESET}"

    print(f"  Player 1: {p1_choice}  vs  Player 2: {p2_choice}")


def render_turn_prompt(player_name: str, player_num: int) -> None:
    """Render turn prompt for AI."""
    color = _player_color(player_num)
    print()
    print(f"🤖 {color}{term.BOLD}{player_name}'s turn...{term.RESET}")


def render_ai_choice(choice: str, reasoning: Optional[str] = None) -> None:
    """Render AI's choice and reasoning."""
    print(f"   {term.BOLD}Choice:{term.RESET} {choice}")
    if reasoning:
        # Truncate long reasoning
        if len(reasoning) > 150:
            reasoning = reasoning[:147] + "..."
        print(f"   {term.DIM}Reasoning: {reasoning}{term.RESET}")


def render_game_over(game: "StrategyRPSGame") -> None:
    """Render game over screen."""
    state = game.state
    winner = state.get_winner()

    print()
    print("═" * 60)
    print()

    if winner == "Player 1":
        color = _player_color(1)
        print(f"  🏆 {color}{term.BOLD}{winner} WINS!{term.RESET}")
    elif winner == "Player 2":
        color = _player_color(2)
        print(f"  🏆 {color}{term.BOLD}{winner} WINS!{term.RESET}")
    else:
        print(f"  {term.BOLD}TIE GAME!{term.RESET}")

    print()
    print(f"  Final Scores:  P1: {term.BOLD}{state.player1_score}{term.RESET}/10  |  P2: {term.BOLD}{state.player2_score}{term.RESET}/10")
    print(f"  Final Health:  P1: {term.BOLD}{state.player1_health}♥{term.RESET}   |  P2: {term.BOLD}{state.player2_health}♥{term.RESET}")
    print()
    print("═" * 60)


def refresh(game: "StrategyRPSGame") -> None:
    """Full UI refresh - clear and redraw everything."""
    term.clear()
    term.render_header("STRATEGIC ROCK PAPER SCISSORS", width=60)
    print()
    render_status(game)
    render_effects(game)
    render_last_round(game)
