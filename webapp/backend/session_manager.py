import asyncio
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Set

from fastapi import WebSocket
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import ActionLog, Session as SessionModel, Snapshot
from .registry import GameAdapter, get_registry


@dataclass
class ActiveSession:
    session_id: str
    adapter: GameAdapter
    game: Any
    human_players: set[int] = field(default_factory=set)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    sockets: Set[WebSocket] = field(default_factory=set)
    turn_counter: int = 0


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ActiveSession] = {}
        self.registry = get_registry()

    def _ensure_adapter(self, slug: str) -> GameAdapter:
        if slug not in self.registry:
            raise ValueError("Unknown game")
        return self.registry[slug]

    async def create_session(
        self,
        db: AsyncSession,
        game_slug: str,
        config: dict,
        human_seats: set[int],
    ) -> ActiveSession:
        adapter = self._ensure_adapter(game_slug)
        game = adapter.create_game(config)
        # Configure agents for AI seats
        adapter.configure_players(game, human_seats, config)
        session_id = uuid.uuid4().hex[:12]
        active = ActiveSession(
            session_id=session_id,
            adapter=adapter,
            game=game,
            human_players=human_seats,
        )
        self.sessions[session_id] = active

        # Persist session row
        session_row = SessionModel(
            id=session_id,
            game_slug=game_slug,
            config=config,
            players=self._players_meta(game, human_seats),
        )
        db.add(session_row)
        await db.commit()
        await db.refresh(session_row)

        # Take initial snapshot
        await self._persist_snapshot(db, active)
        return active

    def _players_meta(self, game, human_seats: set[int]):
        meta = []
        for idx, player in enumerate(getattr(game, "players", [])):
            meta.append(
                {
                    "idx": idx,
                    "team": player.team,
                    "name": player.name,
                    "human": idx in human_seats,
                }
            )
        return meta

    async def _persist_snapshot(self, db: AsyncSession, active: ActiveSession):
        data = active.adapter.serialize_state(active.game)
        snap = Snapshot(
            session_id=active.session_id,
            turn=active.turn_counter,
            state=data.get("state", {}),
            board_view=data.get("board_view"),
        )
        db.add(snap)
        await db.commit()
        await db.refresh(snap)
        return snap

    async def _log_action(self, db: AsyncSession, session_id: str, actor: str, action: str, payload: dict):
        log = ActionLog(
            session_id=session_id,
            actor=actor,
            action=action,
            payload=payload,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    async def apply_action(
        self,
        db: AsyncSession,
        session_id: str,
        player_idx: int,
        action_name: str,
        params: dict[str, Any],
    ) -> dict:
        if session_id not in self.sessions:
            raise ValueError("Session not active")
        active = self.sessions[session_id]
        adapter = active.adapter
        game = active.game

        async with active.lock:
            player = game.players[player_idx]
            action_obj = adapter.apply_action(game, player, action_name, params)
            active.turn_counter += 1
            await self._log_action(db, session_id, player.team or f"Player {player_idx+1}", action_name, params)
            await adapter.after_action(session_id, game, db)
            snap = await self._persist_snapshot(db, active)
            return {
                "action": action_name,
                "params": params,
                "turn": active.turn_counter,
                "snapshot": snap,
                "state": adapter.serialize_state(game),
            }

    async def auto_run_ai(self, db: AsyncSession, session_id: str, send_event: callable):
        """Keep running AI turns until a human turn or game over."""
        if session_id not in self.sessions:
            return
        active = self.sessions[session_id]
        adapter = active.adapter

        while True:
            game = active.game
            if adapter.is_terminal(game):
                break
            current = adapter.get_current_player(game)
            if current is None:
                break
            idx = getattr(current, "player_idx", None) or 0
            if idx in active.human_players:
                break

            # AI turn
            ai_action = await self._get_ai_action(adapter, game, current)
            result = await self.apply_action(db, session_id, idx, ai_action[0], ai_action[1])
            await send_event(
                {
                    "type": "action_applied",
                    "turn": result["turn"],
                    "action": result["action"],
                    "params": result["params"],
                    "state": result["state"],
                }
            )

        # Terminal state broadcast
        if adapter.is_terminal(active.game):
            await send_event(
                {
                    "type": "game_over",
                    "state": adapter.serialize_state(active.game),
                }
            )

    async def _get_ai_action(self, adapter: GameAdapter, game, player):
        """Simple AI: use player.agent if available; otherwise random choice for RPS."""
        import random
        import json
        import re
        from pydantic import BaseModel, ValidationError

        # If agent has get_action (like LoggedLLMAgent)
        if hasattr(player, "agent") and player.agent is not None:
            if hasattr(player.agent, "get_action"):
                try:
                    llm_output = await _maybe_async(player.agent.get_action, game, player)
                    if isinstance(llm_output, BaseModel):
                        data = llm_output.model_dump()
                    elif isinstance(llm_output, dict):
                        data = llm_output
                    else:
                        # Attempt to coerce string to json
                        raw = str(llm_output)
                        match = re.search(r"\{.*\}", raw, re.DOTALL)
                        if match:
                            data = json.loads(match.group(0))
                        else:
                            raise ValueError("LLM output not JSON")
                    action_name = adapter.valid_actions_for_player(game, player)[0]["name"]
                    if action_name == "guess" and data.get("action") == "pass":
                        action_name = "pass"
                    return action_name, {k: v for k, v in data.items() if k not in {"reasoning", "action"}}
                except (ValidationError, json.JSONDecodeError, ValueError):
                    pass

        # Fallback random for RPS
        choices = ["rock", "paper", "scissors"]
        action_name = adapter.valid_actions_for_player(game, player)[0]["name"]
        return action_name, {"choice": random.choice(choices)}

    def attach_socket(self, session_id: str, ws: WebSocket):
        if session_id not in self.sessions:
            return
        self.sessions[session_id].sockets.add(ws)

    def detach_socket(self, session_id: str, ws: WebSocket):
        if session_id not in self.sessions:
            return
        self.sessions[session_id].sockets.discard(ws)

    async def broadcast(self, session_id: str, message: dict):
        if session_id not in self.sessions:
            return
        for ws in list(self.sessions[session_id].sockets):
            try:
                await ws.send_json(message)
            except Exception:
                pass


async def _maybe_async(fn, *args, **kwargs):
    res = fn(*args, **kwargs)
    if asyncio.iscoroutine(res):
        return await res
    return res


session_manager = SessionManager()
