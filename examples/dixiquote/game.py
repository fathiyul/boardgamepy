"""DixiQuote game implementation using boardgamepy."""

import random
from typing import TYPE_CHECKING

from boardgamepy import Game, GameHistory, Player
from state import DixiQuoteState
from actions import ChooseSituationAction, GiveQuoteAction, SubmitSituationAction, VoteAction

if TYPE_CHECKING:
    pass


class DixiQuoteGame(Game):
    """
    DixiQuote board game implementation.

    A storytelling game where players use situation cards and poetic quotes
    to create interpretable but not obvious connections.
    """

    # Declarative metadata
    name = "DixiQuote"
    min_players = 3
    max_players = 8

    # Type hints for components
    state: DixiQuoteState

    # Register actions
    actions = [ChooseSituationAction, GiveQuoteAction, SubmitSituationAction, VoteAction]

    def setup(self, situations: list[str], **config) -> None:
        """
        Initialize DixiQuote game.

        Args:
            situations: Pool of situation cards to use
            **config: Additional configuration including:
                - num_players: Number of players (3-8, default 4)
                - target_score: Score to win (default 20)
                - max_rounds: Maximum rounds (default 15)
                - target: Alias for target_score (for CLI compatibility)
        """
        num_players = config.get("num_players", 4)
        target_score = config.get("target", config.get("target_score", 20))
        max_rounds = config.get("max_rounds", 15)

        # Initialize deck
        self.deck = situations.copy()
        random.shuffle(self.deck)

        # Initialize player hands
        self.hands: dict[int, list[str]] = {}

        # Initialize state
        self.state = DixiQuoteState()
        self.state.target_score = target_score
        self.state.max_rounds = max_rounds

        # Initialize history
        self.history = GameHistory()
        self.history.start_new_round()

        # Create players
        self.players = [
            Player(name=f"Player {i + 1}", agent_type="ai", player_idx=i)
            for i in range(num_players)
        ]

        # Deal 6 cards to each player
        for i in range(num_players):
            self.hands[i] = []
            for _ in range(6):
                if self.deck:
                    self.hands[i].append(self.deck.pop())

        # Initialize scores
        for i in range(num_players):
            self.state.scores[i] = 0

    def get_player_hand(self, player_idx: int) -> list[str]:
        """Get a player's hand of situation cards."""
        return self.hands.get(player_idx, [])

    def remove_from_hand(self, player_idx: int, situation: str) -> None:
        """Remove a situation card from a player's hand."""
        if player_idx in self.hands and situation in self.hands[player_idx]:
            self.hands[player_idx].remove(situation)

    def draw_card(self, player_idx: int) -> None:
        """Draw a card from the deck to a player's hand."""
        if self.deck and player_idx in self.hands:
            self.hands[player_idx].append(self.deck.pop())

    def get_current_player(self) -> Player | None:
        """
        Get the player whose turn it is based on current phase.

        Returns None during scoring/transition phases.
        """
        if self.state.phase == "choose_situation" or self.state.phase == "give_quote":
            # Storyteller's turn
            return self.players[self.state.storyteller_idx]
        elif self.state.phase == "submit_situations":
            # Find next player who hasn't submitted and wasn't skipped
            for player in self.players:
                if (
                    player.player_idx != self.state.storyteller_idx
                    and player.player_idx not in self.state.submitted_situations
                    and player.player_idx not in self.state.skipped_players
                ):
                    return player
            return None
        elif self.state.phase == "vote":
            # Find next player who hasn't voted and wasn't skipped
            for player in self.players:
                if (
                    player.player_idx != self.state.storyteller_idx
                    and player.player_idx not in self.state.votes
                    and player.player_idx not in self.state.skipped_players
                ):
                    return player
            return None
        else:
            # Scoring or round_end phase
            return None

    def calculate_scores(self) -> dict[str, int]:
        """
        Calculate and apply scores for the current round.

        Returns:
            Dictionary mapping situation to points earned.
        """
        # Count votes for each situation
        vote_counts: dict[str, int] = {}
        situation_to_player: dict[str, int] = {}

        # Map situations to players
        for player_idx, situation in self.state.submitted_situations.items():
            situation_to_player[situation] = player_idx
            vote_counts[situation] = 0

        # Add storyteller's situation
        if self.state.storyteller_situation:
            situation_to_player[self.state.storyteller_situation] = self.state.storyteller_idx
            vote_counts[self.state.storyteller_situation] = 0

        # Count votes
        for situation in self.state.votes.values():
            if situation in vote_counts:
                vote_counts[situation] += 1

        # Calculate points for each situation
        situation_scores: dict[str, int] = {}
        num_voters = len(self.players) - 1  # All except storyteller

        for situation, votes in vote_counts.items():
            if votes == 0:
                points = 0  # No votes
            elif votes == num_voters:
                points = -1  # All votes (too obvious - penalty)
            else:
                points = 1  # Some but not all votes

            situation_scores[situation] = points

            # Award points to the player who submitted this situation
            player_idx = situation_to_player[situation]
            current_score = self.state.scores.get(player_idx, 0)
            self.state.scores[player_idx] = max(0, current_score + points)

        # Calculate storyteller bonus
        # Storyteller gets 1 point if at least 2 different cards get votes, including their own
        # UNLESS all other players were skipped (then give storyteller the bonus anyway)
        num_non_storyteller_players = len(self.players) - 1
        num_skipped_non_storyteller = sum(
            1 for idx in self.state.skipped_players if idx != self.state.storyteller_idx
        )

        # If all other players were skipped, give storyteller the bonus automatically
        if num_skipped_non_storyteller >= num_non_storyteller_players:
            self.state.scores[self.state.storyteller_idx] += 1
        else:
            # Normal scoring: at least 2 different cards get votes and storyteller's card is one of them
            cards_with_votes = sum(1 for v in vote_counts.values() if v > 0)
            storyteller_votes = vote_counts.get(self.state.storyteller_situation, 0)

            if cards_with_votes >= 2 and storyteller_votes > 0:
                self.state.scores[self.state.storyteller_idx] += 1

        # Award bonus points to players who correctly guessed the storyteller's card
        if self.state.storyteller_situation:
            for voter_idx, voted_situation in self.state.votes.items():
                if voted_situation == self.state.storyteller_situation:
                    self.state.scores[voter_idx] = self.state.scores.get(voter_idx, 0) + 1

        return situation_scores

    def start_new_round(self) -> None:
        """Start a new round."""
        # Remove played cards from hands
        if self.state.storyteller_situation and self.state.storyteller_idx in self.hands:
            self.remove_from_hand(self.state.storyteller_idx, self.state.storyteller_situation)

        for player_idx, situation in self.state.submitted_situations.items():
            self.remove_from_hand(player_idx, situation)

        # Draw new cards (if deck has cards)
        for player_idx in range(len(self.players)):
            if len(self.get_player_hand(player_idx)) < 6:
                self.draw_card(player_idx)

        # Advance storyteller
        self.state.storyteller_idx = (self.state.storyteller_idx + 1) % len(self.players)

        # Increment round number
        self.state.round_number += 1

        # Reset round state
        self.state.reset_round()

        # Check end conditions (target score, max rounds, or deck empty)
        if self.state.check_win_conditions() or not self.deck:
            self.state.is_over = True
            # Find winner (highest score)
            if self.state.scores:
                max_score = max(self.state.scores.values())
                for player_idx, score in self.state.scores.items():
                    if score == max_score:
                        self.state.winner_idx = player_idx
                        break

        # Start new round in history
        if not self.state.is_over:
            self.history.start_new_round()

    def next_turn(self) -> None:
        """
        Advance to next turn.

        Not typically called directly - actions handle phase advancement.
        """
        pass
