from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from repositories import alerts as alerts_repo
from repositories import posture_classes as pc_repo
from repositories import posture_readings as pr_repo

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/session/{session_id}")
def session_summary(session_id: int, db: Session = Depends(get_session)):
    """Per-class reading counts + alert count for one session (feeds the Stats tab)."""
    id_map = pc_repo.id_to_class_map(db)
    by_class = []
    total = 0
    for class_id, count in pr_repo.class_counts(db, session_id):
        pc = id_map.get(class_id)
        by_class.append(
            {
                "name": pc.name if pc else str(class_id),
                "severity": pc.severity if pc else "?",
                "count": count,
            }
        )
        total += count
    by_class.sort(key=lambda x: x["count"], reverse=True)
    return {
        "session_id": session_id,
        "total_readings": total,
        "alerts": alerts_repo.count_for_session(db, session_id),
        "by_class": by_class,
    }
