"""
The /live endpoints. These are deliberately dumb: they only read what the
background LiveWorker last wrote into runtime_state. No camera access, no model
inference happens here — that all lives in the worker thread.
"""

from fastapi import APIRouter, Response

from services.config import CAMERAS
from services.runtime_state import state

router = APIRouter(prefix="/live", tags=["live"])


@router.get("/cameras")
def list_cameras():
    """Which cameras are configured."""
    return {"cameras": list(CAMERAS.keys())}


@router.get("/status")
def status():
    """Current verdict per camera, plus whether the worker loop is running."""
    verdicts = state.all_verdicts()
    return {
        "running": state.running,
        "verdicts": {
            name: {"label": label, "confidence": conf}
            for name, (label, conf) in verdicts.items()
        },
    }


@router.get("/frame/{camera}")
def frame(camera: str):
    """
    The latest annotated JPEG for one camera. Returns 204 (no content) if the
    worker hasn't produced a frame yet, so the frontend can just show a blank.
    """
    data = state.get_frame(camera)
    if data is None:
        return Response(status_code=204)
    return Response(content=data, media_type="image/jpeg")
