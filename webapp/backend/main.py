import os
import sys
import asyncio
from pathlib import Path
from functools import partial
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

# Ensure repo root on sys.path so `webapp` and `examples` imports resolve when running from backend/ cwd
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))

from .db import get_db, init_db, AsyncSessionLocal
from .models import Session as SessionModel, Snapshot
from .registry import get_games_meta
from .schemas import ActionRequest, ActionResponse, CreateSessionRequest, SessionStateResponse
from .session_manager import session_manager

load_dotenv()

app = FastAPI(title="BoardGamePy Web API", version="0.1")

origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/games")
async def list_games():
    return [meta.__dict__ for meta in get_games_meta()]


@app.post("/games/{slug}/sessions", response_model=SessionStateResponse)
async def create_session(slug: str, req: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    if slug not in session_manager.registry:
        raise HTTPException(status_code=404, detail="Unknown game")

    human_seats = set(req.human_seats or [])
    config = req.config or {}
    if req.num_players:
        config["num_players"] = req.num_players
    if req.target:
        config["target"] = req.target

    active = await session_manager.create_session(db, slug, config, human_seats)

    # Kick AI turns if first player is AI
    async def send_event(message):
        await session_manager.broadcast(active.session_id, message)

    async def run_ai_after(session_id: str):
        async with AsyncSessionLocal() as session:
            await session_manager.auto_run_ai(session, session_id, send_event)

    asyncio.create_task(run_ai_after(active.session_id))

    data = session_manager.sessions[active.session_id].adapter.serialize_state(active.game)
    payload = SessionStateResponse(
        session_id=active.session_id,
        game_slug=slug,
        players=session_manager._players_meta(active.game, human_seats),
        state=data.get("state", {}),
        board_view=data.get("board_view"),
        board_cards=data.get("board_cards"),
        history=data.get("history"),
        turn=active.turn_counter,
    )
    return payload


@app.get("/games/{slug}/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session_state(slug: str, session_id: str, db: AsyncSession = Depends(get_db)):
    if slug not in session_manager.registry:
        raise HTTPException(status_code=404, detail="Unknown game")

    session_row = await db.get(SessionModel, session_id)
    if not session_row:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id in session_manager.sessions:
        active = session_manager.sessions[session_id]
        data = active.adapter.serialize_state(active.game)
        return SessionStateResponse(
            session_id=session_id,
            game_slug=slug,
            players=session_row.players,
            state=data.get("state", {}),
            board_view=data.get("board_view"),
            board_cards=data.get("board_cards"),
            history=data.get("history"),
            turn=active.turn_counter,
        )

    # Latest snapshot (fallback)
    from sqlmodel import select

    result = await db.exec(
        select(Snapshot).where(Snapshot.session_id == session_id).order_by(Snapshot.id.desc()).limit(1)
    )
    snap = result.first()

    state = snap.state if snap else {}
    board_view = snap.board_view if snap else None

    return SessionStateResponse(
        session_id=session_id,
        game_slug=slug,
        players=session_row.players,
        state=state,
        board_view=board_view,
        board_cards=None,
        history=None,
        turn=snap.turn if snap else None,
    )


@app.get("/games/{slug}/sessions/{session_id}/actions/{player_idx}")
async def list_actions(slug: str, session_id: str, player_idx: int):
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not active")
    active = session_manager.sessions[session_id]
    if slug != active.adapter.meta.slug:
        raise HTTPException(status_code=400, detail="Game mismatch")
    if player_idx >= len(active.game.players):
        raise HTTPException(status_code=400, detail="Invalid player index")
    player = active.game.players[player_idx]
    return active.adapter.valid_actions_for_player(active.game, player)


@app.post("/games/{slug}/sessions/{session_id}/action", response_model=ActionResponse)
async def submit_action(slug: str, session_id: str, req: ActionRequest, db: AsyncSession = Depends(get_db)):
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not active")

    active = session_manager.sessions[session_id]
    if slug != active.adapter.meta.slug:
        raise HTTPException(status_code=400, detail="Game mismatch")

    # Validate player_idx existence
    if req.player_idx >= len(active.game.players):
        raise HTTPException(status_code=400, detail="Invalid player index")

    try:
        result = await session_manager.apply_action(
            db,
            session_id=session_id,
            player_idx=req.player_idx,
            action_name=req.action,
            params=req.params,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Broadcast action
    await session_manager.broadcast(
        session_id,
        {
            "type": "action_applied",
            "turn": result["turn"],
            "action": result["action"],
            "params": result["params"],
            "state": result["state"],
        },
    )

    # Auto-run AI after human move
    async def send_event(message):
        await session_manager.broadcast(session_id, message)

    async def run_ai_after(session_id: str):
        async with AsyncSessionLocal() as session:
            await session_manager.auto_run_ai(session, session_id, send_event)

    asyncio.create_task(run_ai_after(session_id))

    return ActionResponse(
        turn=result["turn"],
        action=result["action"],
        params=result["params"],
        state=result["state"],
    )


@app.websocket("/ws/sessions/{session_id}")
async def websocket_session(session_id: str, websocket: WebSocket):
    await websocket.accept()
    if session_id not in session_manager.sessions:
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return

    session_manager.attach_socket(session_id, websocket)

    # Send initial state
    active = session_manager.sessions[session_id]
    await websocket.send_json(
        {
            "type": "session_state",
            "state": active.adapter.serialize_state(active.game),
            "turn": active.turn_counter,
        }
    )

    try:
        while True:
            await websocket.receive_text()
            # This WS is mostly server-push; ignore client messages
    except WebSocketDisconnect:
        session_manager.detach_socket(session_id, websocket)
    except Exception:
        session_manager.detach_socket(session_id, websocket)
        await websocket.close()


@app.exception_handler(Exception)
async def unhandled(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})
