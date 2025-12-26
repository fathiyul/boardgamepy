"""Tic-Tac-Toe game implementation using boardgamepy."""

from boardgamepy import Game, GameHistory, Player
from board import TicTacToeBoard
from state import TicTacToeState
from actions import MoveAction


class TicTacToeGame(Game):
    """
    Tic-Tac-Toe game implementation.

    Classic 3x3 board game where players alternate placing X and O,
    trying to get 3 in a row.
    """

    # Declarative metadata
    name = "Tic-Tac-Toe"
    min_players = 2
    max_players = 2

    # Type hints
    board: TicTacToeBoard
    state: TicTacToeState

    # Register actions
    actions = [MoveAction]

    def setup(self, **config) -> None:
        """Initialize Tic-Tac-Toe game."""
        # Create board
        self.board = TicTacToeBoard()

        # Initialize state
        self.state = TicTacToeState(current_player="X")

        # Initialize history
        self.history = GameHistory()
        self.history.start_new_round()

        # Create players (X and O)
        self.players = [
            Player(name="X", team="X", agent_type="ai"),
            Player(name="O", team="O", agent_type="ai"),
        ]

    def get_current_player(self) -> Player:
        """Get the player whose turn it is."""
        mark = self.state.current_player
        player = self.get_player(team=mark)
        if player is None:
            raise RuntimeError(f"No player found for {mark}")
        return player

    def next_turn(self) -> None:
        """
        Advance to next turn.

        In Tic-Tac-Toe, turns are handled by the MoveAction,
        so this is mostly a no-op.
        """
        pass
