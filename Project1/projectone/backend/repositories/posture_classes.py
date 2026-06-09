from sqlmodel import Session, select

from models.posture_classes import PostureClass


def name_to_class_map(session: Session) -> dict[str, PostureClass]:
    """{'Forward Slouch': PostureClass(...), ...} keyed by DB name."""
    return {row.name: row for row in session.exec(select(PostureClass)).all()}


def id_to_class_map(session: Session) -> dict[int, PostureClass]:
    """{1: PostureClass(...), ...} keyed by id (for summaries)."""
    return {row.id: row for row in session.exec(select(PostureClass)).all()}
