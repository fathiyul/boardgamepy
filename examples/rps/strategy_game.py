"""Strategic Rock Paper Scissors with health and points."""

from dataclasses import dataclass, field
import random
import copy
from boardgamepy import Game, GameState, Board, Player, GameHistory
from boardgamepy.protocols import ViewContext
from actions import StrategyChooseAction

# Five possible effect levels (randomly assigned each round)
EFFECT_LEVELS = [
    {"win_points": 1, "lose_effect": 0, "lose_type": "none", "name": "Safe (+1/0)"},
    {"win_points": 2, "lose_effect": 1, "lose_type": "none", "name": "Low Risk (+2/0)"},
    {
        "win_points": 3,
        "lose_effect": 2,
        "lose_type": "points",
        "name": "Medium Risk (+3/-2pt)",
    },
    {
        "win_points": 4,
        "lose_effect": 1,
        "lose_type": "health",
        "name": "High Risk (+4/-1♥)",
    },
    {
        "win_points": 5,
        "lose_effect": 2,
        "lose_type": "health",
        "name": "Extreme Risk (+5/-2♥)",
    },
]


def randomize_effects() -> dict[str, dict]:
    """Randomly assign 3 of the 5 effects to rock/paper/scissors."""
    choices = ["rock", "paper", "scissors"]
    selected_effects = random.sample(EFFECT_LEVELS, 3)
    return {choice: effect for choice, effect in zip(choices, selected_effects)}


@dataclass
class StrategyRPSState(GameState):
    """Enhanced RPS with points and health."""

    current_round: int = 0
    max_rounds: int = 15  # Maximum rounds
    player1_choice: str | None = None
    player2_choice: str | None = None

    # Player 1 stats
    player1_score: int = 0
    player1_health: int = 3

    # Player 2 stats
    player2_score: int = 0
    player2_health: int = 3

    # Game over flag
    game_over: bool = False
    winner: str | None = None

    # Store last round's choices to display
    last_player1_choice: str | None = None
    last_player2_choice: str | None = None

    # Current round's effect mapping (randomized each round)
    # Maps choice -> (win_points, lose_effect, lose_type)
    effect_mapping: dict[str, dict] = field(default_factory=dict)

    # Last round's effect mapping (for UI display)
    last_effect_mapping: dict[str, dict] = field(default_factory=dict)


    def is_terminal(self) -> bool:
        """Game ends when someone reaches 10 points or dies."""
        return self.game_over

    def get_winner(self) -> str | None:
        """Return the winner."""
        return self.winner


class StrategyRPSBoard(Board):
    """Board showing current game state."""

    def get_view(self, context: ViewContext) -> str:
        """Return strategic board view."""
        state = context.game_state

        view = [
            "╔═══════════════════════════════════════════════╗",
            "║       STRATEGIC ROCK PAPER SCISSORS           ║",
            "╚═══════════════════════════════════════════════╝",
            "",
            f"Round: {state.current_round + 1}",
            "",
            "┌─────────────────────────────────────────────┐",
            "│  PLAYER 1                    PLAYER 2       │",
            f"│  Score: {state.player1_score:<2}                    Score: {state.player2_score:<2}      │",
            f"│  Health: {state.player1_health}                    Health: {state.player2_health}       │",
            "└─────────────────────────────────────────────┘",
        ]

        # Show current round's randomized effects
        if state.effect_mapping:
            view.extend(
                [
                    "",
                    "THIS ROUND'S EFFECTS:",
                ]
            )
            for choice in ["rock", "paper", "scissors"]:
                effect = state.effect_mapping.get(choice)
                if effect:
                    # Format the effect display
                    win_text = f"+{effect['win_points']}"
                    if effect["lose_type"] == "none":
                        lose_text = "0"
                    elif effect["lose_type"] == "points":
                        lose_text = f"-{effect['lose_effect']}pt"
                    elif effect["lose_type"] == "health":
                        lose_text = f"-{effect['lose_effect']}♥"

                    view.append(f"  {choice.capitalize():8} → {win_text}/{lose_text}")

        # Show previous round result
        if state.current_round > 0 and state.last_player1_choice:
            view.extend(
                [
                    "",
                    "Last Round:",
                    f"  P1: {state.last_player1_choice} vs P2: {state.last_player2_choice}",
                ]
            )

        return "\n".join(view)


class StrategyRPSGame(Game):
    """Strategic Rock Paper Scissors with points and health."""

    name = "Strategic RPS"
    min_players = 2
    max_players = 2

    def setup(self, **config):
        """Initialize the game."""
        self.state = StrategyRPSState()
        self.board = StrategyRPSBoard()
        self.history = GameHistory()
        self.history.start_new_round()
        self.players = [
            Player(name="Player 1", team="Player 1", player_idx=0),
            Player(name="Player 2", team="Player 2", player_idx=1),
        ]
        self.actions = [StrategyChooseAction()]

        # Randomize effects for first round
        self.state.effect_mapping = randomize_effects()

    def get_current_player(self):
        """Return current player."""
        if self.state.game_over:
            return None

        if self.state.player1_choice is None:
            return self.players[0]
        elif self.state.player2_choice is None:
            return self.players[1]
        return None

    def next_turn(self) -> None:
        """Advance to next turn - handled automatically in RPS after both players choose."""
        pass  # Turn advancement is handled in action.apply()
