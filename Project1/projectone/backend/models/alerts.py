from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id")
    posture_reading_id: Optional[int] = Field(default=None, foreign_key="posture_readings.id")
    triggered_at: Optional[datetime] = None
    alert_type: str  # 'buzzer' | 'led' | 'speaker' | 'oled_message'
    duration_ms: Optional[int] = None
