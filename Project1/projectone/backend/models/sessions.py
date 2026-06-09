from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class PostureSession(SQLModel, table=True):
    __tablename__ = "sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    notes: Optional[str] = None
