"""Prompt builder for Strategic RPS AI players."""

from typing import TYPE_CHECKING
from boardgamepy.ai import PromptBuilder
from boardgamepy.protocols import SimpleViewContext

if TYPE_CHECKING:
    from strategy_game import StrategyRPSGame
    from boardgamepy.core.player import Player


class StrategyRPSPromptBuilder(PromptBuilder["StrategyRPSGame"]):
    """Prompt builder for Strategic Rock Paper Scissors AI agents."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are an expert Strategic Rock Paper Scissors player. "
            "Analyze the risk/reward of each choice based on the current round's effects. "
            "Think strategically and output ONLY valid JSON matching the provided schema."
        )

    def build_user_prompt(self, game: "StrategyRPSGame", player: "Player") -> str:
        """Build user prompt with game context."""
        # Get the board view
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_view(context)

        prompt = f"""You are playing Strategic Rock Paper Scissors.

{board_view}

Game Rules:
- Rock beats Scissors
- Scissors beats Paper
- Paper beats Rock
- First to 10 points OR reduce opponent to 0 health wins

IMPORTANT - This Round's Effects:
Each round, the three choices (rock/paper/scissors) are randomly assigned different risk/reward effects.
- Format: +X/-Y where X is points you gain on win, Y is the penalty if you lose
- Penalties can be: 0 (nothing), -Xpt (lose points), or -X♥ (lose health)

Strategy Considerations:
1. Your current score vs opponent's score
2. Your health vs opponent's health
3. Risk/reward tradeoff of each choice THIS round
4. What might your opponent choose?

Examples of strategic thinking:
- If you're ahead in points, maybe choose safer options
- If you're behind and need points, consider higher risk choices
- If health is low, avoid choices with health penalties
- If opponent is low on health, you might risk a health penalty choice

Your task: Choose rock, paper, or scissors for this round.
Output your choice in the required JSON format with your strategic reasoning."""

        return prompt
