from datetime import datetime, timezone

from sqlmodel import Session, select

from models.sessions import PostureSession


def start(session: Session, user_id: int, notes: str | None = None) -> PostureSession:
    row = PostureSession(
        user_id=user_id,
        started_at=datetime.now(timezone.utc),
        notes=notes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def stop(session: Session, session_id: int) -> PostureSession | None:
    row = session.get(PostureSession, session_id)
    if row is None:
        return None
    row.ended_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_recent(session: Session, limit: int = 20) -> list[PostureSession]:
    stmt = select(PostureSession).order_by(PostureSession.started_at.desc()).limit(limit)
    return list(session.exec(stmt))
