"""Basic Rock Paper Scissors game."""

from dataclasses import dataclass
from boardgamepy import Game, GameState, Board, Player, GameHistory
from boardgamepy.protocols import SimpleViewContext, ViewContext
from actions import ChooseAction


@dataclass
class RPSState(GameState):
    """Game state for Rock Paper Scissors."""

    current_round: int = 0
    max_rounds: int = 3
    player1_choice: str | None = None
    player2_choice: str | None = None
    player1_score: int = 0
    player2_score: int = 0

    # Store last round's choices to display
    last_player1_choice: str | None = None
    last_player2_choice: str | None = None

    def is_terminal(self) -> bool:
        """Game ends after max rounds."""
        return self.current_round >= self.max_rounds

    def get_winner(self) -> str | None:
        """Return winner based on final score."""
        if not self.is_terminal():
            return None

        if self.player1_score > self.player2_score:
            return "Player 1"
        elif self.player2_score > self.player1_score:
            return "Player 2"
        return "Tie"


class RPSBoard(Board):
    """Simple board for Rock Paper Scissors."""

    def get_view(self, context: ViewContext) -> str:
        """Return board view - same for all players."""
        state = context.game_state

        view = [
            "=== ROCK PAPER SCISSORS ===",
            f"Round: {state.current_round + 1}/{state.max_rounds}",
            f"Score - Player 1: {state.player1_score} | Player 2: {state.player2_score}",
        ]

        # Show previous round's choices if available
        if state.current_round > 0 and state.last_player1_choice:
            view.append(f"\nLast round:")
            view.append(f"  Player 1 chose: {state.last_player1_choice}")
            view.append(f"  Player 2 chose: {state.last_player2_choice}")

        return "\n".join(view)


class RPSGame(Game):
    """Rock Paper Scissors game."""

    name = "Rock Paper Scissors"
    min_players = 2
    max_players = 2

    def setup(self, max_rounds: int = 3, **config):
        """Initialize the game."""
        self.state = RPSState(max_rounds=max_rounds)
        self.board = RPSBoard()
        self.history = GameHistory()
        self.history.start_new_round()
        self.players = [
            Player(name="Player 1", team="1"),
            Player(name="Player 2", team="2")
        ]
        self.actions = [ChooseAction()]

    def get_current_player(self):
        """Determine whose turn it is."""
        if self.state.player1_choice is None:
            return self.players[0]
        elif self.state.player2_choice is None:
            return self.players[1]
        return None  # Both chose, round will be resolved

    def next_turn(self) -> None:
        """Advance to next turn - handled automatically in RPS after both players choose."""
        pass  # Turn advancement is handled in action.apply()
