"""Sushi Go! game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder
from cards import CARD_DESCRIPTIONS, CardType

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import SushiGoGame


class SushiGoPromptBuilder(PromptBuilder):
    """Build prompts for Sushi Go! AI agents."""

    def build_system_prompt(self) -> str:
        """System prompt with Sushi Go! rules."""
        descriptions = "\n".join(
            f"  - {card.card_name}: {CARD_DESCRIPTIONS[card]}"
            for card in CardType
        )

        return f"""You are playing Sushi Go!, a card drafting game where you pick cards to build the best sushi meal!

GAME RULES:
- Each round, you start with a hand of cards
- Each turn: Pick 1 card to KEEP, then pass remaining cards to next player
- Cards you pick go into your collection and score points
- After passing all cards, the round ends and scores are tallied
- Play 3 rounds total, highest total score wins!

CARD TYPES AND SCORING:
{descriptions}

KEY STRATEGIES:
1. **Maki Rolls**: Collect more maki icons than others (6 pts for most, 3 pts for 2nd)
2. **Sets**: Complete sets for big points
   - 2 Tempura = 5 points
   - 3 Sashimi = 10 points (very valuable!)
3. **Dumplings**: More is better (1=1, 2=3, 3=6, 4=10, 5+=15)
4. **Nigiri**: Immediate points, look for Wasabi to triple them
5. **Pudding**: Keep track across all rounds! Most/least affects final score

STRATEGIC TIPS:
- Early round: Start sets (Sashimi, Tempura) or grab Wasabi
- Mid round: Complete sets, watch what others are collecting
- Late round: Deny opponents' sets, secure maki if competitive
- Pudding: Balance with round points, but don't ignore
- Wasabi: Only valuable if you can get nigiri to follow

CARD DRAFTING STRATEGY:
- Pick cards that complete YOUR sets
- Deny cards that complete OPPONENT sets
- Watch for rare cards (Squid Nigiri, Wasabi)
- Don't over-commit to a single strategy

OUTPUT FORMAT:
- card_to_play: Exact name of card in your hand to play
- reasoning: Your strategic thinking
"""

    def build_user_prompt(self, game: "SushiGoGame", player: "Player") -> str:
        """Build user prompt with current game state."""
        from boardgamepy.protocols import SimpleViewContext

        player_idx = player.player_idx
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Current hand
        hand = game.board.hands[player_idx]
        hand_str = ", ".join(f'"{card.name}"' for card in hand)

        # Current collection analysis
        collection = game.board.collections[player_idx]

        tempura_count = sum(1 for c in collection if c.type == CardType.TEMPURA)
        sashimi_count = sum(1 for c in collection if c.type == CardType.SASHIMI)
        dumpling_count = sum(1 for c in collection if c.type == CardType.DUMPLING)
        maki_count = sum(c.type.maki_value for c in collection if c.is_maki)
        wasabi_count = sum(1 for c in collection if c.type == CardType.WASABI)
        nigiri = [c for c in collection if c.is_nigiri]

        # Build prompt
        parts = [
            f"You are Player {player_idx + 1}.",
            "",
            f"Round {game.state.current_round}/3",
            "",
            board_view,
            "",
            "YOUR CURRENT HAND (choose 1 card to play):",
            f"  {hand_str}",
            "",
            "YOUR COLLECTION ANALYSIS:",
            f"  Tempura: {tempura_count} (need 2 for 5 pts)",
            f"  Sashimi: {sashimi_count} (need 3 for 10 pts)",
            f"  Dumpling: {dumpling_count} (1/2/3/4/5+ = 1/3/6/10/15 pts)",
            f"  Maki icons: {maki_count} (most = 6 pts, 2nd = 3 pts)",
            f"  Wasabi: {wasabi_count} (triples next nigiri)",
        ]

        if nigiri:
            nigiri_str = ", ".join(str(n) for n in nigiri)
            parts.append(f"  Nigiri: {nigiri_str}")

        parts.append("")

        # Current scores
        if game.state.round_scores:
            parts.append("CURRENT SCORES:")
            for i in range(game.board.num_players):
                total = game.state.total_scores.get(i, 0)
                parts.append(f"  Player {i + 1}: {total} points")
            parts.append("")

        parts.append("Choose which card to play. Consider:")
        parts.append("  - Completing your sets (Sashimi is 10 pts!)")
        parts.append("  - Building maki to compete for 6/3 bonus points")
        parts.append("  - Wasabi + Nigiri combo (triple points)")
        parts.append("  - Denying strong cards to opponents")

        return "\n".join(parts)

    def build_messages(self, game: "SushiGoGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
