"""Codenames game actions."""

from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field

from boardgamepy import Action

if TYPE_CHECKING:
    from game import CodenamesGame
    from state import Team
    from boardgamepy.core.player import Player


class ClueOutput(BaseModel):
    """LLM structured output for giving a clue."""

    clue: str = Field(..., description="Single-word clue")
    count: int = Field(..., description="Number of cards this clue connects to", ge=1, le=9)
    reasoning: str | None = Field(None, description="Short explanation of clue choice")


class ClueAction(Action["CodenamesGame"]):
    """Action for spymaster giving a clue to operatives."""

    name = "clue"
    display_name = "Give Clue"
    roles = ["Spymaster"]
    OutputSchema = ClueOutput

    def validate(self, game: "CodenamesGame", player: "Player", clue: str, count: int) -> bool:
        """
        Validate clue action.

        Clue is invalid if:
        - Game is over
        - Operatives are still guessing
        - Clue matches a remaining codename
        """
        if game.state.is_over:
            return False

        if game.state.guesses_remaining > 0:
            return False  # Operatives still guessing

        # Clue cannot match any hidden codename
        hidden_codenames = {
            c.code.lower() for c in game.board.cards.values() if c.state == "Hidden"
        }
        if clue.lower() in hidden_codenames:
            return False

        return True

    def apply(self, game: "CodenamesGame", player: "Player", clue: str, count: int) -> None:
        """
        Apply clue action.

        Sets guesses_remaining and logs the clue.
        """
        # Check for illegal clue (matches codename)
        hidden_codenames = {
            c.code.lower() for c in game.board.cards.values() if c.state == "Hidden"
        }
        if clue.lower() in hidden_codenames:
            # Illegal clue - team loses immediately
            game.state.is_over = True
            game.state.winner = "Blue" if player.team == "Red" else "Red"
            game.state.guesses_remaining = 0
        else:
            # Valid clue
            game.state.guesses_remaining = count

        # Log to history
        game.history.add_action(self, player, clue=clue, count=count)

    def to_history_record(self, player: "Player", clue: str, count: int, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "clue",
            "player": f"{player.team} {player.role}",
            "team": player.team,
            "clue": clue,
            "count": count,
        }


class GuessOutput(BaseModel):
    """LLM structured output for making a guess."""

    action: Literal["guess", "pass"] = Field(..., description="'guess' to choose a codename, 'pass' to stop guessing")
    codename: str | None = Field(None, description="Codename to guess if action == 'guess'")
    reasoning: str | None = Field(None, description="Short explanation of decision")


class GuessAction(Action["CodenamesGame"]):
    """Action for operatives guessing a card."""

    name = "guess"
    display_name = "Make Guess"
    roles = ["Operatives"]
    OutputSchema = GuessOutput

    def validate(self, game: "CodenamesGame", player: "Player", codename: str) -> bool:
        """
        Validate guess action.

        Guess is invalid if:
        - Game is over
        - No guesses remaining
        - Card doesn't exist or is already revealed
        """
        if game.state.is_over:
            return False

        if game.state.guesses_remaining <= 0:
            return False

        card = game.board.find_by_codename(codename)
        return card is not None and card.state == "Hidden"

    def apply(self, game: "CodenamesGame", player: "Player", codename: str):
        """
        Apply guess action.

        Reveals the card, updates counts, checks win conditions, and may end turn.
        """
        # Find and reveal card
        card = game.board.find_by_codename(codename)
        if card is None:
            raise ValueError(f"No card with codename '{codename}'")

        if card.state == "Revealed":
            raise ValueError(f"Card '{codename}' already revealed")

        revealed = game.board.reveal(card.id)
        card_type = revealed.type

        # Log to history
        game.history.add_action(self, player, codename=codename, card_type=card_type)

        # Update state based on card type
        if card_type == "Assassin":
            # Instant loss
            game.state.is_over = True
            game.state.winner = "Blue" if player.team == "Red" else "Red"
            game.state.guesses_remaining = 0
            return card_type

        if card_type == "Red":
            game.state.red_remaining -= 1
            if game.state.red_remaining == 0:
                game.state.is_over = True
                game.state.winner = "Red"
                game.state.guesses_remaining = 0
                return card_type

        if card_type == "Blue":
            game.state.blue_remaining -= 1
            if game.state.blue_remaining == 0:
                game.state.is_over = True
                game.state.winner = "Blue"
                game.state.guesses_remaining = 0
                return card_type

        # House rule: wrong guesses don't end turn, only decrement count
        game.state.guesses_remaining -= 1

        # End turn if no guesses left
        if game.state.guesses_remaining <= 0:
            game._end_team_turn()

        return card_type

    def to_history_record(self, player: "Player", codename: str, card_type: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "guess",
            "player": f"{player.team} {player.role}",
            "team": player.team,
            "codename": codename,
            "card_type": card_type,
        }


class PassAction(Action["CodenamesGame"]):
    """Action for operatives passing (ending turn early)."""

    name = "pass"
    display_name = "Pass"
    roles = ["Operatives"]

    def validate(self, game: "CodenamesGame", player: "Player") -> bool:
        """Validate pass action."""
        if game.state.is_over:
            return False
        return game.state.guesses_remaining > 0

    def apply(self, game: "CodenamesGame", player: "Player") -> None:
        """Apply pass action - end turn."""
        # Log to history
        game.history.add_action(self, player)

        # End turn
        game._end_team_turn()

    def to_history_record(self, player: "Player", **params) -> dict:
        """Convert to history record."""
        return {
            "type": "pass",
            "player": f"{player.team} {player.role}",
            "team": player.team,
        }
