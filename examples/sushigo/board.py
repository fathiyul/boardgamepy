"""Sushi Go! board implementation."""

import random
from typing import TYPE_CHECKING
from boardgamepy import Board
from cards import Card, CardType, create_deck

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class SushiGoBoard(Board):
    """
    Sushi Go! game board managing card drafting and scoring.

    Tracks:
    - Deck of cards
    - Each player's current hand
    - Each player's played cards (collection area)
    - Each player's pudding count (for end-game scoring)
    """

    def __init__(self, num_players: int):
        """
        Initialize board for Sushi Go!

        Args:
            num_players: Number of players (2-5)
        """
        if num_players < 2 or num_players > 5:
            raise ValueError("Sushi Go! requires 2-5 players")

        self.num_players = num_players

        # Card management
        self.deck: list[Card] = []

        # Player hands (cards currently in hand for drafting)
        self.hands: dict[int, list[Card]] = {i: [] for i in range(num_players)}

        # Player collections (cards played this round)
        self.collections: dict[int, list[Card]] = {i: [] for i in range(num_players)}

        # Pudding tracking (persists across rounds)
        self.pudding_counts: dict[int, int] = {i: 0 for i in range(num_players)}

        # Cards per hand based on player count
        self.cards_per_hand = {
            2: 10,
            3: 9,
            4: 8,
            5: 7,
        }[num_players]

    def setup_round(self) -> None:
        """Setup a new round of Sushi Go!"""
        # Create and shuffle deck
        self.deck = create_deck()
        random.shuffle(self.deck)

        # Clear collections (but not pudding counts)
        self.collections = {i: [] for i in range(self.num_players)}

        # Deal hands
        for player_idx in range(self.num_players):
            self.hands[player_idx] = [
                self.deck.pop() for _ in range(self.cards_per_hand)
            ]

    def play_card(self, player_idx: int, card: Card) -> None:
        """Play a card from hand to collection."""
        if card not in self.hands[player_idx]:
            raise ValueError(f"Player {player_idx} doesn't have {card}")

        self.hands[player_idx].remove(card)
        self.collections[player_idx].append(card)

        # Track pudding
        if card.type == CardType.PUDDING:
            self.pudding_counts[player_idx] += 1

    def pass_hands(self) -> None:
        """Pass hands to the next player (card drafting mechanic)."""
        # Rotate hands clockwise
        temp_hands = {}
        for i in range(self.num_players):
            next_player = (i + 1) % self.num_players
            temp_hands[next_player] = self.hands[i]
        self.hands = temp_hands

    def is_round_over(self) -> bool:
        """Check if round is over (all hands empty)."""
        return all(len(hand) == 0 for hand in self.hands.values())

    def calculate_round_scores(self) -> dict[int, int]:
        """
        Calculate scores for the current round.

        Returns:
            dict mapping player_idx to round score
        """
        scores = {i: 0 for i in range(self.num_players)}

        for player_idx in range(self.num_players):
            cards = self.collections[player_idx]

            # Count cards by type
            maki_count = sum(c.type.maki_value for c in cards if c.is_maki)
            tempura_count = sum(1 for c in cards if c.type == CardType.TEMPURA)
            sashimi_count = sum(1 for c in cards if c.type == CardType.SASHIMI)
            dumpling_count = sum(1 for c in cards if c.type == CardType.DUMPLING)

            # Tempura: 2 = 5 points
            scores[player_idx] += (tempura_count // 2) * 5

            # Sashimi: 3 = 10 points
            scores[player_idx] += (sashimi_count // 3) * 10

            # Dumpling: 1,3,6,10,15
            dumpling_points = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}
            scores[player_idx] += dumpling_points.get(dumpling_count, 15)

            # Nigiri with wasabi
            wasabi_cards = [c for c in cards if c.type == CardType.WASABI]
            nigiri_cards = [c for c in cards if c.is_nigiri]

            # Match nigiri with wasabi (first nigiri after wasabi gets tripled)
            wasabi_used = 0
            for card in cards:
                if card.is_nigiri:
                    points = card.type.points
                    if wasabi_used < len(wasabi_cards):
                        points *= 3
                        wasabi_used += 1
                    scores[player_idx] += points

        # Maki scoring (most and second most)
        maki_totals = {
            i: sum(c.type.maki_value for c in self.collections[i] if c.is_maki)
            for i in range(self.num_players)
        }

        if any(total > 0 for total in maki_totals.values()):
            sorted_players = sorted(maki_totals.items(), key=lambda x: x[1], reverse=True)

            # Most maki gets 6 points
            if sorted_players[0][1] > 0:
                most_maki = sorted_players[0][1]
                winners = [p for p, count in sorted_players if count == most_maki]
                points_each = 6 // len(winners)
                for p in winners:
                    scores[p] += points_each

            # Second most gets 3 points (if different from most)
            if len(sorted_players) > 1 and sorted_players[1][1] > 0:
                if sorted_players[1][1] < sorted_players[0][1]:
                    second_maki = sorted_players[1][1]
                    winners = [p for p, count in sorted_players if count == second_maki]
                    points_each = 3 // len(winners)
                    for p in winners:
                        scores[p] += points_each

        return scores

    def calculate_pudding_scores(self) -> dict[int, int]:
        """
        Calculate pudding scores at end of game.

        Returns:
            dict mapping player_idx to pudding score
        """
        scores = {i: 0 for i in range(self.num_players)}

        if self.num_players == 2:
            # In 2-player, only most gets points
            max_pudding = max(self.pudding_counts.values())
            if max_pudding > 0:
                winners = [p for p, count in self.pudding_counts.items() if count == max_pudding]
                for p in winners:
                    scores[p] = 6 // len(winners)
        else:
            # Most pudding gets +6
            max_pudding = max(self.pudding_counts.values())
            if max_pudding > 0:
                winners = [p for p, count in self.pudding_counts.items() if count == max_pudding]
                for p in winners:
                    scores[p] = 6 // len(winners)

            # Least pudding gets -6
            min_pudding = min(self.pudding_counts.values())
            losers = [p for p, count in self.pudding_counts.items() if count == min_pudding]
            for p in losers:
                scores[p] -= 6 // len(losers)

        return scores

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view with information hiding.

        Players see:
        - Their own hand
        - Their own collection
        - Other players' collections (visible)
        - Other players' hand sizes
        """
        from boardgamepy.core.player import Player

        player: Player = context.player
        player_idx = player.player_idx

        lines = ["=== SUSHI GO! ===", ""]

        # Your hand
        hand_str = ", ".join(str(card) for card in self.hands[player_idx])
        lines.append(f"Your Hand ({len(self.hands[player_idx])} cards): {hand_str}")
        lines.append("")

        # Your collection
        collection_str = ", ".join(str(card) for card in self.collections[player_idx]) or "(none)"
        lines.append(f"Your Collection: {collection_str}")
        lines.append("")

        # Other players
        lines.append("Other Players:")
        for i in range(self.num_players):
            if i == player_idx:
                continue

            hand_size = len(self.hands[i])
            collection = self.collections[i]
            collection_str = ", ".join(str(card) for card in collection) or "(none)"
            pudding = self.pudding_counts[i]

            lines.append(f"  Player {i + 1}:")
            lines.append(f"    Hand: {hand_size} cards")
            lines.append(f"    Collection: {collection_str}")
            lines.append(f"    Pudding: {pudding}")

        lines.append("")
        lines.append(f"Your Pudding Count: {self.pudding_counts[player_idx]}")

        return "\n".join(lines)
