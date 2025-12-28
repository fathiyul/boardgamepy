"""Love Letter game UI rendering."""

from typing import TYPE_CHECKING
from boardgamepy.ui import terminal as term

if TYPE_CHECKING:
    from game import LoveLetterGame



def render_header(game: "LoveLetterGame") -> None:
    """Render game header."""
    print(f"\n{term.BOLD}{term.FG_MAGENTA}{'=' * 60}{term.RESET}")
    print(f"{term.BOLD}{term.FG_CYAN}    LOVE LETTER{term.RESET}")
    print(f"{term.BOLD}{term.FG_MAGENTA}{'=' * 60}{term.RESET}\n")


def render_game_status(game: "LoveLetterGame") -> None:
    """Render overall game status."""
    print(f"{term.BOLD}Round {game.state.round_number}{term.RESET}")
    print(f"{term.BOLD}Score:{term.RESET}")
    for i in range(game.num_players):
        player = game.players[i] if i < len(game.players) else None
        name = player.name if player and player.name else None
        player_label = f"P{i + 1} ({name})" if name else f"Player {i + 1}"
        tokens = game.state.scores.get(i, 0)
        bar = "❤️ " * tokens
        target = game.state.target_tokens
        print(f"  {player_label}: {bar}({tokens}/{target})")
    print()


def render_board(game: "LoveLetterGame") -> None:
    """Render the game board state."""
    print(f"{term.BOLD}Players:{term.RESET}")

    for i in range(game.num_players):
        player = game.players[i] if i < len(game.players) else None
        name = player.name if player and player.name else None
        player_label = f"P{i + 1} ({name})" if name else f"Player {i + 1}"
        color = term.get_player_color(i)

        status_parts = [f"{color}{player_label}{term.RESET}"]

        if i in game.board.eliminated:
            status_parts.append(f"{term.DIM}[ELIMINATED]{term.RESET}")
        elif i in game.board.protected:
            status_parts.append(f"{term.FG_YELLOW}[PROTECTED]{term.RESET}")
        else:
            status_parts.append(f"{term.FG_GREEN}[ACTIVE]{term.RESET}")

        # Show cards in hand
        hand = game.board.hands.get(i, [])
        if hand:
            hand_str = ", ".join([f"{card.name}({card.value})" for card in hand])
            status_parts.append(f"| Hand: {term.FG_CYAN}{hand_str}{term.RESET}")

        print(f"  {' '.join(status_parts)}")

    print()

    # Discarded cards
    if game.board.discarded:
        discards_by_value = {}
        for card in game.board.discarded:
            name = f"{card.name}({card.value})"
            discards_by_value[name] = discards_by_value.get(name, 0) + 1

        discard_str = ", ".join(f"{name}×{count}" for name, count in discards_by_value.items())
        print(f"{term.BOLD}Discarded:{term.RESET} {term.DIM}{discard_str}{term.RESET}")
    else:
        print(f"{term.BOLD}Discarded:{term.RESET} {term.DIM}(none){term.RESET}")

    print(f"{term.BOLD}Cards in deck:{term.RESET} {len(game.board.deck)}")
    print()


def render_current_turn(game: "LoveLetterGame") -> None:
    """Render current turn information."""
    if game.state.round_over:
        return

    player_idx = game.state.current_player_idx
    color = term.get_player_color(player_idx)
    player = game.players[player_idx] if player_idx < len(game.players) else None
    name = player.name if player and player.name else None
    player_label = f"P{player_idx + 1} ({name})" if name else f"Player {player_idx + 1}"

    print(f"{term.BOLD}{color}>>> {player_label}'s Turn{term.RESET}\n")


def render_draw(player_idx: int, card) -> None:
    """Render a card draw action."""
    color = term.get_player_color(player_idx)
    player_name = f"Player {player_idx + 1}"
    card_str = f"{card.name}({card.value})"

    print(f"{term.BOLD}{color}[{player_name}]{term.RESET} draws {term.FG_CYAN}{card_str}{term.RESET}")
    print()


def render_action_result(result: dict) -> None:
    """Render the result of a card action with emojis."""
    if not result:
        return

    # Guard result
    if 'guard_correct' in result:
        if result['guard_correct']:
            print(f"  ✅ {term.FG_GREEN}Guess CORRECT!{term.RESET} (was {result['actual_card']})")
        else:
            print(f"  ❌ {term.FG_RED}Guess wrong.{term.RESET} (was {result['actual_card']}, guessed {result['guessed_card']})")
        print()

    # Priest result
    if 'priest_saw' in result:
        print(f"  👁️  {term.FG_CYAN}Saw: {result['priest_saw']}{term.RESET}")
        print()

    # Baron result
    if 'baron_compare' in result:
        print(f"  ⚔️  Baron comparison:")
        print(f"     Your card: {result['player_card']}")
        print(f"     Their card: {result['target_card']}")
        if result['winner'] == 'player':
            print(f"     {term.FG_GREEN}You win!{term.RESET}")
        elif result['winner'] == 'target':
            print(f"     {term.FG_RED}You lose!{term.RESET}")
        else:
            print(f"     {term.FG_YELLOW}Tie!{term.RESET}")
        print()


