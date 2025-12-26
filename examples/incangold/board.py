"""Incan Gold board implementation."""

from typing import TYPE_CHECKING
from boardgamepy import Board
from cards import PathCard, create_deck, shuffle_deck, HazardType

if TYPE_CHECKING:
    from boardgamepy.protocols import ViewContext


class IncanGoldBoard(Board):
    """
    Incan Gold game board managing temple exploration.

    Tracks:
    - Deck of path cards
    - Revealed path cards
    - Gems on the path (unclaimed)
    - Players still in the temple vs. those who returned
    - Hazards encountered
    - Player collections (gems and artifacts)
    """

    def __init__(self, num_players: int):
        """
        Initialize board for Incan Gold.

        Args:
            num_players: Number of players (3-8)
        """
        if num_players < 3 or num_players > 8:
            raise ValueError("Incan Gold requires 3-8 players")

        self.num_players = num_players

        # Deck and path
        self.deck: list[PathCard] = []
        self.revealed_path: list[PathCard] = []
        self.gems_on_path: int = 0  # Undivided gems sitting on the path

        # Player tracking
        self.in_temple: set[int] = set()  # Players currently exploring
        self.returned_this_turn: set[int] = set()  # Players who just returned

        # Hazards encountered this round
        self.hazards_seen: dict[HazardType, int] = {}

        # Player collections
        self.player_gems: dict[int, int] = {i: 0 for i in range(num_players)}
        self.player_artifacts: dict[int, list[PathCard]] = {i: [] for i in range(num_players)}
        self.player_temp_gems: dict[int, int] = {i: 0 for i in range(num_players)}  # Gems in temple

    def setup_round(self) -> None:
        """Setup a new round of exploration."""
        self.deck = shuffle_deck(create_deck())
        self.revealed_path = []
        self.gems_on_path = 0
        self.in_temple = set(range(self.num_players))
        self.returned_this_turn = set()
        self.hazards_seen = {}
        self.player_temp_gems = {i: 0 for i in range(self.num_players)}

    def reveal_card(self) -> PathCard | None:
        """Reveal next card from deck."""
        if not self.deck:
            return None

        card = self.deck.pop(0)
        self.revealed_path.append(card)

        if card.is_hazard:
            # Track hazard
            if card.hazard in self.hazards_seen:
                self.hazards_seen[card.hazard] += 1
            else:
                self.hazards_seen[card.hazard] = 1
        elif card.is_treasure:
            # Add gems to path
            self.gems_on_path += card.value

        return card

    def is_round_over(self) -> bool:
        """Check if round is over (everyone returned or temple collapsed)."""
        # Temple collapsed if same hazard appeared twice
        for count in self.hazards_seen.values():
            if count >= 2:
                return True

        # Everyone returned
        return len(self.in_temple) == 0

    def did_temple_collapse(self) -> bool:
        """Check if temple collapsed (same hazard twice)."""
        for count in self.hazards_seen.values():
            if count >= 2:
                return True
        return False

    def distribute_gems_to_returners(self) -> None:
        """Distribute gems on path to players who are returning."""
        if not self.returned_this_turn or self.gems_on_path == 0:
            return

        returner_count = len(self.returned_this_turn)
        gems_each = self.gems_on_path // returner_count
        remaining_gems = self.gems_on_path % returner_count

        # Give each returner their share
        for player_idx in self.returned_this_turn:
            self.player_gems[player_idx] += gems_each
            # Also save their temp gems
            self.player_gems[player_idx] += self.player_temp_gems[player_idx]
            self.player_temp_gems[player_idx] = 0

        # Remaining gems stay on path
        self.gems_on_path = remaining_gems

    def distribute_treasure_to_explorers(self, gems: int) -> None:
        """Distribute treasure gems to players still in temple."""
        if not self.in_temple or gems == 0:
            return

        explorer_count = len(self.in_temple)
        gems_each = gems // explorer_count
        remaining_gems = gems % explorer_count

        # Give each explorer their share (to temp collection)
        for player_idx in self.in_temple:
            self.player_temp_gems[player_idx] += gems_each

        # Remaining gems go to path
        self.gems_on_path += remaining_gems

    def give_artifact_to_sole_returner(self, artifact: PathCard) -> int | None:
        """
        Give artifact to sole returner.

        Returns player_idx who got it, or None if multiple returners.
        """
        if len(self.returned_this_turn) == 1:
            player_idx = list(self.returned_this_turn)[0]
            self.player_artifacts[player_idx].append(artifact)
            return player_idx
        else:
            # Multiple returners or none - artifact stays in temple
            return None

    def players_lose_temp_gems(self, player_indices: set[int]) -> None:
        """Players lose their temp gems (temple collapsed)."""
        for player_idx in player_indices:
            self.player_temp_gems[player_idx] = 0

    def get_total_score(self, player_idx: int) -> int:
        """Get player's total score (gems + artifacts)."""
        gems = self.player_gems[player_idx]
        artifacts = sum(a.value for a in self.player_artifacts[player_idx])
        return gems + artifacts

    def get_view(self, context: "ViewContext") -> str:
        """
        Get board view.

        Players see:
        - All revealed path cards
        - Gems on the path
        - Who is still exploring vs. who returned
        - Their own collection
        """
        from boardgamepy.core.player import Player

        player: Player = context.player
        player_idx = int(player.team.split()[-1]) - 1

        lines = ["=== INCAN GOLD ===", ""]

        # Your status
        if player_idx in self.in_temple:
            status = f"{player.team}: 🏃 IN TEMPLE"
            temp_gems = self.player_temp_gems[player_idx]
            if temp_gems > 0:
                status += f" (carrying {temp_gems} gems)"
        else:
            status = f"{player.team}: 🏕️ SAFE AT CAMP"

        lines.append(status)
        lines.append("")

        # Revealed path
        if self.revealed_path:
            lines.append("Temple Path:")
            for i, card in enumerate(self.revealed_path, 1):
                lines.append(f"  {i}. {card}")
        else:
            lines.append("Temple Path: (unexplored)")

        lines.append("")

        if self.gems_on_path > 0:
            lines.append(f"💎 Gems on path: {self.gems_on_path}")
            lines.append("")

        # Explorer count
        explorer_count = len(self.in_temple)
        lines.append(f"Explorers in temple: {explorer_count}")
        lines.append("")

        # Your collection
        your_gems = self.player_gems[player_idx]
        your_artifacts = self.player_artifacts[player_idx]
        your_score = self.get_total_score(player_idx)

        lines.append("Your Collection:")
        lines.append(f"  Gems: {your_gems}")
        if your_artifacts:
            artifact_str = ", ".join(f"{a.value}pts" for a in your_artifacts)
            lines.append(f"  Artifacts: {artifact_str}")
        lines.append(f"  Total Score: {your_score}")

        return "\n".join(lines)
