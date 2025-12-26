"""Love Letter game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import LoveLetterBoard
from state import LoveLetterState
from actions import PlayCardAction

if TYPE_CHECKING:
    pass


class LoveLetterGame(Game):
    """Love Letter card game."""

    name = "Love Letter"
    min_players = 2
    max_players = 4

    def __init__(self):
        """Initialize game."""
        self.board: LoveLetterBoard
        self.state: LoveLetterState
        self.history: GameHistory
        self.players: list[Player]
        self.num_players: int = 0

    def setup(self, num_players: int = 2, target_tokens: int | None = None) -> None:
        """
        Setup Love Letter game.

        Args:
            num_players: Number of players (2-4)
            target_tokens: Number of tokens to win (optional, uses defaults if not specified)
        """
        if num_players < 2 or num_players > 4:
            raise ValueError("Love Letter requires 2-4 players")

        self.num_players = num_players
        self.board = LoveLetterBoard(num_players)
        self.state = LoveLetterState()

        # Set target tokens - use provided value or defaults based on player count
        # 2 players: 7 tokens, 3 players: 5 tokens, 4 players: 4 tokens
        if target_tokens is not None:
            self.state.target_tokens = target_tokens
        elif num_players == 2:
            self.state.target_tokens = 7
        elif num_players == 3:
            self.state.target_tokens = 5
        else:
            self.state.target_tokens = 4

        # Initialize scores
        self.state.scores = {i: 0 for i in range(num_players)}

        self.history = GameHistory()

        # Create players
        self.players = [
            Player(team=f"Player {i + 1}", role="player", agent=None)
            for i in range(num_players)
        ]

        # Register actions
        self.actions = [PlayCardAction()]

        # Setup first round
        self.board.setup_round()

    def get_current_player(self) -> Player:
        """Get current player."""
        return self.players[self.state.current_player_idx]

    def next_turn(self) -> None:
        """Advance to next turn (handled by action.apply)."""
        pass

    def start_new_round(self) -> None:
        """Start a new round after previous round ended."""
        self.state.round_number += 1
        self.state.round_over = False
        self.state.round_winner = None
        self.history = GameHistory()  # Clear round history
        self.board.setup_round()

        # Start with player who didn't go first last time
        self.state.current_player_idx = (self.state.current_player_idx + 1) % self.num_players

    def draw_card_for_turn(self) -> None:
        """Draw a card at the start of the turn (before playing)."""
        if not self.board.deck:
            return
        self.board.draw_card(self.state.current_player_idx)
