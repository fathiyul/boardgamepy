"""Love Letter game actions."""

from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field

from boardgamepy import Action
from cards import CardType, Card

if TYPE_CHECKING:
    from game import LoveLetterGame
    from boardgamepy.core.player import Player


class PlayCardOutput(BaseModel):
    """LLM structured output for playing a card."""

    card_to_play: Literal["Guard", "Priest", "Baron", "Handmaid", "Prince", "King", "Countess", "Princess"] = Field(
        ..., description="Which card from your hand to play"
    )
    target_player: int | None = Field(
        None, description="Target player number (1-4), or null if card has no target"
    )
    guess_card: Literal["Priest", "Baron", "Handmaid", "Prince", "King", "Countess", "Princess"] | None = Field(
        None, description="For Guard: which card type to guess (cannot guess Guard)"
    )
    reasoning: str | None = Field(None, description="Explanation of your play")


class PlayCardAction(Action["LoveLetterGame"]):
    """Action for playing a card from hand."""

    name = "play_card"
    display_name = "Play Card"
    OutputSchema = PlayCardOutput

    def validate(
        self,
        game: "LoveLetterGame",
        player: "Player",
        card_to_play: str,
        target_player: int | None = None,
        guess_card: str | None = None,
    ) -> bool:
        """Validate card play."""
        player_idx = game.state.current_player_idx

        # Check if player is eliminated
        if player_idx in game.board.eliminated:
            return False

        # Check if player has the card
        card_type = self._get_card_type_by_name(card_to_play)
        if not card_type:
            return False

        player_hand = game.board.hands[player_idx]
        has_card = any(c.type == card_type for c in player_hand)
        if not has_card:
            return False

        # Countess rule: must play Countess if you have King or Prince
        if len(player_hand) == 2:
            has_countess = any(c.type == CardType.COUNTESS for c in player_hand)
            has_king_or_prince = any(
                c.type in [CardType.KING, CardType.PRINCE] for c in player_hand
            )
            if has_countess and has_king_or_prince and card_type != CardType.COUNTESS:
                return False

        # Validate target if needed
        if card_type in [CardType.GUARD, CardType.PRIEST, CardType.BARON, CardType.KING]:
            # These cards require a target
            if target_player is None:
                return False

            target_idx = target_player - 1
            targetable = game.board.get_targetable_players(player_idx)
            if target_idx not in targetable:
                # Check if NO players are targetable (then card can still be played but has no effect)
                if not targetable:
                    return True  # Valid to play, just won't do anything
                return False

        # Validate guess for Guard
        if card_type == CardType.GUARD and guess_card:
            if guess_card == "Guard":
                return False  # Cannot guess Guard

        return True

    def apply(
        self,
        game: "LoveLetterGame",
        player: "Player",
        card_to_play: str,
        target_player: int | None = None,
        guess_card: str | None = None,
    ) -> dict | None:
        """Apply card play and execute its effect.

        Returns:
            dict with effect results (e.g., {'guard_correct': True}) or None
        """
        player_idx = game.state.current_player_idx
        card_type = self._get_card_type_by_name(card_to_play)

        # Find and discard the card
        card_obj = next(c for c in game.board.hands[player_idx] if c.type == card_type)
        game.board.discard_card(player_idx, card_obj)

        # Log action
        game.history.add_action(
            self,
            player,
            card_name=card_to_play,
            target=target_player,
            guess=guess_card,
            player_name=game.state.get_current_player_name(),
        )

        # Execute card effect and get result
        result = self._execute_effect(game, player_idx, card_type, target_player, guess_card)

        # Clear protection from previous turn
        game.board.protected.discard(player_idx)

        # Check if round is over
        if game.board.is_round_over():
            game.state.round_over = True
            winner_idx = game.board.get_round_winner()
            game.state.round_winner = winner_idx
            if winner_idx is not None:
                game.state.scores[winner_idx] = game.state.scores.get(winner_idx, 0) + 1

                # Check if someone won the game
                if game.state.scores[winner_idx] >= game.state.target_tokens:
                    game.state.is_over = True
                    game.state.winner = winner_idx
            return result

        # Advance to next active player
        next_idx = (player_idx + 1) % game.board.num_players
        while next_idx in game.board.eliminated:
            next_idx = (next_idx + 1) % game.board.num_players

        game.state.current_player_idx = next_idx

        return result

    def _execute_effect(
        self,
        game: "LoveLetterGame",
        player_idx: int,
        card_type: CardType,
        target_player: int | None,
        guess_card: str | None,
    ) -> dict | None:
        """Execute the card's special effect.

        Returns:
            dict with effect results or None
        """
        if card_type == CardType.GUARD:
            return self._guard_effect(game, player_idx, target_player, guess_card)
        elif card_type == CardType.PRIEST:
            return self._priest_effect(game, player_idx, target_player)
        elif card_type == CardType.BARON:
            return self._baron_effect(game, player_idx, target_player)
        elif card_type == CardType.HANDMAID:
            self._handmaid_effect(game, player_idx)
        elif card_type == CardType.PRINCE:
            self._prince_effect(game, player_idx, target_player)
        elif card_type == CardType.KING:
            self._king_effect(game, player_idx, target_player)
        elif card_type == CardType.PRINCESS:
            self._princess_effect(game, player_idx)
        # Countess has no effect
        return None

    def _guard_effect(
        self, game: "LoveLetterGame", player_idx: int, target: int | None, guess: str | None
    ) -> dict | None:
        """Guard: Guess another player's card.

        Returns:
            dict with {'guard_correct': bool, 'actual_card': str} or None
        """
        if target is None or guess is None:
            return None

        target_idx = target - 1
        if target_idx in game.board.eliminated or target_idx in game.board.protected:
            return None

        guess_type = self._get_card_type_by_name(guess)
        if not guess_type:
            return None

        # Check if guess is correct
        target_hand = game.board.hands[target_idx]
        if not target_hand:
            return None

        actual_card = target_hand[0]
        is_correct = actual_card.type == guess_type

        if is_correct:
            game.board.eliminate_player(target_idx)

        return {
            'guard_correct': is_correct,
            'actual_card': actual_card.name,
            'guessed_card': guess
        }

    def _priest_effect(self, game: "LoveLetterGame", player_idx: int, target: int | None) -> dict | None:
        """Priest: Look at another player's hand.

        Returns:
            dict with {'priest_saw': str} or None
        """
        if target is None:
            return None

        target_idx = target - 1
        if target_idx in game.board.eliminated or target_idx in game.board.protected:
            return None

        # Record knowledge
        target_hand = game.board.hands[target_idx]
        if target_hand:
            game.board.known_cards[player_idx][target_idx] = target_hand[0].type
            return {'priest_saw': target_hand[0].name}
        return None

    def _baron_effect(self, game: "LoveLetterGame", player_idx: int, target: int | None) -> dict | None:
        """Baron: Compare hands, lower value is eliminated.

        Returns:
            dict with comparison result or None
        """
        if target is None:
            return None

        target_idx = target - 1
        if target_idx in game.board.eliminated or target_idx in game.board.protected:
            return None

        player_hand = game.board.hands[player_idx]
        target_hand = game.board.hands[target_idx]

        if not player_hand or not target_hand:
            return None

        player_value = player_hand[0].value
        target_value = target_hand[0].value

        result = {
            'baron_compare': True,
            'player_card': player_hand[0].name,
            'target_card': target_hand[0].name
        }

        if player_value < target_value:
            game.board.eliminate_player(player_idx)
            result['winner'] = 'target'
        elif target_value < player_value:
            game.board.eliminate_player(target_idx)
            result['winner'] = 'player'
        else:
            result['winner'] = 'tie'

        return result

    def _handmaid_effect(self, game: "LoveLetterGame", player_idx: int) -> None:
        """Handmaid: Protection until next turn."""
        game.board.protected.add(player_idx)

    def _prince_effect(self, game: "LoveLetterGame", player_idx: int, target: int | None) -> None:
        """Prince: Force a player to discard and draw."""
        if target is None:
            target = player_idx + 1  # Target self if not specified

        target_idx = target - 1
        if target_idx in game.board.eliminated:
            return

        # Can target protected players with Prince
        target_hand = game.board.hands[target_idx]
        if not target_hand:
            return

        discarded_card = target_hand[0]
        game.board.discard_card(target_idx, discarded_card)

        # Check if Princess was discarded
        if discarded_card.type == CardType.PRINCESS:
            game.board.eliminate_player(target_idx)
            return

        # Draw new card (or removed card if deck empty)
        if game.board.deck:
            game.board.draw_card(target_idx)
        elif game.board.removed_card:
            game.board.hands[target_idx].append(game.board.removed_card)
            game.board.removed_card = None

    def _king_effect(self, game: "LoveLetterGame", player_idx: int, target: int | None) -> None:
        """King: Trade hands with another player."""
        if target is None:
            return

        target_idx = target - 1
        if target_idx in game.board.eliminated or target_idx in game.board.protected:
            return

        # Swap hands
        game.board.hands[player_idx], game.board.hands[target_idx] = (
            game.board.hands[target_idx],
            game.board.hands[player_idx],
        )

    def _princess_effect(self, game: "LoveLetterGame", player_idx: int) -> None:
        """Princess: Player is eliminated if this is played."""
        game.board.eliminate_player(player_idx)

    @staticmethod
    def _get_card_type_by_name(name: str) -> CardType | None:
        """Get CardType enum from card name string."""
        for card_type in CardType:
            if card_type.card_name == name:
                return card_type
        return None

    def to_history_record(
        self, player: "Player", card_name: str, target: int | None, guess: str | None, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        record = {
            "type": "play_card",
            "player": player_name,
            "card": card_name,
        }
        if target:
            record["target"] = f"Player {target}"
        if guess:
            record["guess"] = guess
        return record
