from datetime import datetime, timezone

from sqlmodel import Session, func, select

from models.posture_readings import PostureReading


def create(
    session: Session,
    session_id: int,
    posture_class_id: int,
    confidence: float,
    spine_angle: float | None = None,
    head_angle: float | None = None,
) -> PostureReading:
    row = PostureReading(
        session_id=session_id,
        posture_class_id=posture_class_id,
        recorded_at=datetime.now(timezone.utc),
        confidence=confidence,
        spine_angle=spine_angle,
        head_angle=head_angle,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def class_counts(session: Session, session_id: int) -> list[tuple[int, int]]:
    """[(posture_class_id, count), ...] for one session."""
    stmt = (
        select(PostureReading.posture_class_id, func.count())
        .where(PostureReading.session_id == session_id)
        .group_by(PostureReading.posture_class_id)
    )
    return list(session.exec(stmt))
