"""Codenames game implementation using boardgamepy."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from .board import CodenamesBoard
from .state import CodenamesState, Team
from .actions import ClueAction, GuessAction, PassAction

if TYPE_CHECKING:
    pass


class CodenamesGame(Game):
    """
    Codenames board game implementation.

    A team-based word association game where Spymasters give one-word
    clues to help their Operatives identify their team's agents on a
    5x5 board of codenames.
    """

    # Declarative metadata
    name = "Codenames"
    min_players = 4
    max_players = 4

    # Type hints for components
    board: CodenamesBoard
    state: CodenamesState

    # Register actions
    actions = [ClueAction, GuessAction, PassAction]

    def setup(self, codenames: list[str], **config) -> None:
        """
        Initialize Codenames game.

        Args:
            codenames: Pool of codenames to use for the board
            **config: Additional configuration (unused)
        """
        # Create board
        self.board = CodenamesBoard.create_random(codenames)

        # Initialize state
        self.state = CodenamesState(current_team="Red")

        # Initialize history
        self.history = GameHistory()
        self.history.start_new_round()

        # Create players (4 players: 2 per team, 2 roles)
        # By default, all AI players - can be configured later
        self.players = [
            Player(name="Red Spymaster", team="Red", role="Spymaster", agent_type="ai", player_idx=0),
            Player(name="Red Operatives", team="Red", role="Operatives", agent_type="ai", player_idx=1),
            Player(name="Blue Spymaster", team="Blue", role="Spymaster", agent_type="ai", player_idx=2),
            Player(name="Blue Operatives", team="Blue", role="Operatives", agent_type="ai", player_idx=3),
        ]

    def get_current_player(self) -> Player:
        """
        Get the player whose turn it is.

        In Codenames:
        - If guesses_remaining > 0, it's Operatives' turn
        - Otherwise, it's Spymaster's turn
        """
        team = self.state.current_team
        role = "Operatives" if self.state.guesses_remaining > 0 else "Spymaster"

        player = self.get_player(team=team, role=role)
        if player is None:
            raise RuntimeError(f"No player found for team={team}, role={role}")
        return player

    def next_turn(self) -> None:
        """
        Advance to next turn.

        Not typically called directly - actions handle turn advancement.
        """
        self._end_team_turn()

    def _end_team_turn(self) -> None:
        """
        End current team's turn and switch to other team.

        When Blue finishes, start a new round and go back to Red.
        """
        if self.state.current_team == "Red":
            # Pass turn to Blue, same round
            self.state.current_team = "Blue"
            self.state.guesses_remaining = 0
        else:
            # Blue just finished: new round, back to Red
            self.state.current_team = "Red"
            self.state.guesses_remaining = 0
            self.history.start_new_round()
