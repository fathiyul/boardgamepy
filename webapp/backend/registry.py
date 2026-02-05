import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Ensure repository root is on sys.path for `examples` and `boardgamepy`
ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from boardgamepy.protocols import SimpleViewContext
from sqlmodel.ext.asyncio.session import AsyncSession


@dataclass
class GameMeta:
    slug: str
    title: str
    description: str
    min_players: int
    max_players: int
    playable: bool = True
    tags: list[str] | None = None


class GameAdapter:
    meta: GameMeta

    def create_game(self, config: dict[str, Any]):
        raise NotImplementedError

    def configure_players(self, game, human_seats: set[int], config: dict[str, Any]):
        """Optional hook to assign agents or names after creation."""
        return None

    def default_players(self) -> list[dict]:
        """Metadata about default players for lobby display."""
        raise NotImplementedError

    def valid_actions_for_player(self, game, player) -> list[dict[str, Any]]:
        raise NotImplementedError

    def apply_action(self, game, player, action_name: str, params: dict[str, Any]):
        raise NotImplementedError

    def serialize_state(self, game, viewer=None) -> dict[str, Any]:
        raise NotImplementedError

    def is_terminal(self, game) -> bool:
        return game.state.is_terminal()

    def get_current_player(self, game):
        return game.get_current_player()

    async def after_action(self, session_id: str, game, db: AsyncSession):
        """Hook for persistence after each action."""
        return None


# ---------------------------------------------------------------------------
# RPS Adapter
# ---------------------------------------------------------------------------