def render_move(
    player_name: str,
    card: str,
    target: int | None = None,
    guess: str | None = None,
    reasoning: str | None = None,
) -> None:
    """Render a move being made."""
    player_idx = int(player_name.split()[-1]) - 1
    color = term.get_player_color(player_idx)

    print(f"{term.BOLD}{color}[{player_name}]{term.RESET}")
    print(f"  {term.BOLD}Played:{term.RESET} {term.FG_YELLOW}{card}{term.RESET}")

    if target:
        print(f"  {term.BOLD}Target:{term.RESET} Player {target}")

    if guess:
        print(f"  {term.BOLD}Guess:{term.RESET} {guess}")

    if reasoning:
        print(f"  {term.BOLD}Reasoning:{term.RESET} {term.DIM}{reasoning}{term.RESET}")

    print()


def render_round_end(game: "LoveLetterGame") -> None:
    """Render round end summary."""
    if not game.state.round_over:
        return

    print(f"\n{term.BOLD}{term.FG_GREEN}{'=' * 60}{term.RESET}")
    print(f"{term.BOLD}{term.FG_GREEN}Round {game.state.round_number} Over!{term.RESET}")

    if game.state.round_winner is not None:
        winner_idx = game.state.round_winner
        player = game.players[winner_idx] if winner_idx < len(game.players) else None
        name = player.name if player and player.name else None
        winner_label = f"P{winner_idx + 1} ({name})" if name else f"Player {winner_idx + 1}"
        winner_hand = game.board.hands[winner_idx]
        if winner_hand:
            winner_card = winner_hand[0]
            print(f"{term.BOLD}Winner: {term.FG_YELLOW}{winner_label}{term.RESET} with {term.FG_CYAN}{winner_card}{term.RESET}")
        else:
            print(f"{term.BOLD}Winner: {term.FG_YELLOW}{winner_label}{term.RESET}")

    print(f"{term.BOLD}{term.FG_GREEN}{'=' * 60}{term.RESET}\n")


def render_game_end(game: "LoveLetterGame") -> None:
    """Render game end screen."""
    if not game.state.is_over:
        return

    print(f"\n{term.BOLD}{term.FG_MAGENTA}{'=' * 60}{term.RESET}")
    print(f"{term.BOLD}{term.FG_MAGENTA}GAME OVER!{term.RESET}")

    if game.state.winner is not None:
        winner_idx = game.state.winner
        player = game.players[winner_idx] if winner_idx < len(game.players) else None
        name = player.name if player and player.name else None
        winner_label = f"P{winner_idx + 1} ({name})" if name else f"Player {winner_idx + 1}"
        print(f"{term.BOLD}{term.FG_YELLOW}🏆 {winner_label} WINS! 🏆{term.RESET}")

    print(f"\n{term.BOLD}Final Scores:{term.RESET}")
    for i in range(game.num_players):
        player = game.players[i] if i < len(game.players) else None
        name = player.name if player and player.name else None
        player_label = f"P{i + 1} ({name})" if name else f"Player {i + 1}"
        tokens = game.state.scores.get(i, 0)
        bar = "❤️ " * tokens
        print(f"  {player_label}: {bar}({tokens})")

    print(f"{term.BOLD}{term.FG_MAGENTA}{'=' * 60}{term.RESET}\n")


def render_history(game: "LoveLetterGame", max_moves: int = 5) -> None:
    """Render recent move history."""
    if not game.history.rounds:
        return

    print(f"{term.BOLD}Recent Moves:{term.RESET}")

    # Collect actions
    moves = []
    for round_data in game.history.rounds:
        for action_record in round_data.actions:
            moves.append(action_record)

    # Show last N moves
    for move in moves[-max_moves:]:
        player = move["player"]
        card = move["card"]
        target = move.get("target", "")
        guess = move.get("guess", "")

        parts = [f"{player}: {card}"]
        if target:
            parts.append(f"→ {target}")
        if guess:
            parts.append(f"(guessed {guess})")

        print(f"  {term.DIM}{' '.join(parts)}{term.RESET}")

    print()


def refresh(game: "LoveLetterGame") -> None:
    """Refresh the entire UI."""
    term.clear()
    render_header(game)
    render_game_status(game)
    render_board(game)
    render_history(game)
    render_current_turn(game)


