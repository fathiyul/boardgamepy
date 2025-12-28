"""Wavelength game actions."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

from boardgamepy import Action

if TYPE_CHECKING:
    from game import WavelengthGame
    from boardgamepy.core.player import Player


class GiveClueOutput(BaseModel):
    """LLM structured output for psychic giving a clue."""

    clue: str = Field(
        ...,
        description="A creative clue that hints at the target position on the spectrum. Be creative and subtle!",
    )
    reasoning: str | None = Field(None, description="Why this clue matches the target position")


class GuessPositionOutput(BaseModel):
    """LLM structured output for team guessing position."""

    position: int = Field(
        ...,
        description="Your guess for the target position (0-100, where 0=left extreme, 100=right extreme)",
    )
    reasoning: str | None = Field(None, description="How you interpreted the clue")


class PredictDirectionOutput(BaseModel):
    """LLM structured output for opponent predicting direction."""

    prediction: str = Field(
        ..., description="Predict if their guess is 'left' or 'right' of the actual target"
    )
    reasoning: str | None = Field(None, description="Why you think the guess is off in this direction")


class GiveClueAction(Action["WavelengthGame"]):
    """Action for psychic to give a clue."""

    name = "give_clue"
    display_name = "Give Clue"
    OutputSchema = GiveClueOutput
    roles = ["Psychic"]

    def validate(self, game: "WavelengthGame", player: "Player", clue: str, **kwargs) -> bool:
        """Validate clue giving."""
        if game.state.phase != "psychic_clue":
            return False
        if not clue or len(clue.strip()) == 0:
            return False
        return True

    def apply(self, game: "WavelengthGame", player: "Player", clue: str, **kwargs) -> None:
        """Apply the clue."""
        game.board.psychic_clue = clue

        game.history.add_action(
            self,
            player,
            clue=clue,
            team=game.state.get_current_team_name(),
        )

        # Advance to team guessing phase
        game.state.phase = "team_guess"

    def to_history_record(self, player: "Player", clue: str, team: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "give_clue",
            "team": team,
            "clue": clue,
        }


class GuessPositionAction(Action["WavelengthGame"]):
    """Action for team to guess the position."""

    name = "guess_position"
    display_name = "Guess Position"
    OutputSchema = GuessPositionOutput
    roles = ["Guesser"]

    def validate(self, game: "WavelengthGame", player: "Player", position: int, **kwargs) -> bool:
        """Validate position guess."""
        if game.state.phase != "team_guess":
            return False
        if position < 0 or position > 100:
            return False
        return True

    def apply(self, game: "WavelengthGame", player: "Player", position: int, **kwargs) -> None:
        """Apply the guess."""
        game.board.set_dial_position(position)

        game.history.add_action(
            self,
            player,
            position=position,
            team=game.state.get_current_team_name(),
        )

        # Advance to opponent prediction phase
        game.state.phase = "opponent_predict"

    def to_history_record(self, player: "Player", position: int, team: str, **params) -> dict:
        """Convert to history record."""
        return {
            "type": "guess_position",
            "team": team,
            "position": position,
        }


class PredictDirectionAction(Action["WavelengthGame"]):
    """Action for opponent to predict direction."""

    name = "predict_direction"
    display_name = "Predict Direction"
    OutputSchema = PredictDirectionOutput
    roles = ["Opponent"]

    def validate(
        self, game: "WavelengthGame", player: "Player", prediction: str, **kwargs
    ) -> bool:
        """Validate prediction."""
        if game.state.phase != "opponent_predict":
            return False
        if prediction.lower() not in ["left", "right"]:
            return False
        return True

    def apply(self, game: "WavelengthGame", player: "Player", prediction: str, **kwargs) -> None:
        """Apply the prediction and calculate score."""
        game.board.set_opponent_prediction(prediction)

        # Calculate score
        base_points, opponent_correct = game.board.calculate_score()
        final_points = base_points - (1 if opponent_correct else 0)
        final_points = max(0, final_points)  # Can't go negative

        # Award points
        game.state.team_scores[game.state.current_team] += final_points

        game.history.add_action(
            self,
            player,
            prediction=prediction,
            base_points=base_points,
            opponent_correct=opponent_correct,
            final_points=final_points,
        )

        # Check for winner
        if game.state.team_scores[game.state.current_team] >= game.state.target_score:
            game.state.is_over = True
            game.state.winner = game.state.current_team
            return

        # Advance to reveal (handled by game loop - will start new round)
        game.state.phase = "reveal"

    def to_history_record(
        self,
        player: "Player",
        prediction: str,
        base_points: int,
        opponent_correct: bool,
        final_points: int,
        **params,
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "predict_direction",
            "prediction": prediction,
            "base_points": base_points,
            "opponent_correct": opponent_correct,
            "final_points": final_points,
        }
