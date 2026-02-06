from datetime import datetime
from typing import Any, Optional
from sqlmodel import Field, SQLModel, Column, JSON


class Session(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    game_slug: str
    status: str = Field(default="active")
    config: dict = Field(sa_column=Column(JSON), default={})
    players: list[dict] = Field(sa_column=Column(JSON), default=[])
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ActionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    actor: str
    action: str
    payload: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Snapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    turn: int = Field(default=0)
    state: dict = Field(sa_column=Column(JSON), default={})
    board_view: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class RateLimit(SQLModel, table=True):
    ip: str = Field(primary_key=True, index=True)
    window_start: datetime = Field(index=True)
    count: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
