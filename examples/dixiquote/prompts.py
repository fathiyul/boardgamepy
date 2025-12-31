"""DixiQuote prompt builders for AI players."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder

if TYPE_CHECKING:
    from game import DixiQuoteGame
    from boardgamepy.core.player import Player


def get_rules_prompt() -> str:
    """Get DixiQuote rules explanation."""
    return """
You are playing DixiQuote, a storytelling game about how moments are remembered.

Game Overview:
- 3-8 players take turns being the Storyteller
- Each player has 6 situation cards (narrative descriptions of events)
- The Storyteller provides a poetic quote-like clue
- Other players submit situation cards that fit the quote
- Players vote on which situation best matches the quote
- The goal is to be interpretable, not obvious

Round Structure:
1. Storyteller secretly chooses a situation card
2. Storyteller gives a quote-like clue inspired by that situation
3. Other players submit one situation card from their hand that fits the clue
4. All situations (including Storyteller's) are revealed
5. Players vote for the situation they think matches the quote (cannot vote for their own)

Scoring:
- Situation cards score 2 points for some-but-not-all votes
- Situation cards score 1 point for zero votes
- Situation cards score 0 points for all votes (too obvious)
- Storyteller scores 3 points if at least 2 different cards get votes and no card gets all votes

The game rewards ambiguity and penalizes being too obvious or too obscure.
""".strip()


class StorytellerChoosePromptBuilder(PromptBuilder["DixiQuoteGame"]):
    """Prompt builder for Storyteller choosing a situation."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are playing DixiQuote as the Storyteller. "
            "Choose a situation card from your hand that you can give a good poetic quote for. "
            "Output ONLY valid JSON matching the provided schema."
        )

    def build_user_prompt(self, game: "DixiQuoteGame", player: "Player") -> str:
        """Build user prompt with game context."""
        rules = get_rules_prompt()

        # Get player's hand
        hand = game.get_player_hand(player.player_idx)
        hand_text = "\n".join([f"{i + 1}. {situation}" for i, situation in enumerate(hand)])

        # Get current scores
        scores = [f"Player {i + 1}: {score}" for i, score in game.state.scores.items()]
        scores_text = ", ".join(scores)

        return f"""
{rules}

You are the Storyteller for this round.

Current Scores:
{scores_text}

Your hand of situation cards:
{hand_text}

Task: Choose ONE situation card from your hand that you can give an interesting poetic quote for.

The best situations to choose are ones that:
- Can be framed in multiple ways
- Have emotional or symbolic depth
- Connect to universal themes

Output format (JSON only):
{{
  "situation": "Exact text of the situation card you choose",
  "reasoning": "Brief explanation of why you chose this situation"
}}
""".strip()


class StorytellerQuotePromptBuilder(PromptBuilder["DixiQuoteGame"]):
    """Prompt builder for Storyteller giving a quote."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are playing DixiQuote as the Storyteller. "
            "Give a poetic, quote-like clue for your chosen situation. "
            "Output ONLY valid JSON matching the provided schema."
        )

    def build_user_prompt(self, game: "DixiQuoteGame", player: "Player") -> str:
        """Build user prompt with game context."""
        rules = get_rules_prompt()

        # Get chosen situation
        situation = game.state.storyteller_situation or ""

        # Get history
        history_text = game.history.to_prompt(max_rounds=2)

        return f"""
{rules}

You are the Storyteller for this round.

Your chosen situation:
"{situation}"

{history_text}

Task: Give a poetic, quote-like clue that frames or interprets this situation.

Your quote should:
- Be a single line or sentence fragment
- Sound like it could appear in a book, film, or poem
- Express a way of remembering, framing, or interpreting the situation
- Be evocative but not too literal
- Create multiple plausible readings

Remember: If your clue is too obvious, your card will get all votes and you'll score 0.
If it's too obscure, no cards will get votes and you'll also score poorly.
Aim for interpretable ambiguity.

Output format (JSON only):
{{
  "quote": "Your poetic quote",
  "reasoning": "Brief explanation of how this quote relates to your situation"
}}
""".strip()


class SubmitSituationPromptBuilder(PromptBuilder["DixiQuoteGame"]):
    """Prompt builder for submitting a situation card."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are playing DixiQuote. "
            "Submit a situation card from your hand that fits the Storyteller's quote. "
            "Output ONLY valid JSON matching the provided schema."
        )

    def build_user_prompt(self, game: "DixiQuoteGame", player: "Player") -> str:
        """Build user prompt with game context."""
        rules = get_rules_prompt()

        # Get the quote
        quote = game.state.storyteller_quote or ""

        # Get player's hand
        hand = game.get_player_hand(player.player_idx)
        hand_text = "\n".join([f"{i + 1}. {situation}" for i, situation in enumerate(hand)])

        # Get current scores
        scores = [f"Player {i + 1}: {score}" for i, score in game.state.scores.items()]
        scores_text = ", ".join(scores)

        return f"""
{rules}

Current Scores:
{scores_text}

The Storyteller's quote:
"{quote}"

Your hand of situation cards:
{hand_text}

Task: Choose ONE situation card from your hand that fits the quote.

Strategy tips:
- Look for situations that could plausibly match the quote's theme or mood
- Don't be too literal - interpretive connections are better
- Consider that other players will also be submitting cards
- Your card should be a reasonable match but not the only possible match

Remember: You score 2 points if you get some votes, 1 point for zero votes, and 0 points if you get all votes.

Output format (JSON only):
{{
  "situation": "Exact text of the situation card you choose",
  "reasoning": "Brief explanation of how this situation fits the quote"
}}
""".strip()


class VotePromptBuilder(PromptBuilder["DixiQuoteGame"]):
    """Prompt builder for voting."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are playing DixiQuote. "
            "Vote for the situation that you think is the Storyteller's card. "
            "Output ONLY valid JSON matching the provided schema."
        )

    def build_user_prompt(self, game: "DixiQuoteGame", player: "Player") -> str:
        """Build user prompt with game context."""
        rules = get_rules_prompt()

        # Get the quote
        quote = game.state.storyteller_quote or ""

        # Get all submitted situations (shuffled)
        all_situations = game.state.get_all_submitted_situations()
        situations_text = "\n".join([f"{i + 1}. {situation}" for i, situation in enumerate(all_situations)])

        # Get which one was player's submission (if any)
        player_submission = game.state.submitted_situations.get(player.player_idx, None)

        return f"""
{rules}

The Storyteller's quote:
"{quote}"

All submitted situations (including the Storyteller's):
{situations_text}

Task: Vote for the situation you believe is the Storyteller's original card.

Strategy tips:
- Look for the situation that best matches the quote's theme, mood, or interpretation
- Consider which situation the quote most naturally frames
- Remember you cannot vote for your own submission{f' (which was: "{player_submission}")' if player_submission else ''}

Output format (JSON only):
{{
  "situation": "Exact text of the situation you vote for",
  "reasoning": "Brief explanation of why you think this is the Storyteller's card"
}}
""".strip()
