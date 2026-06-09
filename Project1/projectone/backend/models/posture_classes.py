from typing import Optional

from sqlmodel import Field, SQLModel


class PostureClass(SQLModel, table=True):
    __tablename__ = "posture_classes"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    severity: str  # 'good' | 'warning' | 'bad'
