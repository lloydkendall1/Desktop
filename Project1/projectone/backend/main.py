import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import check_db_connection
from routers.live import router as live_router
from routers.readings import router as readings_router
from routers.sessions import router as sessions_router
from services.live_worker import worker

STUDENT_NAME = os.getenv("STUDENT_NAME", "Lloyd")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        check_db_connection()
    except Exception as exc:  # noqa: BLE001
        print(f"[db] WARNING: could not connect to Postgres: {exc}")
        print("[db] Is the Docker container running? Start it before the backend.")
    worker.start()
    yield
    worker.stop()


app = FastAPI(title=f"Slouch Punisher API - {STUDENT_NAME}", lifespan=lifespan)

app.include_router(live_router)
app.include_router(sessions_router)
app.include_router(readings_router)


@app.get("/")
def root():
    return {"message": "Slouch Punisher API is running.", "student_name": STUDENT_NAME}


@app.get("/health")
def health():
    return {"status": "ok"}
