"""Game history tracking."""

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from boardgamepy.core.action import Action
    from boardgamepy.core.player import Player


@dataclass
class Round:
    """
    Container for actions in a single round/turn.

    A round typically represents one complete cycle of turns
    (e.g., all players taking one turn each).
    """

    actions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GameHistory:
    """
    Track all game actions over time.

    Maintains a log of all actions taken during the game,
    organized into rounds. This is used for:
    - Generating LLM prompts with game context
    - Replay and debugging
    - Game analysis
    """

    rounds: list[Round] = field(default_factory=list)

    def start_new_round(self) -> Round:
        """
        Create and append a new round.

        Returns:
            The newly created round
        """
        round_ = Round()
        self.rounds.append(round_)
        return round_

    def _current_round(self) -> Round:
        """
        Get the current round, creating one if none exists.

        Returns:
            Current round
        """
        if not self.rounds:
            return self.start_new_round()
        return self.rounds[-1]

    def add_action(
        self, action: "Action", player: "Player", **params: Any
    ) -> None:
        """
        Add an action to the current round.

        Args:
            action: Action instance that was performed
            player: Player who performed the action
            **params: Action-specific parameters
        """
        round_ = self._current_round()
        record = action.to_history_record(player, **params)
        round_.actions.append(record)

    def to_prompt(self, max_rounds: int | None = 3) -> str:
        """
        Convert history to text suitable for LLM prompts.

        Args:
            max_rounds: Maximum number of recent rounds to include
                       (None for all rounds)

        Returns:
            Text representation of game history
        """
        # Filter to non-empty rounds
        non_empty = [
            (i, r) for i, r in enumerate(self.rounds, start=1) if r.actions
        ]

        if not non_empty:
            return "No previous rounds have been played yet."

        # Keep only last N rounds if specified
        if max_rounds is not None and max_rounds > 0:
            non_empty = non_empty[-max_rounds:]

        lines: list[str] = ["Game history so far:"]

        for round_index, round_ in non_empty:
            lines.append(f"\nRound {round_index}:")
            for action_record in round_.actions:
                # Format depends on action type
                action_type = action_record.get("type", "unknown")
                lines.append(f"- {self._format_action(action_record)}")

        return "\n".join(lines)

    def _format_action(self, action_record: dict[str, Any]) -> str:
        """
        Format a single action record for display.

        This is a default implementation that can be overridden
        by subclasses for game-specific formatting.

        Args:
            action_record: Action record dictionary

        Returns:
            Formatted action string
        """
        action_type = action_record.get("type", "unknown")
        player_info = action_record.get("player", "Unknown")

        # Basic formatting - games can override for custom formatting
        parts = [f"{player_info}"]

        # Add action type
        parts.append(action_type)

        # Add any other fields (excluding type and player)
        for key, value in action_record.items():
            if key not in ("type", "player"):
                parts.append(f"{key}={value}")

        return " ".join(parts)
