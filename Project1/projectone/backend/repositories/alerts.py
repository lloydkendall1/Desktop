from datetime import datetime, timezone

from sqlmodel import Session, func, select

from models.alerts import Alert


def create(
    session: Session,
    session_id: int,
    alert_type: str,
    duration_ms: int | None = None,
    posture_reading_id: int | None = None,
) -> Alert:
    row = Alert(
        session_id=session_id,
        posture_reading_id=posture_reading_id,
        triggered_at=datetime.now(timezone.utc),
        alert_type=alert_type,
        duration_ms=duration_ms,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def count_for_session(session: Session, session_id: int) -> int:
    stmt = select(func.count()).select_from(Alert).where(Alert.session_id == session_id)
    return session.exec(stmt).one()
