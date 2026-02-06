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
# Codenames Adapter
# ---------------------------------------------------------------------------


class CodenamesAdapter(GameAdapter):
    def __init__(self):
        codenames_dir = ROOT_DIR / "examples" / "codenames"
        if str(codenames_dir) not in sys.path:
            sys.path.append(str(codenames_dir))
        from examples.codenames.game import CodenamesGame

        self.meta = GameMeta(
            slug="codenames",
            title="Codenames",
            description="Team word association (Spymaster + Operatives).",
            min_players=4,
            max_players=4,
            tags=["team", "hidden-info"],
        )
        self._game_cls = CodenamesGame
        # Load codename pool
        txt_path = codenames_dir / "codenames.txt"
        self._pool = [line.strip() for line in txt_path.read_text().splitlines() if line.strip()]

    def _make_openrouter_llm(self, model_name: str):
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for AI opponents")
        return ChatOpenAI(model=model_name, api_key=api_key, base_url="https://openrouter.ai/api/v1")

    def create_game(self, config: dict[str, Any]):
        game = self._game_cls()
        game.setup(codenames=self._pool)
        return game

    def configure_players(self, game, human_seats: set[int], config: dict[str, Any]):
        from boardgamepy.ai import LLMAgent
        from examples.codenames.prompts import SpymasterPromptBuilder, OperativesPromptBuilder
        from examples.codenames.actions import ClueAction, GuessAction

        team_model_map = config.get("team_model_map", {})
        default_model = config.get("opponent_model", "google/gemini-3-flash-preview")

        for idx, player in enumerate(game.players):
            if idx in human_seats:
                player.agent = None
                player.agent_type = "human"
                continue

            model = team_model_map.get(str(idx)) or default_model
            if model == "random":
                model = default_model
            llm = self._make_openrouter_llm(model)
            if player.role == "Spymaster":
                builder = SpymasterPromptBuilder()
                base_agent = LLMAgent(llm=llm, prompt_builder=builder, output_schema=ClueAction.OutputSchema)
            else:
                builder = OperativesPromptBuilder()
                base_agent = LLMAgent(llm=llm, prompt_builder=builder, output_schema=GuessAction.OutputSchema)
            player.agent = base_agent
            player.agent_type = "ai"

    def default_players(self) -> list[dict]:
        return [
            {"name": "Red Spymaster", "idx": 0, "role": "Spymaster", "team": "Red"},
            {"name": "Red Operatives", "idx": 1, "role": "Operatives", "team": "Red"},
            {"name": "Blue Spymaster", "idx": 2, "role": "Spymaster", "team": "Blue"},
            {"name": "Blue Operatives", "idx": 3, "role": "Operatives", "team": "Blue"},
        ]

    def valid_actions_for_player(self, game, player) -> list[dict[str, Any]]:
        actions = game.get_valid_actions(player)
        out: list[dict[str, Any]] = []
        for action in actions:
            action_cls = action if isinstance(action, type) else action
            schema = None
            if getattr(action_cls, "OutputSchema", None):
                schema = action_cls.OutputSchema.model_json_schema()
            # For guess, add enum of hidden codenames for convenience
            if action_cls.name == "guess" and schema:
                hidden = [c.code for c in game.board.cards.values() if c.state == "Hidden"]
                if "properties" in schema and "codename" in schema["properties"]:
                    schema["properties"]["codename"]["enum"] = hidden
            out.append(
                {
                    "name": action_cls.name,
                    "display_name": getattr(action_cls, "display_name", action_cls.name),
                    "schema": schema,
                }
            )
        return out

    def apply_action(self, game, player, action_name: str, params: dict[str, Any]):
        from examples.codenames.actions import ClueAction, GuessAction, PassAction

        action_map = {
            ClueAction.name: ClueAction,
            GuessAction.name: GuessAction,
            PassAction.name: PassAction,
        }
        if action_name not in action_map:
            raise ValueError("Unknown action")
        action = action_map[action_name]()
        clean_params = {k: v for k, v in params.items() if k not in {"reasoning", "action"}}
        if action_name == "pass":
            clean_params = {}
        if not action.validate(game, player, **clean_params):
            raise ValueError("Invalid action")
        action.apply(game, player, **clean_params)
        return action

    def serialize_state(self, game, viewer=None) -> dict[str, Any]:
        from dataclasses import asdict, is_dataclass
        from boardgamepy.protocols import SimpleViewContext
        state = game.state
        state_data = asdict(state) if is_dataclass(state) else state.__dict__

        # Choose viewer: provided, else first human, else Red Operatives
        view_player = viewer
        if view_player is None:
            humans = [p for p in game.players if getattr(p, "agent_type", "ai") == "human"]
            view_player = humans[0] if humans else game.get_player(team="Red", role="Operatives") or game.players[0]

        board_view = None
        if hasattr(game, "board") and game.board is not None:
            context = SimpleViewContext(player=view_player, game_state=state)
            board_view = game.board.get_view(context)

        board_cards = []
        if hasattr(game, "board") and game.board is not None and getattr(game.board, "cards", None):
            for card in game.board.cards.values():
                visible_type = card.type if (card.state == "Revealed" or view_player.role == "Spymaster" or getattr(game.state, "is_over", False)) else None
                board_cards.append(
                    {
                        "id": card.id,
                        "code": card.code,
                        "state": card.state,
                        "type": visible_type,
                    }
                )
            board_cards.sort(key=lambda c: c["id"])

        history_entries: list[dict[str, Any]] = []
        if getattr(game, "history", None) is not None:
            for round_idx, round_ in enumerate(game.history.rounds, start=1):
                if not round_.actions:
                    continue
                for action in round_.actions:
                    entry = dict(action)
                    entry["round"] = round_idx
                    history_entries.append(entry)

        return {
            "state": state_data,
            "board_view": board_view,
            "board_cards": board_cards,
            "history": history_entries,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def get_registry() -> Dict[str, GameAdapter]:
    # Extendable registry; other games can be added later
    adapters: Dict[str, GameAdapter] = {
        "rps": RPSAdapter(),
        "codenames": CodenamesAdapter(),
    }
    return adapters


def get_games_meta() -> List[GameMeta]:
    metas = [adapter.meta for adapter in get_registry().values()]
    # Non-playable placeholders for remaining examples
    placeholders = [
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
