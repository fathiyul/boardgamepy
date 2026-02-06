"""Codenames prompt builders for AI players."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder
from boardgamepy.protocols import SimpleViewContext

if TYPE_CHECKING:
    from .game import CodenamesGame
    from .state import Team
    from boardgamepy.core.player import Player


def get_rules_prompt() -> str:
    """Get Codenames rules explanation."""
    return """
You are playing the board game Codenames.
There are two teams: Red and Blue. Each team has a Spymaster and a Guesser.
The board contains 25 codenames. Each codename secretly belongs to one of:
- 9 Red Agent
- 8 Blue Agent
- 7 Civilian (neutral)
- 1 Assassin (instant loss)

Red always goes first in a round.

The game is played in rounds. In each round:
1. The Red Spymaster gives a one-word clue and a number.
2. The Red Guesser guesses cards, one at a time.
   - Wrong guesses (Civilian or Blue Agent) do NOT end the turn.
   - Continue guessing until the guess count is exhausted.
   - If they reveal the Assassin: their team loses immediately.
3. Then the Blue team takes their turn in the same way.

Goal: The first team to reveal all of their own agents wins.

Important constraints:
- Spymasters must not reveal secret card colors.
- Clues must relate only to word meanings, not spelling/letters/positions.
- Clues cannot be:
  * The same word as a card on the board
  * A translation of a card on the board
  * Multi-word phrases
- Guessers make the best guess from visible cards only.

Penalty rule:
- If a Spymaster gives a clue that exactly matches any remaining codename on the table, that team immediately loses.
""".strip()


def get_player_prompt(team: str, role: str) -> str:
    """Get role-specific instructions."""
    if role == "Spymaster":
        return f"""
You are the {team} Spymaster.
Your partner is the {team} Guesser.
You can see which cards belong to each team.

Your goal: Help the {team} Guesser find all {team} Agent cards,
while avoiding clues that lead to Blue Agents, Civilians, or the Assassin.

Critical rule: If your clue matches any remaining codename on the board, your team instantly loses.

Output format: a single-word clue and a number.
Example:
Clue: Animal 2
""".strip()

    # role == "Operatives"
    return f"""
You are the {team} Guesser.
You do not know the hidden card types.

You will be shown a list of REMAINING cards that are still hidden.
You must ONLY guess codenames from that remaining-cards list.
Do NOT guess words that are not listed there, even if they appear in the history.

Your goal: Guess the card that best matches your Spymaster's latest clue.
If you believe no safe guesses remain, you may pass.
""".strip()


class SpymasterPromptBuilder(PromptBuilder["CodenamesGame"]):
    """Prompt builder for Spymaster role."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are an expert Codenames Spymaster AI. "
            "Follow the rules strictly and output ONLY valid JSON "
            "matching the provided schema."
        )

    def build_user_prompt(self, game: "CodenamesGame", player: "Player") -> str:
        """Build user prompt with game context."""
        rules = get_rules_prompt()
        role_prompt = get_player_prompt(player.team, player.role)  # type: ignore

        # Get board view for spymaster
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Get history
        history_text = game.history.to_prompt(max_rounds=3)

        # Get state
        state_line = (
            f"Red agents remaining: {game.state.red_remaining}. "
            f"Blue agents remaining: {game.state.blue_remaining}."
        )

        return f"""
{rules}

{role_prompt}

Game state:
{state_line}

Board (you see all hidden card types, do NOT reveal them explicitly):
{board_view}

{history_text}

Instructions for your output:
- Give ONE single-word clue (no spaces) and a number.
- The clue MUST NOT be identical to any remaining codename.
- If your clue matches any remaining codename, your team LOSES immediately.
- The clue MUST relate to MEANING only (not letters, spelling, positions, etc.).
- Aim to connect as many of your own team cards as safely as possible.
- Avoid clues that strongly suggest opponent cards, civilians, or the assassin.

Output format (JSON only, no extra text):
{{
  "clue": "SingleWord",
  "count": 2,
  "reasoning": "Very short explanation of which words this clue connects and why."
}}
""".strip()


class OperativesPromptBuilder(PromptBuilder["CodenamesGame"]):
    """Prompt builder for Operatives role."""

    def build_system_prompt(self) -> str:
        """Build system message."""
        return (
            "You are an expert Codenames Guesser AI. "
            "Follow the rules strictly and output ONLY valid JSON "
            "matching the provided schema."
        )

    def build_user_prompt(self, game: "CodenamesGame", player: "Player") -> str:
        """Build user prompt with game context."""
        rules = get_rules_prompt()
        role_prompt = get_player_prompt(player.team, player.role)  # type: ignore

        # Get board view for operatives
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Get history
        history_text = game.history.to_prompt(max_rounds=3)

        # Get state
        state_line = (
            f"Red agents remaining: {game.state.red_remaining}. "
            f"Blue agents remaining: {game.state.blue_remaining}."
        )

        # Get latest clue
        clue, count = self._get_latest_clue_for_team(game, player.team)  # type: ignore
        if clue is None:
            latest_clue_text = "No clue has been given to your team yet."
        else:
            latest_clue_text = f"Latest clue from your Spymaster: {clue} {count}"

        return f"""
{rules}

{role_prompt}

Game state:
{state_line}

{latest_clue_text}
You have {game.state.guesses_remaining} guesses remaining this turn.

Remaining hidden cards you may guess from:
{board_view}

{history_text}

Important instructions:
- You may ONLY guess codenames from the 'Remaining hidden cards' list above.
- NEVER guess a word that is not in that list.
- If you think any guess is too risky, you may choose to PASS instead.
- Remember that picking the Assassin loses the game immediately.

Your task:
1. Decide whether to 'guess' or 'pass'.
2. If 'guess', pick exactly ONE codename from the list.
3. Provide a very short reasoning.

Output format (JSON only, no extra text):
{{
  "action": "guess" | "pass",
  "codename": "ChosenCodename or null if passing",
  "reasoning": "Very short explanation of why you guessed or passed."
}}
""".strip()

    def _get_latest_clue_for_team(self, game: "CodenamesGame", team: str) -> tuple[str | None, int | None]:
        """Get the most recent clue given to this team."""
        for round_ in reversed(game.history.rounds):
            for action in reversed(round_.actions):
                if action.get("type") == "clue" and action.get("team") == team:
                    return action.get("clue"), action.get("count")
        return None, None
