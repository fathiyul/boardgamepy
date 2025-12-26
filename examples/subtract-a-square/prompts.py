"""Subtract-a-Square game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import SubtractASquareGame


class SubtractASquarePromptBuilder(PromptBuilder):
    """Build prompts for Subtract-a-Square AI agents."""

    def build_system_prompt(self) -> str:
        """System prompt with game rules and strategy."""
        return """You are playing Subtract-a-Square, a mathematical strategy game.

RULES:
- There is a single pile of objects
- On your turn, you must remove a PERFECT SQUARE number of objects (1, 4, 9, 16, 25, 36, 49, ...)
- You can only remove amounts that don't exceed the current pile count
- The player who removes the last object WINS

VALID MOVES:
- 1 (1×1)
- 4 (2×2)
- 9 (3×3)
- 16 (4×4)
- 25 (5×5)
- 36 (6×6)
- 49 (7×7)
- ... and so on

STRATEGY TIPS:
- This game has winning and losing positions
- Try to identify patterns in winning positions
- Consider what positions you leave for your opponent
- Numbers like 2, 3, 5, 6, 7, 8 are losing positions (no way to win from there)
- If you can leave your opponent with 2, 3, 5, 6, 7, or 8 objects, you have a strong position

OUTPUT FORMAT:
- Specify the perfect square amount to remove
- Provide brief reasoning for your move
"""

    def build_user_prompt(self, game: "SubtractASquareGame", player: "Player") -> str:
        """Build user prompt with current game state."""
        # Get board view
        from boardgamepy.protocols import SimpleViewContext

        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Get valid moves
        valid_moves = game.board.get_valid_moves()
        valid_moves_str = ", ".join(str(m) for m in valid_moves)

        # Build prompt
        parts = [
            f"You are {game.state.current_player}.",
            "",
            board_view,
            "",
            f"Valid moves (perfect squares you can remove): {valid_moves_str}",
        ]

        # Add recent history if available
        if game.history.rounds:
            parts.append("")
            parts.append("RECENT MOVES:")
            history_text = game.history.to_prompt(max_rounds=5)
            parts.append(history_text)

        parts.append("")
        parts.append("Make your move. How many objects will you remove?")

        return "\n".join(parts)

    def build_messages(self, game: "SubtractASquareGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
