"""Love Letter game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder
from cards import CARD_EFFECTS, CardType

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import LoveLetterGame


class LoveLetterPromptBuilder(PromptBuilder):
    """Build prompts for Love Letter AI agents."""

    def build_system_prompt(self) -> str:
        """System prompt with Love Letter rules."""
        effects_text = "\n".join(
            f"  - {card.card_name} ({card.value}): {CARD_EFFECTS[card]}"
            for card in CardType
        )

        return f"""You are playing Love Letter, a card game of deduction and risk.

GAME RULES:
- Goal: Win rounds by being the last player standing OR having the highest card when the deck runs out
- On your turn: You have 2 cards. You must play 1 card and execute its effect.
- When a player is eliminated, they're out for this round
- The round winner gets a token. First to win enough tokens wins the game!

CARD EFFECTS:
{effects_text}

IMPORTANT RULES:
- If you have Countess AND (King OR Prince), you MUST play Countess
- Protected players (Handmaid) cannot be targeted by other cards
- You can target yourself with Prince
- If you play or discard Princess, you're immediately eliminated

STRATEGY TIPS:
- Track discarded cards to deduce what others might have
- Use Priest to gain information
- Baron is risky but can eliminate high-value cards
- Handmaid provides safety but uses your turn
- Guard is good for elimination if you can deduce their card
- Keep Princess safe! Never play or discard it.

OUTPUT FORMAT:
- card_to_play: Which card from your hand to play (exact card name)
- target_player: Player number (1-4) if card requires target, otherwise null
- guess_card: For Guard only - which card type to guess (cannot guess Guard)
- reasoning: Your strategic thinking
"""

    def build_user_prompt(self, game: "LoveLetterGame", player: "Player") -> str:
        """Build user prompt with current game state."""
        from boardgamepy.protocols import SimpleViewContext

        player_idx = game.state.current_player_idx
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Get current hand
        hand = game.board.hands[player_idx]
        hand_str = " and ".join(f"{card.name} ({card.value})" for card in hand)

        # Get targetable players
        targetable = game.board.get_targetable_players(player_idx)
        if targetable:
            target_str = ", ".join(str(p + 1) for p in targetable)
            target_info = f"You can target: Player {target_str}"
        else:
            target_info = "No players can be targeted (all eliminated or protected)"

        # Build prompt
        parts = [
            f"You are Player {player_idx + 1}.",
            "",
            "YOUR HAND (you must play 1 card):",
            f"  {hand_str}",
            "",
            target_info,
            "",
            board_view,
            "",
        ]

        # Add game score
        parts.append("GAME SCORE:")
        for i in range(game.board.num_players):
            tokens = game.state.scores.get(i, 0)
            parts.append(f"  Player {i + 1}: {tokens} token(s)")
        parts.append(f"  (Need {game.state.target_tokens} tokens to win)")
        parts.append("")

        # Add recent history
        if game.history.rounds:
            parts.append("RECENT PLAYS THIS ROUND:")
            history_text = game.history.to_prompt(max_rounds=1)
            parts.append(history_text)
            parts.append("")

        # Remind about Countess rule
        if len(hand) == 2:
            has_countess = any(c.type == CardType.COUNTESS for c in hand)
            has_king_or_prince = any(c.type in [CardType.KING, CardType.PRINCE] for c in hand)
            if has_countess and has_king_or_prince:
                parts.append("⚠️ IMPORTANT: You MUST play Countess (you have King or Prince)")
                parts.append("")

        parts.append("Make your play. Choose which card to play and any required parameters.")

        return "\n".join(parts)

    def build_messages(self, game: "LoveLetterGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