class RPSAdapter(GameAdapter):
    def __init__(self):
        rps_dir = ROOT_DIR / "examples" / "rps"
        if str(rps_dir) not in sys.path:
            sys.path.append(str(rps_dir))
        from examples.rps.strategy_game import StrategyRPSGame
        self.meta = GameMeta(
            slug="rps",
            title="Strategic Rock Paper Scissors",
            description="Best-of-15 with randomized effects each round.",
            min_players=2,
            max_players=2,
            tags=["beginner", "fast"],
        )
        self._game_cls = StrategyRPSGame

    def _make_openrouter_llm(self, model_name: str):
        try:
            from langchain_openai import ChatOpenAI
        except Exception as e:
            raise ImportError("langchain-openai is required for AI opponent; pip install langchain-openai") from e

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for AI opponent")

        return ChatOpenAI(model=model_name, api_key=api_key, base_url="https://openrouter.ai/api/v1")

    def create_game(self, config: dict[str, Any]):
        game = self._game_cls()
        game.setup(**config)
        return game

    def configure_players(self, game, human_seats: set[int], config: dict[str, Any]):
        """Assign agents to AI seats based on selected model."""
        opponent_model = config.get("opponent_model", "random")
        for idx, player in enumerate(game.players):
            if idx in human_seats:
                player.agent = None
                player.agent_type = "human"
                player.name = player.name or f"Player {idx+1}"
            else:
                if opponent_model == "random":
                    player.agent = RandomRPSAgent()
                    player.name = "Random"
                else:
                    llm = self._make_openrouter_llm(opponent_model)
                    from examples.rps.prompts_strategy import StrategyRPSPromptBuilder
                    from boardgamepy.ai import LLMAgent
                    from examples.rps.actions import StrategyChooseAction

                    prompt_builder = StrategyRPSPromptBuilder()
                    base_agent = LLMAgent(llm=llm, prompt_builder=prompt_builder, output_schema=StrategyChooseAction.OutputSchema)
                    player.agent = base_agent
                    short = opponent_model.split("/", 1)[-1]
                    player.name = short
                player.agent_type = "ai"
                player.team = player.team or f"Player {idx+1}"
        return game

    def default_players(self) -> list[dict]:
        return [
            {"name": "Player 1", "idx": 0, "role": None},
            {"name": "Player 2", "idx": 1, "role": None},
        ]

    def valid_actions_for_player(self, game, player) -> list[dict[str, Any]]:
        actions = game.get_valid_actions(player)
        out: list[dict[str, Any]] = []
        for action in actions:
            action_cls = action if isinstance(action, type) else action.__class__
            schema = None
            if getattr(action_cls, "OutputSchema", None):
                schema = action_cls.OutputSchema.model_json_schema()
                # Remove reasoning field for UI simplicity
                if "properties" in schema and "reasoning" in schema["properties"]:
                    schema["properties"].pop("reasoning", None)
                    if "required" in schema and "reasoning" in schema["required"]:
                        schema["required"].remove("reasoning")
                # Add enum hints for RPS choices
                if action_cls.name == "choose" and "properties" in schema and "choice" in schema["properties"]:
                    schema["properties"]["choice"]["enum"] = ["rock", "paper", "scissors"]
            out.append(
                {
                    "name": action_cls.name,
                    "display_name": getattr(action_cls, "display_name", action_cls.name),
                    "schema": schema,
                }
            )
        return out

    def apply_action(self, game, player, action_name: str, params: dict[str, Any]):
        from examples.rps.actions import StrategyChooseAction

        if action_name != StrategyChooseAction.name:
            raise ValueError("Unknown action")
        action = StrategyChooseAction()
        # Ignore optional reasoning param from UI
        clean_params = {k: v for k, v in params.items() if k != "reasoning"}
        if not action.validate(game, player, **clean_params):
            raise ValueError("Invalid action")
        action.apply(game, player, **clean_params)
        return action

    def serialize_state(self, game, viewer=None) -> dict[str, Any]:
        from dataclasses import asdict, is_dataclass
        from boardgamepy.protocols import SimpleViewContext

        state = game.state
        state_data = asdict(state) if is_dataclass(state) else state.__dict__

        board_view = None
        if hasattr(game, "board") and game.board is not None:
            context = SimpleViewContext(player=viewer or None, game_state=state)
            board_view = game.board.get_view(context)

        return {
            "state": state_data,
            "board_view": board_view,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def get_registry() -> Dict[str, GameAdapter]:
    # Extendable registry; other games can be added later
    adapters: Dict[str, GameAdapter] = {
        "rps": RPSAdapter(),
    }
    return adapters


def get_games_meta() -> List[GameMeta]:
    metas = [adapter.meta for adapter in get_registry().values()]
    # Non-playable placeholders for remaining examples
    placeholders = [
        GameMeta(slug="codenames", title="Codenames", description="Team word association with hidden roles.", min_players=4, max_players=6, playable=False),
        GameMeta(slug="loveletter", title="Love Letter", description="Deduction card game with hidden roles.", min_players=2, max_players=4, playable=False),
        GameMeta(slug="sushigo", title="Sushi Go", description="Draft-and-pass card game.", min_players=2, max_players=5, playable=False),
        GameMeta(slug="wavelength", title="Wavelength", description="Team guessing on a spectrum.", min_players=4, max_players=6, playable=False),
        GameMeta(slug="splendor", title="Splendor", description="Engine-building resource game.", min_players=2, max_players=4, playable=False),
        GameMeta(slug="coup", title="Coup", description="Bluffing and deduction.", min_players=2, max_players=6, playable=False),
        GameMeta(slug="incangold", title="Incan Gold", description="Push-your-luck treasure hunt.", min_players=3, max_players=8, playable=False),
        GameMeta(slug="wythoff", title="Wythoff", description="Two-pile Nim variant.", min_players=2, max_players=2, playable=False),
    ]
    # Avoid duplicate slugs
    existing = {m.slug for m in metas}
    metas.extend([m for m in placeholders if m.slug not in existing])
    return metas


# ---------------------------------------------------------------------------
# Simple random agent for RPS
# ---------------------------------------------------------------------------


class RandomRPSAgent:
    def get_action(self, game, player):
        import random
        choice = random.choice(["rock", "paper", "scissors"])
        from examples.rps.actions import StrategyChoiceOutput
        return StrategyChoiceOutput(choice=choice, reasoning=None)
