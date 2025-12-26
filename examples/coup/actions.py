"""Coup game actions."""

from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field

from boardgamepy import Action
from characters import CharacterType

if TYPE_CHECKING:
    from game import CoupGame
    from boardgamepy.core.player import Player


class CoupActionOutput(BaseModel):
    """LLM structured output for Coup actions."""

    action: Literal[
        "income", "foreign_aid", "coup", "tax", "assassinate", "steal", "exchange"
    ] = Field(..., description="Which action to take")

    target_player: int | None = Field(
        None, description="Target player number (for Coup, Assassinate, Steal)"
    )

    challenge: bool = Field(
        False, description="Set to true if you want to challenge the current action"
    )

    character_to_reveal: Literal["Duke", "Assassin", "Captain", "Ambassador", "Contessa"] | None = Field(
        None, description="If you lost influence, which character to reveal"
    )

    reasoning: str | None = Field(None, description="Explanation of your decision")


class TakeTurnAction(Action["CoupGame"]):
    """Main action for taking a turn in Coup."""

    name = "take_turn"
    display_name = "Take Turn"
    OutputSchema = CoupActionOutput

    def validate(
        self,
        game: "CoupGame",
        player: "Player",
        action: str,
        target_player: int | None = None,
        character_to_reveal: str | None = None,
        **kwargs,
    ) -> bool:
        """Validate the action."""
        player_idx = game.state.current_player_idx

        # Check if player has influence
        if not game.board.has_influence(player_idx):
            return False

        # Validate based on action type
        if action == "income":
            return True

        elif action == "foreign_aid":
            return True

        elif action == "coup":
            # Must have at least 7 coins
            if game.board.coins[player_idx] < 7:
                return False
            # Must have a target
            if target_player is None:
                return False
            target_idx = target_player - 1
            # Target must have influence
            if not game.board.has_influence(target_idx):
                return False
            # If you have 10+ coins, you MUST coup
            return True

        elif action == "tax":
            # Claim to be Duke
            return True

        elif action == "assassinate":
            # Must have 3 coins
            if game.board.coins[player_idx] < 3:
                return False
            # Must have a target
            if target_player is None:
                return False
            target_idx = target_player - 1
            if not game.board.has_influence(target_idx):
                return False
            return True

        elif action == "steal":
            # Must have a target
            if target_player is None:
                return False
            target_idx = target_player - 1
            if not game.board.has_influence(target_idx):
                return False
            return True

        elif action == "exchange":
            # Claim to be Ambassador
            return True

        return False

    def apply(
        self,
        game: "CoupGame",
        player: "Player",
        action: str,
        target_player: int | None = None,
        character_to_reveal: str | None = None,
        **kwargs,
    ) -> None:
        """Apply the action."""
        player_idx = game.state.current_player_idx

        # Execute action (simplified - no challenges/blocks for now)
        if action == "income":
            game.board.add_coins(player_idx, 1)
            game.history.add_action(
                self,
                player,
                action_type="income",
                player_name=game.state.get_current_player_name(),
            )

        elif action == "foreign_aid":
            game.board.add_coins(player_idx, 2)
            game.history.add_action(
                self,
                player,
                action_type="foreign_aid",
                player_name=game.state.get_current_player_name(),
            )

        elif action == "coup":
            target_idx = target_player - 1
            game.board.remove_coins(player_idx, 7)
            # Target loses influence
            game.board.reveal_random_influence(target_idx)
            game.history.add_action(
                self,
                player,
                action_type="coup",
                target=f"Player {target_player}",
                player_name=game.state.get_current_player_name(),
            )

        elif action == "tax":
            # Duke ability - simplified (no challenge)
            game.board.add_coins(player_idx, 3)
            game.history.add_action(
                self,
                player,
                action_type="tax",
                claimed_character="Duke",
                player_name=game.state.get_current_player_name(),
            )

        elif action == "assassinate":
            target_idx = target_player - 1
            game.board.remove_coins(player_idx, 3)
            # Simplified - no block/challenge
            game.board.reveal_random_influence(target_idx)
            game.history.add_action(
                self,
                player,
                action_type="assassinate",
                target=f"Player {target_player}",
                claimed_character="Assassin",
                player_name=game.state.get_current_player_name(),
            )

        elif action == "steal":
            target_idx = target_player - 1
            # Steal up to 2 coins
            amount = min(2, game.board.coins[target_idx])
            game.board.transfer_coins(target_idx, player_idx, amount)
            game.history.add_action(
                self,
                player,
                action_type="steal",
                target=f"Player {target_player}",
                amount=amount,
                claimed_character="Captain",
                player_name=game.state.get_current_player_name(),
            )

        elif action == "exchange":
            # Ambassador ability - simplified
            # Draw 2, return 2
            drawn = game.board.exchange_with_court(player_idx)
            if drawn:
                # Add to hand temporarily
                temp_hand = [
                    c for c in game.board.influence[player_idx] if not c.revealed
                ] + drawn

                # For simplicity, keep best 2 cards
                # In real game, player chooses
                temp_hand.sort(key=lambda c: c.type.char_name)
                to_keep = temp_hand[:2]
                to_return = [c for c in temp_hand if c not in to_keep]

                # Update influence
                for i, card in enumerate(game.board.influence[player_idx]):
                    if not card.revealed:
                        game.board.influence[player_idx].remove(card)

                game.board.influence[player_idx].extend(to_keep)
                game.board.return_to_court(to_return)

            game.history.add_action(
                self,
                player,
                action_type="exchange",
                claimed_character="Ambassador",
                player_name=game.state.get_current_player_name(),
            )

        # Check if game is over
        active_players = game.board.get_active_players()
        if len(active_players) == 1:
            game.state.is_over = True
            game.state.winner = active_players[0]
            return

        # Advance to next player with influence
        next_idx = (player_idx + 1) % game.board.num_players
        while not game.board.has_influence(next_idx):
            next_idx = (next_idx + 1) % game.board.num_players

        game.state.current_player_idx = next_idx

    def to_history_record(
        self, player: "Player", action_type: str, player_name: str, **params
    ) -> dict:
        """Convert to history record."""
        record = {
            "type": action_type,
            "player": player_name,
        }
        if "target" in params:
            record["target"] = params["target"]
        if "amount" in params:
            record["amount"] = params["amount"]
        if "claimed_character" in params:
            record["claimed"] = params["claimed_character"]
        return record
