from typing import Any, List, Optional
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    num_players: Optional[int] = None
    target: Optional[int] = None
    human_seats: List[int] = Field(default_factory=lambda: [0])
    config: dict[str, Any] | None = None


class SessionStateResponse(BaseModel):
    session_id: str
    game_slug: str
    players: list[dict]
    state: dict
    board_view: str | None = None
    board_cards: list[dict] | None = None
    history: list[dict] | None = None
    turn: int | None = None


class ActionRequest(BaseModel):
    player_idx: int
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


class ActionResponse(BaseModel):
    turn: int
    action: str
    params: dict[str, Any]
    state: dict
