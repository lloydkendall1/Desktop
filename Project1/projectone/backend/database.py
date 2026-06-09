import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlmodel import Session, create_engine

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "slouch_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "slouch_punisher")

DATABASE_URL = (
    f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    """FastAPI dependency: open a DB session for one request, close it after."""
    with Session(engine) as session:
        yield session


def check_db_connection() -> None:
    """
    Verify Postgres is reachable on startup.

    NOTE: the tables are created by init.sql inside the Postgres container
    (mounted into /docker-entrypoint-initdb.d/), NOT by SQLModel here.
    This function only confirms we can connect.
    """
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"[db] connected to '{POSTGRES_DB}' at {POSTGRES_HOST}:{POSTGRES_PORT}")
