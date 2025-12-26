"""Incan Gold game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import IncanGoldGame


class IncanGoldPromptBuilder(PromptBuilder):
    """Build prompts for Incan Gold AI agents."""

    def build_system_prompt(self) -> str:
        """System prompt with Incan Gold rules."""
        return """You are playing Incan Gold, a push-your-luck adventure game!

GAME RULES:
- You and other players are exploring an ancient temple together
- Each turn, you must decide: CONTINUE exploring OR RETURN to camp
- After all decisions, a new path card is revealed

PATH CARDS:
- 💎 TREASURE: Gems are divided among remaining explorers
  - If 5 explorers and 7 gems revealed: each gets 1, remainder stays on path
- 🏺 ARTIFACT: If only 1 player returns, they get it (5, 10, or 15 points)
- ⚠️ HAZARD: Danger! (Snake, Spider, Fire, Rockslide, Mummy)
  - If SAME hazard appears TWICE: Temple collapses! You lose all gems carried this round!

RETURNING TO CAMP:
- You collect ALL gems on the path, divided among all returners
- You KEEP your gems safely (can't lose them)
- You also keep any gems you collected earlier this round
- If you're the ONLY one returning and an artifact is on the path, you get it!
- You're out for the rest of this round (safe but can't get more)

CONTINUING:
- You might get more treasure
- Risk: Temple could collapse and you lose EVERYTHING from this round
- Reward: More gems, potential artifacts

TEMPLE COLLAPSE:
- Happens when the SAME hazard appears twice (e.g., 2 Snakes)
- All explorers still in temple lose gems they collected this round
- Round ends immediately

STRATEGY TIPS:
1. **Early round**: Usually safe to continue (few hazards revealed)
2. **Mid round**: Assess risk - how many hazards of each type revealed?
3. **Late round**: Very risky! Consider returning with your gems
4. **Gem calculation**: More explorers = smaller share per person
5. **Artifacts**: Worth risking if you might be sole returner
6. **Hazard tracking**: Count each hazard type (2nd of same type = collapse)

RISK ASSESSMENT:
- Hazards seen: 0 of a type = safe, 1 of a type = DANGER
- If 1 Snake already revealed, another Snake = instant collapse
- With 5 hazard types, probability of repeat increases as more cards revealed

OUTPUT FORMAT:
- decision: "continue" or "return"
- reasoning: Your strategic thinking
"""

    def build_user_prompt(self, game: "IncanGoldGame", player: "Player") -> str:
        """Build user prompt with current game state."""
        from boardgamepy.protocols import SimpleViewContext

        player_idx = int(player.team.split()[-1]) - 1
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Analyze hazards
        hazard_analysis = []
        for hazard_type, count in game.board.hazards_seen.items():
            if count == 1:
                hazard_analysis.append(f"  ⚠️ {hazard_type.value}: 1 seen (2nd one = COLLAPSE!)")
            else:
                hazard_analysis.append(f"  ⚠️ {hazard_type.value}: {count} seen")

        if not hazard_analysis:
            hazard_analysis.append("  ✅ No hazards yet (safe!)")

        # Build prompt
        parts = [
            f"Round {game.state.current_round}/{game.state.total_rounds}",
            "",
            board_view,
            "",
            "HAZARD ANALYSIS:",
            *hazard_analysis,
            "",
        ]

        # Recent cards
        if game.board.revealed_path:
            recent = game.board.revealed_path[-3:]
            recent_str = ", ".join(str(card) for card in recent)
            parts.append(f"Recent cards: {recent_str}")
            parts.append("")

        # Explorer count
        explorer_count = len(game.board.in_temple)
        parts.append(f"Explorers in temple: {explorer_count}")
        if game.board.gems_on_path > 0:
            share = game.board.gems_on_path // max(1, explorer_count)
            parts.append(f"If you return now: ~{share} gems from path")
        parts.append("")

        # Temp gems
        temp_gems = game.board.player_temp_gems[player_idx]
        if temp_gems > 0:
            parts.append(f"⚠️ You're carrying {temp_gems} gems! (Lost if temple collapses)")
            parts.append("")

        # Scores
        parts.append("Current Scores:")
        for i in range(game.board.num_players):
            score = game.board.get_total_score(i)
            if i == player_idx:
                parts.append(f"  YOU: {score} points")
            else:
                parts.append(f"  Player {i + 1}: {score} points")
        parts.append("")

        parts.append("Decision time: CONTINUE exploring (risky) or RETURN to camp (safe)?")

        return "\n".join(parts)

    def build_messages(self, game: "IncanGoldGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
