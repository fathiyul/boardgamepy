"""Coup game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder
from characters import CHARACTER_ABILITIES, CharacterType

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import CoupGame


class CoupPromptBuilder(PromptBuilder):
    """Build prompts for Coup AI agents."""

    def build_system_prompt(self) -> str:
        """System prompt with Coup rules."""
        abilities_text = "\n".join(
            f"  - {char.char_name}: {CHARACTER_ABILITIES[char]}" for char in CharacterType
        )

        return f"""You are playing Coup, a bluffing and deduction card game.

GAME OBJECTIVE:
- Be the last player with influence (character cards)
- Each player starts with 2 influence cards (hidden from others)
- When you lose influence, you reveal a card
- Lose both cards and you're eliminated

YOUR INFLUENCE:
- You have 2 hidden character cards
- You can CLAIM to be any character and use their ability (even if you don't have it!)
- Others can challenge your claim
- If challenged and you DON'T have the card: you lose influence
- If challenged and you DO have it: challenger loses influence

AVAILABLE ACTIONS:

BASIC ACTIONS (always available, can't be challenged):
- income: Take 1 coin
- foreign_aid: Take 2 coins (can be blocked by Duke)
- coup: Pay 7 coins to eliminate target's influence (can't be blocked/challenged)

CHARACTER ACTIONS (can be challenged if you don't have the character):
{abilities_text}

IMPORTANT RULES:
- If you have 10+ coins, you MUST coup
- Coup costs 7 coins and always succeeds
- You can BLUFF - claim characters you don't have!
- In this simplified version, challenges and blocks are not fully implemented

STRATEGY TIPS:
- Build coins for coups (7 coins needed)
- Bluff strategically - claim characters to use their abilities
- Track what others claim and what's been revealed
- Duke (Tax) is powerful for coin generation
- Captain (Steal) disrupts others' coin accumulation
- Assassinate costs 3 coins but cheaper than Coup
- Keep at least one strong character for defense

OUTPUT FORMAT:
- action: Choose one action to perform
- target_player: Required for coup, assassinate, steal (player number 1-6)
- reasoning: Your strategic thinking
"""

    def build_user_prompt(self, game: "CoupGame", player: "Player") -> str:
        """Build user prompt with current game state."""
        from boardgamepy.protocols import SimpleViewContext

        player_idx = game.state.current_player_idx
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        coins = game.board.coins[player_idx]
        influence_count = game.board.get_influence_count(player_idx)

        # Build prompt
        parts = [
            f"You are Player {player_idx + 1}.",
            "",
            board_view,
            "",
            f"You have {coins} coins and {influence_count} influence remaining.",
            "",
        ]

        # Mandatory coup warning
        if coins >= 10:
            parts.append("⚠️ WARNING: You have 10+ coins. You MUST perform a Coup!")
            parts.append("")

        # Available actions
        parts.append("AVAILABLE ACTIONS:")
        parts.append("  - income: Take 1 coin")
        parts.append("  - foreign_aid: Take 2 coins")

        if coins >= 7:
            targetable = [
                i + 1
                for i in range(game.board.num_players)
                if i != player_idx and game.board.has_influence(i)
            ]
            if targetable:
                targets = ", ".join(str(p) for p in targetable)
                parts.append(f"  - coup: Pay 7 coins, eliminate target (targets: {targets})")

        parts.append("  - tax: Claim Duke, take 3 coins")

        if coins >= 3:
            targetable = [
                i + 1
                for i in range(game.board.num_players)
                if i != player_idx and game.board.has_influence(i)
            ]
            if targetable:
                targets = ", ".join(str(p) for p in targetable)
                parts.append(
                    f"  - assassinate: Claim Assassin, pay 3 coins, eliminate target (targets: {targets})"
                )

        targetable = [
            i + 1
            for i in range(game.board.num_players)
            if i != player_idx and game.board.has_influence(i)
        ]
        if targetable:
            targets = ", ".join(str(p) for p in targetable)
            parts.append(
                f"  - steal: Claim Captain, steal 2 coins from target (targets: {targets})"
            )

        parts.append("  - exchange: Claim Ambassador, swap cards with deck")
        parts.append("")

        # Recent history
        if game.history.rounds:
            parts.append("RECENT ACTIONS:")
            history_text = game.history.to_prompt(max_rounds=1)
            parts.append(history_text)
            parts.append("")

        parts.append("Choose your action.")

        return "\n".join(parts)

    def build_messages(self, game: "CoupGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
