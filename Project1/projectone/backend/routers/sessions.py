from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from repositories import sessions as sessions_repo
from repositories import users as users_repo
from services.runtime_state import state

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start")
def start_session(notes: str | None = None, db: Session = Depends(get_session)):
    """Begin recording. Creates a session row and flips the worker into logging mode."""
    user = users_repo.get_or_create_default(db)
    row = sessions_repo.start(db, user.id, notes)
    state.set_active_session(row.id)
    return {"id": row.id, "user_id": user.id, "started_at": row.started_at}


@router.post("/{session_id}/stop")
def stop_session(session_id: int, db: Session = Depends(get_session)):
    """End recording. Stamps ended_at and tells the worker to stop logging."""
    if state.active_session_id == session_id:
        state.set_active_session(None)
    row = sessions_repo.stop(db, session_id)
    if row is None:
        return {"error": "session not found", "id": session_id}
    return {"id": row.id, "ended_at": row.ended_at}


@router.get("")
def list_sessions(db: Session = Depends(get_session)):
    rows = sessions_repo.list_recent(db)
    return [
        {"id": r.id, "started_at": r.started_at, "ended_at": r.ended_at, "notes": r.notes}
        for r in rows
    ]


@router.get("/active")
def active_session():
    return {"active_session_id": state.active_session_id}
