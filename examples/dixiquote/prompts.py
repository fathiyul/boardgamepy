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
- Situation cards score 1 point for some-but-not-all votes
- Situation cards score 0 points for zero votes
- Situation cards score -1 point for all votes (too obvious - penalty)
- Players who correctly guess the Storyteller's card earn +1 bonus point
- Storyteller scores 1 point if at least 2 different cards get votes, including their own card

The game rewards interpretable clues and penalizes being too obvious or totally unrelated.
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

Task: Give a poetic, quote-like clue that captures the emotional experience of this situation.

IMPORTANT: Your quote should NOT be a paraphrase or restatement of the situation text. Instead, create a quote that expresses what someone experiencing this situation might say, think, or feel - like a cry, prayer, realization, or emotional outburst.

Your quote should:
- Be a single line or sentence fragment
- Sound like a character's voice speaking from within the experience
- Express raw emotion, longing, despair, hope, or realization
- Be a subjective experience, NOT an objective description
- Be poetic and evocative, capturing the mood rather than the details
- Create multiple plausible readings

Examples:
- Situation: "During the coronation, the throne remains empty while the crowd waits."
  Good quote: "Oh divine heavens above, send us a shepherd in this hour of silence."
  Bad quote: "The empty throne waits for a new king."

- Situation: "The shadow enters the room several seconds before the person does."
  Good quote: "First comes the darkness that men carry in their hearts."
  Bad quote: "The shade arrives before its master."

Remember: To score, at least 2 cards must get votes including your own. If your clue is too obvious, all vote for you and you get -1 point. If it's totally unrelated, no one votes for you and you get 0 points.

Output format (JSON only):
{{
  "quote": "Your poetic quote expressing the emotional experience",
  "reasoning": "Brief explanation of the emotional connection"
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

Remember: You score 1 point if you get some votes, 0 points for zero votes, and -1 point if you get all votes.
You also earn +1 bonus point if you correctly vote for the Storyteller's card.

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

        # Get all submitted situations (shuffled), then remove player's own submission
        all_situations = game.state.get_all_submitted_situations()
        player_submission = game.state.submitted_situations.get(player.player_idx, None)
        votable_situations = [s for s in all_situations if s != player_submission]
        situations_text = "\n".join([f"{i + 1}. {situation}" for i, situation in enumerate(votable_situations)])

        return f"""
{rules}

The Storyteller's quote:
"{quote}"

Available situations to vote for:
{situations_text}

Note: Your own submission has been removed from the list as you cannot vote for yourself.

Task: Vote for the situation you believe is the Storyteller's original card.

Strategy tips:
- Look for the situation that best matches the quote's theme, mood, or interpretation
- Consider which situation the quote most naturally frames
- You earn +1 bonus point if you correctly guess the Storyteller's card

Output format (JSON only):
{{
  "situation": "Exact text of the situation you vote for",
  "reasoning": "Brief explanation of why you think this is the Storyteller's card"
}}
""".strip()
