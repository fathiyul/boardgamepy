"""Tic-Tac-Toe prompt builders for AI players."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder
from boardgamepy.protocols import SimpleViewContext

if TYPE_CHECKING:
    from game import TicTacToeGame
    from boardgamepy.core.player import Player


class TicTacToePromptBuilder(PromptBuilder["TicTacToeGame"]):
    """Prompt builder for Tic-Tac-Toe AI."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are an expert Tic-Tac-Toe player. "
            "Analyze the board and make the best move. "
            "Output ONLY valid JSON matching the schema."
        )

    def build_user_prompt(self, game: "TicTacToeGame", player: "Player") -> str:
        """Build user prompt with game context."""
        # Get board view
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_view(context)

        # Get history
        history_lines = []
        for round_ in game.history.rounds:
            for action in round_.actions:
                if action.get("type") == "move":
                    player_mark = action.get("player")
                    position = action.get("position")
                    history_lines.append(f"{player_mark} played position {position}")

        history_text = "\n".join(history_lines) if history_lines else "No moves yet."

        # Get available positions
        empty_positions = game.board.get_empty_positions()

        return f"""
You are playing Tic-Tac-Toe as {game.state.current_player}.

RULES:
- Place your mark (X or O) on an empty position (1-9)
- Get 3 in a row (horizontal, vertical, or diagonal) to win
- Block your opponent from getting 3 in a row

CURRENT BOARD:
{board_view}

MOVE HISTORY:
{history_text}

AVAILABLE POSITIONS: {empty_positions}

YOUR TASK:
Choose the best position from the available positions.
Consider:
1. Can you win this turn?
2. Must you block opponent from winning?
3. Take center (5) or corners (1,3,7,9) for strategic advantage

Output format (JSON only):
{{
  "position": <number 1-9>,
  "reasoning": "Brief explanation of why this move is best"
}}
""".strip()
