"""Actions for Rock Paper Scissors games."""

from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field
from boardgamepy import Action

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import RPSGame
    from strategy_game import StrategyRPSGame


class ChoiceOutput(BaseModel):
    """LLM output schema for basic RPS choice."""
    choice: str = Field(..., description="Your choice: rock, paper, or scissors")
    reasoning: str | None = Field(None, description="Why you made this choice (optional)")


class ChooseAction(Action["RPSGame"]):
    """Action for choosing rock, paper, or scissors in basic RPS."""

    name = "choose"
    display_name = "Choose Rock/Paper/Scissors"
    OutputSchema = ChoiceOutput

    def validate(self, game: "RPSGame", player: "Player", choice: str) -> bool:
        """Validate the choice is valid."""
        choice = choice.lower()
        if choice not in ["rock", "paper", "scissors"]:
            return False

        # Check if player already made a choice this round
        state = game.state
        if player == game.players[0] and state.player1_choice is not None:
            return False
        if player == game.players[1] and state.player2_choice is not None:
            return False

        return True

    def apply(self, game: "RPSGame", player: "Player", choice: str, **params):
        """Apply the choice to game state."""
        choice = choice.lower()
        state = game.state

        # Record the choice
        if player == game.players[0]:
            state.player1_choice = choice
        else:
            state.player2_choice = choice

        # If both players have chosen, resolve the round
        if state.player1_choice and state.player2_choice:
            self._resolve_round(game)

        # Log the action
        game.history.add_action(self, player, choice=choice)

    def _resolve_round(self, game: "RPSGame"):
        """Determine winner of the round and update scores."""
        state = game.state
        p1_choice = state.player1_choice
        p2_choice = state.player2_choice

        # Determine winner
        if p1_choice == p2_choice:
            # Tie
            pass
        elif (
            (p1_choice == "rock" and p2_choice == "scissors") or
            (p1_choice == "paper" and p2_choice == "rock") or
            (p1_choice == "scissors" and p2_choice == "paper")
        ):
            state.player1_score += 1
        else:
            state.player2_score += 1

        # Save choices for display before resetting
        state.last_player1_choice = p1_choice
        state.last_player2_choice = p2_choice

        # Move to next round
        state.current_round += 1
        state.player1_choice = None
        state.player2_choice = None

    def to_history_record(self, player: "Player", choice: str, **params):
        """Convert action to history record."""
        return {
            "type": "choose",
            "player": player.name,
            "choice": choice
        }


# ============================================================================
# STRATEGIC RPS ACTIONS
# ============================================================================

# Win conditions (standard RPS rules)
BEATS = {
    "rock": ["scissors"],
    "paper": ["rock"],
    "scissors": ["paper"],
}


class StrategyChoiceOutput(BaseModel):
    """LLM output schema for strategic RPS."""
    choice: str = Field(
        ...,
        description="Your choice: rock, paper, or scissors"
    )
    reasoning: str | None = Field(
        None,
        description="Strategic reasoning for this choice (consider the effects for this round)"
    )


class StrategyChooseAction(Action["StrategyRPSGame"]):
    """Strategic choice action with risk/reward."""

    name = "choose"
    display_name = "Make Strategic Choice"
    OutputSchema = StrategyChoiceOutput

    def validate(self, game: "StrategyRPSGame", player: "Player", choice: str) -> bool:
        """Validate choice."""
        choice = choice.lower()

        # Valid choice (only rock, paper, scissors)
        if choice not in ["rock", "paper", "scissors"]:
            return False

        # Check if already chosen
        state = game.state
        if player == game.players[0] and state.player1_choice is not None:
            return False
        if player == game.players[1] and state.player2_choice is not None:
            return False

        return True

    def apply(self, game: "StrategyRPSGame", player: "Player", choice: str, **params):
        """Apply choice and resolve if both players chose."""
        choice = choice.lower()
        state = game.state

        # Record choice
        if player == game.players[0]:
            state.player1_choice = choice
        else:
            state.player2_choice = choice

        # Resolve round if both chose
        if state.player1_choice and state.player2_choice:
            self._resolve_round(game)

        # Log action
        game.history.add_action(self, player, choice=choice)

    def _resolve_round(self, game: "StrategyRPSGame"):
        """Resolve the round with strategic effects."""
        state = game.state
        p1_choice = state.player1_choice
        p2_choice = state.player2_choice

        # Save this round's effects for UI before they change
        import copy
        state.last_effect_mapping = copy.deepcopy(state.effect_mapping)

        # Determine winner
        if p1_choice == p2_choice:
            # Tie - no effects
            pass
        elif p2_choice in BEATS[p1_choice]:
            # Player 1 wins
            self._apply_win(state, p1_choice, p2_choice, player_num=1)
        else:
            # Player 2 wins
            self._apply_win(state, p2_choice, p1_choice, player_num=2)

        # Check win conditions
        self._check_win_conditions(state)

        # Save choices for display before resetting
        state.last_player1_choice = p1_choice
        state.last_player2_choice = p2_choice

        # Reset for next round
        if not state.game_over:
            state.current_round += 1
            state.player1_choice = None
            state.player2_choice = None

            # Randomize effects for next round
            from strategy_game import randomize_effects
            state.effect_mapping = randomize_effects()

    def _apply_win(self, state, winner_choice: str, loser_choice: str, player_num: int):
        """Apply win/lose effects based on this round's effect mapping."""
        # Get effects from current round's mapping
        win_effect = state.effect_mapping[winner_choice]
        lose_effect = state.effect_mapping[loser_choice]

        # Winner gains points
        if player_num == 1:
            state.player1_score = min(state.player1_score + win_effect["win_points"], 10)
        else:
            state.player2_score = min(state.player2_score + win_effect["win_points"], 10)

        # Loser takes penalty
        if lose_effect["lose_type"] == "points":
            # Lose victory points (minimum 0)
            if player_num == 1:
                state.player2_score = max(state.player2_score - lose_effect["lose_effect"], 0)
            else:
                state.player1_score = max(state.player1_score - lose_effect["lose_effect"], 0)
        elif lose_effect["lose_type"] == "health":
            # Lose health
            if player_num == 1:
                state.player2_health -= lose_effect["lose_effect"]
            else:
                state.player1_health -= lose_effect["lose_effect"]

    def _check_win_conditions(self, state):
        """Check if someone won."""
        # Check points
        if state.player1_score >= 10:
            state.game_over = True
            state.winner = "Player 1"
        elif state.player2_score >= 10:
            state.game_over = True
            state.winner = "Player 2"

        # Check health
        elif state.player1_health <= 0:
            state.game_over = True
            state.winner = "Player 2"
        elif state.player2_health <= 0:
            state.game_over = True
            state.winner = "Player 1"

        # Check max rounds
        elif state.current_round >= state.max_rounds:
            state.game_over = True
            # Winner is player with higher score
            if state.player1_score > state.player2_score:
                state.winner = "Player 1"
            elif state.player2_score > state.player1_score:
                state.winner = "Player 2"
            else:
                state.winner = "Tie"

    def to_history_record(self, player: "Player", choice: str, **params):
        """Convert to history record."""
        return {
            "type": "strategic_choose",
            "player": player.name,
            "choice": choice
        }
