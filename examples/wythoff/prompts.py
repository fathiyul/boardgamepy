"""Wythoff's Game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import WythoffGame


class WythoffPromptBuilder(PromptBuilder):
    """Build prompts for Wythoff's Game AI agents."""

    def build_system_prompt(self) -> str:
        """System prompt with Wythoff's Game rules and strategy."""
        return """You are playing Wythoff's Game, a classic mathematical strategy game.

RULES:
- There are two piles of objects (Pile A and Pile B)
- On your turn, you must make ONE of these moves:
  1. Remove any number of objects from Pile A only
  2. Remove any number of objects from Pile B only
  3. Remove the SAME number of objects from BOTH piles simultaneously

- The player who removes the last object(s) WINS

VALID MOVE TYPES:
- "pile_a": Remove only from Pile A (e.g., count=5 removes 5 from A)
- "pile_b": Remove only from Pile B (e.g., count=3 removes 3 from B)
- "both": Remove same amount from both piles (e.g., count=2 removes 2 from A AND 2 from B)

STRATEGY TIPS:
- Wythoff's Game has a connection to the golden ratio φ ≈ 1.618
- Certain positions are "losing positions" (P-positions) - if you leave these for your opponent, you can win
- P-positions follow a pattern based on the golden ratio:
  - (0, 0), (1, 2), (3, 5), (4, 7), (6, 10), (8, 13), (9, 15), (11, 18), ...
- If the current position is a P-position, any move you make gives your opponent advantage
- If the current position is NOT a P-position, try to find a move that leaves a P-position

IMPORTANT:
- You can remove the entire pile (remove all remaining objects)
- The "both" move is powerful - use it strategically
- Think about what position you leave for your opponent

OUTPUT FORMAT:
- Specify move_type: "pile_a", "pile_b", or "both"
- Specify count: number to remove
- Provide reasoning for your strategic choice
"""

    def build_user_prompt(self, game: "WythoffGame", player: "Player") -> str:
        """Build user prompt with current game state."""
        # Get board view
        from boardgamepy.protocols import SimpleViewContext

        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Get position hint
        position_hint = game.board.get_move_type_hint()

        # Build prompt
        parts = [
            f"You are {game.state.current_player}.",
            "",
            board_view,
            "",
            f"Total objects: {game.board.total_objects()}",
            f"Position analysis: {position_hint}",
            "",
            "AVAILABLE MOVES:",
            f"  - Remove 1-{game.board.pile_a} from Pile A only (move_type='pile_a')",
            f"  - Remove 1-{game.board.pile_b} from Pile B only (move_type='pile_b')",
            f"  - Remove 1-{min(game.board.pile_a, game.board.pile_b)} from BOTH piles (move_type='both')",
        ]

        # Add recent history if available
        if game.history.rounds:
            parts.append("")
            parts.append("RECENT MOVES:")
            history_text = game.history.to_prompt(max_rounds=5)
            parts.append(history_text)

        parts.append("")
        parts.append("Make your move. Choose move_type and count.")

        return "\n".join(parts)

    def build_messages(self, game: "WythoffGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
