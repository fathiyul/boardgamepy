"""Prompt builder for RPS AI players."""

from typing import TYPE_CHECKING
from boardgamepy.ai import PromptBuilder
from boardgamepy.protocols import SimpleViewContext

if TYPE_CHECKING:
    from game import RPSGame
    from boardgamepy.core.player import Player


class RPSPromptBuilder(PromptBuilder["RPSGame"]):
    """Prompt builder for Rock Paper Scissors AI agents."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are an expert Rock Paper Scissors player. "
            "Think strategically and output ONLY valid JSON "
            "matching the provided schema."
        )

    def build_user_prompt(self, game: "RPSGame", player: "Player") -> str:
        """Build user prompt with game context."""
        # Get the board view
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_view(context)

        prompt = f"""You are playing Rock Paper Scissors.

{board_view}

Game Rules:
- Rock beats Scissors
- Scissors beats Paper
- Paper beats Rock
- Best of {game.state.max_rounds} rounds
- Highest score wins

Make your choice strategically. Consider:
- What your opponent might choose
- Patterns from previous rounds
- The current score

Your task: Choose rock, paper, or scissors for this round.
Output your choice in the required JSON format with your reasoning."""

        return prompt
