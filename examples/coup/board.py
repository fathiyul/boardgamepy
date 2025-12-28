"""Coup board implementation."""

import random
from typing import TYPE_CHECKING
from boardgamepy import Board
from characters import Character, CharacterType, create_deck

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class CoupBoard(Board):
    """
    Coup game board managing characters, coins, and influence.

    Tracks:
    - Deck of character cards
    - Each player's influence (2 cards, some revealed)
    - Each player's coins
    - Revealed (lost) influence
    """

    def __init__(self, num_players: int):
        """
        Initialize board for Coup.

        Args:
            num_players: Number of players (2-6)
        """
        if num_players < 2 or num_players > 6:
            raise ValueError("Coup requires 2-6 players")

        self.num_players = num_players

        # Card management
        self.deck: list[Character] = []

        # Player influence (player index -> list of characters)
        self.influence: dict[int, list[Character]] = {i: [] for i in range(num_players)}

        # Player coins
        self.coins: dict[int, int] = {i: 2 for i in range(num_players)}

        # Court deck (for Ambassador exchanges)
        self.court_deck: list[Character] = []

    def setup_game(self) -> None:
        """Setup a new game of Coup."""
        # Create and shuffle deck
        self.deck = create_deck()
        random.shuffle(self.deck)

        # Deal 2 cards to each player
        for player_idx in range(self.num_players):
            self.influence[player_idx] = [self.deck.pop(), self.deck.pop()]

        # Remaining cards become court deck
        self.court_deck = self.deck
        self.deck = []

        # Give each player 2 coins
        self.coins = {i: 2 for i in range(self.num_players)}

    def get_active_players(self) -> list[int]:
        """Get list of players with at least one influence."""
        return [i for i in range(self.num_players) if self.has_influence(i)]

    def has_influence(self, player_idx: int) -> bool:
        """Check if player has any unrevealed influence."""
        return any(not card.revealed for card in self.influence[player_idx])

    def get_influence_count(self, player_idx: int) -> int:
        """Get number of unrevealed influence cards."""
        return sum(1 for card in self.influence[player_idx] if not card.revealed)

    def reveal_influence(self, player_idx: int, character_type: CharacterType) -> bool:
        """
        Reveal (lose) an influence card of specified type.

        Returns True if successful, False if player doesn't have that card.
        """
        for card in self.influence[player_idx]:
            if not card.revealed and card.type == character_type:
                card.revealed = True
                return True
        return False

    def reveal_random_influence(self, player_idx: int) -> Character | None:
        """Reveal a random unrevealed influence card."""
        unrevealed = [card for card in self.influence[player_idx] if not card.revealed]
        if unrevealed:
            card = random.choice(unrevealed)
            card.revealed = True
            return card
        return None

    def has_character(self, player_idx: int, character_type: CharacterType) -> bool:
        """Check if player has an unrevealed card of this type."""
        return any(
            card.type == character_type and not card.revealed
            for card in self.influence[player_idx]
        )

    def add_coins(self, player_idx: int, amount: int) -> None:
        """Add coins to player."""
        self.coins[player_idx] = max(0, self.coins[player_idx] + amount)

    def remove_coins(self, player_idx: int, amount: int) -> bool:
        """Remove coins from player. Returns False if not enough coins."""
        if self.coins[player_idx] < amount:
            return False
        self.coins[player_idx] -= amount
        return True

    def transfer_coins(self, from_player: int, to_player: int, amount: int) -> bool:
        """Transfer coins between players. Returns False if not enough coins."""
        if self.coins[from_player] < amount:
            return False
        self.coins[from_player] -= amount
        self.coins[to_player] += amount
        return True

    def exchange_with_court(self, player_idx: int) -> list[Character]:
        """
        Ambassador ability: draw 2 cards from court deck.
        Returns the cards drawn (player temporarily has 4 cards).
        """
        if len(self.court_deck) < 2:
            return []

        drawn = [self.court_deck.pop(), self.court_deck.pop()]
        return drawn

    def return_to_court(self, cards: list[Character]) -> None:
        """Return cards to court deck and shuffle."""
        self.court_deck.extend(cards)
        random.shuffle(self.court_deck)

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view with role-based information hiding.

        Players see:
        - Their own influence (unrevealed cards)
        - All players' coin counts
        - All revealed influence
        But NOT other players' unrevealed cards
        """
        from boardgamepy.core.player import Player

        player: Player = context.player

        # Determine player index
        player_idx = player.player_idx

        lines = ["=== COUP ===", ""]

        # Your influence
        your_cards = self.influence[player_idx]
        unrevealed = [card for card in your_cards if not card.revealed]
        revealed = [card for card in your_cards if card.revealed]

        lines.append(f"Your Influence ({self.get_influence_count(player_idx)} remaining):")
        if unrevealed:
            lines.append(f"  Hidden: {', '.join(str(c) for c in unrevealed)}")
        if revealed:
            lines.append(f"  Revealed: {', '.join(str(c) for c in revealed)}")

        lines.append(f"Your Coins: {self.coins[player_idx]}")
        lines.append("")

        # Other players
        lines.append("Other Players:")
        for i in range(self.num_players):
            if i == player_idx:
                continue

            influence_count = self.get_influence_count(i)
            revealed_cards = [card for card in self.influence[i] if card.revealed]

            status = f"Player {i + 1}: {influence_count} influence, {self.coins[i]} coins"
            if revealed_cards:
                status += f" (revealed: {', '.join(str(c) for c in revealed_cards)})"

            lines.append(f"  {status}")

        return "\n".join(lines)
