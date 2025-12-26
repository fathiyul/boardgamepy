"""Nim game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import NimGame


class NimPromptBuilder(PromptBuilder):
    """Build prompts for Nim AI agents."""

    def build_system_prompt(self) -> str:
        """System prompt with Nim rules and strategy."""
        return """You are playing the game of Nim.

RULES:
- There are multiple piles of objects
- On your turn, you must remove at least 1 object from exactly one pile
- You can remove as many objects as you want from that pile (up to the pile's size)
- The player who removes the last object WINS

STRATEGY TIPS:
- Nim has optimal mathematical strategy based on XOR (nim-sum)
- A position is a "losing position" if the XOR of all pile sizes equals 0
- Try to leave your opponent in a losing position
- If all piles have size 1, try to leave an odd number of piles

OUTPUT FORMAT:
- Specify which pile to remove from (1-based numbering)
- Specify how many objects to remove
- Provide brief reasoning for your move
"""

    def build_user_prompt(self, game: "NimGame", player: "Player") -> str:
        """Build user prompt with current game state."""
        # Get board view
        from boardgamepy.protocols import SimpleViewContext

        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Build prompt
        parts = [
            f"You are {game.state.current_player}.",
            "",
            board_view,
            "",
            f"Total objects remaining: {game.board.total_objects()}",
        ]

        # Add recent history if available
        if game.history.rounds:
            parts.append("")
            parts.append("RECENT MOVES:")
            history_text = game.history.to_prompt(max_rounds=3)
            parts.append(history_text)

        parts.append("")
        parts.append("Make your move. Which pile will you remove from, and how many objects?")

        return "\n".join(parts)

    def build_messages(self, game: "NimGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
