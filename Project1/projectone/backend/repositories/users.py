from datetime import datetime, timezone

from sqlmodel import Session, select

from models.users import User

DEFAULT_USERNAME = "lloyd"


def get_or_create_default(session: Session) -> User:
    """For a single-user device: reuse one fixed user, creating it on first run."""
    user = session.exec(select(User).where(User.username == DEFAULT_USERNAME)).first()
    if user is not None:
        return user
    user = User(username=DEFAULT_USERNAME, created_at=datetime.now(timezone.utc))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
