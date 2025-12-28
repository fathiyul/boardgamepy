"""Sushi Go! game actions."""

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

from boardgamepy import Action
from cards import Card, CardType

if TYPE_CHECKING:
    from game import SushiGoGame
    from boardgamepy.core.player import Player


class PlayCardOutput(BaseModel):
    """LLM structured output for playing a card."""

    card_to_play: str = Field(
        ..., description="Which card from your hand to play (exact card name)"
    )
    second_card: str | None = Field(
        None,
        description="Optional second card to play when using Chopsticks (puts Chopsticks back in hand)"
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
        second_card: str | None = None,
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

        if card_obj is None:
            return False

        # If using chopsticks (second card provided)
        if second_card:
            # Must have chopsticks in collection
            collection = game.board.collections[player_idx]
            has_chopsticks = any(c.type == CardType.CHOPSTICKS for c in collection)
            if not has_chopsticks:
                return False

            # Must have second card in hand (different from first)
            second_obj = self._find_card_by_name(hand, second_card)
            if second_obj is None:
                return False
            # Cards must be different instances (can't play same card twice)
            if second_obj.id == card_obj.id:
                return False

        return True

    def apply(
        self,
        game: "SushiGoGame",
        player: "Player",
        card_to_play: str,
        second_card: str | None = None,
        **kwargs,
    ) -> None:
        """Apply card play."""
        player_idx = int(player.team.split()[-1]) - 1
        hand = game.board.hands[player_idx]

        # Find and play the first card
        card_obj = self._find_card_by_name(hand, card_to_play)

        if card_obj:
            game.board.play_card(player_idx, card_obj)

            # Handle chopsticks - play second card
            if second_card:
                second_obj = self._find_card_by_name(game.board.hands[player_idx], second_card)
                if second_obj:
                    game.board.play_card(player_idx, second_obj)

                    # Return chopsticks from collection to hand
                    collection = game.board.collections[player_idx]
                    for i, c in enumerate(collection):
                        if c.type == CardType.CHOPSTICKS:
                            chopsticks = collection.pop(i)
                            game.board.hands[player_idx].append(chopsticks)
                            break

            # Log action
            game.history.add_action(
                self,
                player,
                card_name=card_to_play,
                second_card=second_card,
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
