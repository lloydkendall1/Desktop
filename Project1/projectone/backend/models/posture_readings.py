from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class PostureReading(SQLModel, table=True):
    __tablename__ = "posture_readings"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    posture_class_id: int = Field(foreign_key="posture_classes.id")
    recorded_at: Optional[datetime] = None
    confidence: float
    spine_angle: Optional[float] = None
    head_angle: Optional[float] = None
