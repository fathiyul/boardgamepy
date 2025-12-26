"""Sushi Go! game actions."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

from boardgamepy import Action
from cards import Card

if TYPE_CHECKING:
    from game import SushiGoGame
    from boardgamepy.core.player import Player


class PlayCardOutput(BaseModel):
    """LLM structured output for playing a card."""

    card_to_play: str = Field(
        ..., description="Which card from your hand to play (exact card name)"
    )
    reasoning: str | None = Field(None, description="Why you chose this card")


class PlayCardAction(Action["SushiGoGame"]):
    """Action for playing a card from hand."""

    name = "play_card"
    display_name = "Play Card"
    OutputSchema = PlayCardOutput

    def validate(
        self,
        game: "SushiGoGame",
        player: "Player",
        card_to_play: str,
        **kwargs,
    ) -> bool:
        """Validate card play."""
        player_idx = int(player.team.split()[-1]) - 1

        # Check if player has cards in hand
        if not game.board.hands[player_idx]:
            return False

        # Check if card is in hand
        hand = game.board.hands[player_idx]
        card_obj = self._find_card_by_name(hand, card_to_play)

        return card_obj is not None

    def apply(
        self,
        game: "SushiGoGame",
        player: "Player",
        card_to_play: str,
        **kwargs,
    ) -> None:
        """Apply card play."""
        player_idx = int(player.team.split()[-1]) - 1

        # Find and play the card
        hand = game.board.hands[player_idx]
        card_obj = self._find_card_by_name(hand, card_to_play)

        if card_obj:
            game.board.play_card(player_idx, card_obj)

            # Log action
            game.history.add_action(
                self,
                player,
                card_name=card_to_play,
                player_name=player.team,
            )

            # Remove player from waiting list
            if player_idx in game.state.waiting_for_players:
                game.state.waiting_for_players.remove(player_idx)

        # Check if all players have played
        if len(game.state.waiting_for_players) == 0:
            # Pass hands for next turn
            if not game.board.is_round_over():
                game.board.pass_hands()
                # Reset waiting list
                game.state.waiting_for_players = set(range(game.board.num_players))

    @staticmethod
    def _find_card_by_name(hand: list[Card], name: str) -> Card | None:
        """Find a card in hand by its display name."""
        for card in hand:
            if card.name.lower() == name.lower() or str(card).lower() == name.lower():
                return card
        return None

    def to_history_record(
        self, player: "Player", card_name: str, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        return {
            "type": "play_card",
            "player": player_name,
            "card": card_name,
        }
