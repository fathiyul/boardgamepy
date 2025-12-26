"""Splendor game implementation."""

from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from board import SplendorBoard
from state import SplendorState
from actions import TakeGemsAction, PurchaseCardAction, ReserveCardAction

if TYPE_CHECKING:
    pass


class SplendorGame(Game):
    """Splendor card development game."""

    name = "Splendor"
    min_players = 2
    max_players = 4

    def __init__(self):
        """Initialize game."""
        self.board: SplendorBoard
        self.state: SplendorState
        self.history: GameHistory
        self.players: list[Player]
        self.num_players: int = 0

    def setup(self, num_players: int = 3) -> None:
        """
        Setup Splendor game.

        Args:
            num_players: Number of players (2-4, default 3)
        """
        if num_players < 2 or num_players > 4:
            raise ValueError("Splendor requires 2-4 players")

        self.num_players = num_players
        self.board = SplendorBoard(num_players)
        self.state = SplendorState()
        self.history = GameHistory()

        # Initialize nobles tracking
        self.state.player_nobles = {i: [] for i in range(num_players)}

        # Create players
        self.players = [
            Player(team=f"Player {i + 1}", role="player", agent=None)
            for i in range(num_players)
        ]

        # Register actions
        self.actions = [TakeGemsAction(), PurchaseCardAction(), ReserveCardAction()]

        # Setup board
        self.board.setup_game()

    def get_current_player(self) -> Player:
        """Get current player."""
        return self.players[self.state.current_player_idx]

    def check_nobles(self, player_idx: int) -> None:
        """Check if player qualifies for any nobles."""
        qualifying_nobles = self.board.check_nobles(player_idx)

        if qualifying_nobles:
            # Player gets one noble (if multiple, game will handle choice)
            # For AI, we'll just give them the first one
            noble = qualifying_nobles[0]
            self.board.claim_noble(player_idx, noble)
            self.state.player_nobles[player_idx].append(noble)

    def check_gem_limit(self, player_idx: int) -> dict:
        """
        Check if player exceeds 10 gem limit.

        Returns dict of gems to return (empty if under limit).
        """
        total = self.board.get_total_gems(player_idx)
        if total <= 10:
            return {}

        # Player must return gems
        # For AI, we'll implement a simple strategy: return least useful gems
        # (This should be handled in UI for human players)
        to_return = {}
        gems_needed = total - 10

        player_gems = self.board.player_gems[player_idx]

        # Return gems we have most of
        from cards import GemType

        regular_gems = [
            GemType.DIAMOND,
            GemType.SAPPHIRE,
            GemType.EMERALD,
            GemType.RUBY,
            GemType.ONYX,
        ]

        # Sort by count (descending)
        sorted_gems = sorted(regular_gems, key=lambda g: player_gems[g], reverse=True)

        for gem in sorted_gems:
            if gems_needed <= 0:
                break
            count = player_gems[gem]
            if count > 0:
                to_return[gem] = min(count, gems_needed)
                gems_needed -= to_return[gem]

        return to_return

    def check_game_end(self) -> None:
        """Check if game should end."""
        # Check if any player reached 15 points
        for i in range(self.num_players):
            points = self.board.get_player_points(i)
            noble_points = len(self.state.player_nobles.get(i, [])) * 3
            total = points + noble_points

            if total >= 15 and not self.state.final_round_triggered:
                self.state.final_round_triggered = True
                self.state.turns_in_final_round = 0

        # If final round triggered, count turns
        if self.state.final_round_triggered:
            self.state.turns_in_final_round += 1

            # Everyone has had final turn
            if self.state.turns_in_final_round >= self.num_players:
                # Determine winner
                max_points = -1
                winner_idx = None
                min_cards = float("inf")

                for i in range(self.num_players):
                    points = self.board.get_player_points(i)
                    noble_points = len(self.state.player_nobles.get(i, [])) * 3
                    total = points + noble_points
                    card_count = len(self.board.player_cards[i])

                    if total > max_points:
                        max_points = total
                        winner_idx = i
                        min_cards = card_count
                    elif total == max_points and card_count < min_cards:
                        winner_idx = i
                        min_cards = card_count

                self.state.is_over = True
                self.state.winner = winner_idx

    def next_turn(self) -> None:
        """Advance to next turn."""
        self.state.current_player_idx = (self.state.current_player_idx + 1) % self.num_players
        self.state.round_number += 1
