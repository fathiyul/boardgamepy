"""Love Letter board implementation."""

import random
from typing import TYPE_CHECKING
from boardgamepy import Board
from cards import Card, CardType, create_deck

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class LoveLetterBoard(Board):
    """
    Love Letter game board managing cards, hands, and game state.

    Tracks:
    - Deck of cards
    - Each player's hand (1 card normally, 2 when deciding which to play)
    - Discarded cards
    - Eliminated players
    - Protected players (Handmaid effect)
    """

    def __init__(self, num_players: int):
        """
        Initialize board for Love Letter.

        Args:
            num_players: Number of players (2-4)
        """
        if num_players < 2 or num_players > 4:
            raise ValueError("Love Letter requires 2-4 players")

        self.num_players = num_players

        # Card management
        self.deck: list[Card] = []
        self.discarded: list[Card] = []
        self.removed_card: Card | None = None  # Card removed at start

        # Player hands (player index -> list of cards)
        self.hands: dict[int, list[Card]] = {i: [] for i in range(num_players)}

        # Player states
        self.eliminated: set[int] = set()  # Player indices who are out
        self.protected: set[int] = set()  # Players protected by Handmaid

        # Knowledge tracking (for AI)
        # player_index -> {other_player_index: known_card_type or None}
        self.known_cards: dict[int, dict[int, CardType | None]] = {
            i: {j: None for j in range(num_players) if j != i}
            for i in range(num_players)
        }

    def setup_round(self) -> None:
        """Setup a new round of Love Letter."""
        # Create and shuffle deck
        self.deck = create_deck()
        random.shuffle(self.deck)

        # Remove one card face-down
        self.removed_card = self.deck.pop()

        # Clear states
        self.discarded = []
        self.eliminated = set()
        self.protected = set()
        self.hands = {i: [] for i in range(self.num_players)}
        self.known_cards = {
            i: {j: None for j in range(self.num_players) if j != i}
            for i in range(self.num_players)
        }

        # Deal one card to each player
        for player_idx in range(self.num_players):
            self.hands[player_idx] = [self.deck.pop()]

    def draw_card(self, player_idx: int) -> Card:
        """Draw a card for a player."""
        if not self.deck:
            raise ValueError("Deck is empty")
        card = self.deck.pop()
        self.hands[player_idx].append(card)
        return card

    def discard_card(self, player_idx: int, card: Card) -> None:
        """Discard a card from player's hand."""
        if card not in self.hands[player_idx]:
            raise ValueError(f"Player {player_idx} doesn't have {card}")
        self.hands[player_idx].remove(card)
        self.discarded.append(card)

    def eliminate_player(self, player_idx: int) -> None:
        """Eliminate a player from the round."""
        self.eliminated.add(player_idx)
        # Discard their hand
        for card in self.hands[player_idx][:]:
            self.discard_card(player_idx, card)

    def get_active_players(self) -> list[int]:
        """Get list of non-eliminated player indices."""
        return [i for i in range(self.num_players) if i not in self.eliminated]

    def get_targetable_players(self, current_player: int) -> list[int]:
        """Get list of players that can be targeted (not protected, not eliminated, not self)."""
        return [
            i
            for i in range(self.num_players)
            if i != current_player and i not in self.eliminated and i not in self.protected
        ]

    def is_round_over(self) -> bool:
        """Check if round is over (1 player left or deck empty)."""
        active = self.get_active_players()
        return len(active) <= 1 or len(self.deck) == 0

    def get_round_winner(self) -> int | None:
        """Get the winner of the round (highest card value among active players)."""
        active = self.get_active_players()
        if not active:
            return None

        # Get highest card value
        winner = max(active, key=lambda p: self.hands[p][0].value if self.hands[p] else 0)
        return winner

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view with role-based information hiding.

        Players see:
        - Their own hand
        - All discarded cards
        - Who is eliminated
        - Who is protected
        - Deck size
        But NOT other players' hands (unless revealed by card effects)
        """
        from boardgamepy.core.player import Player

        player: Player = context.player

        # Determine player index
        player_idx = int(player.team.split()[-1]) - 1  # "Player 1" -> 0

        lines = ["=== LOVE LETTER ===", ""]

        # Your hand
        if player_idx in self.eliminated:
            lines.append(f"You are ELIMINATED")
        else:
            hand_str = ", ".join(str(card) for card in self.hands[player_idx])
            lines.append(f"Your Hand: {hand_str}")

        lines.append("")

        # Other players status
        lines.append("Players:")
        for i in range(self.num_players):
            if i == player_idx:
                continue

            status_parts = [f"Player {i + 1}"]

            if i in self.eliminated:
                status_parts.append("ELIMINATED")
            else:
                if i in self.protected:
                    status_parts.append("PROTECTED")

                # Show known cards
                if self.known_cards[player_idx][i]:
                    known = self.known_cards[player_idx][i]
                    status_parts.append(f"(you know: {known.card_name})")

            lines.append("  " + " - ".join(status_parts))

        lines.append("")

        # Discarded cards
        if self.discarded:
            discard_str = ", ".join(str(card) for card in self.discarded)
            lines.append(f"Discarded: {discard_str}")
        else:
            lines.append("Discarded: (none)")

        lines.append("")
        lines.append(f"Cards in deck: {len(self.deck)}")

        return "\n".join(lines)
