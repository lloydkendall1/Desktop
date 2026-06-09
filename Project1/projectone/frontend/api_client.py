import os
from io import BytesIO

import httpx
from PIL import Image

API_BASE = os.getenv("SLOUCH_API_BASE_URL", "http://127.0.0.1:8000")


def get_backend_status() -> str:
    """Ping the backend root so the UI can show whether the API is up."""
    try:
        response = httpx.get(f"{API_BASE}/", timeout=5)
        response.raise_for_status()
        data = response.json()
        return f"Connected to backend - {data.get('message', '')}"
    except httpx.HTTPError as exc:
        return f"Backend NOT reachable at {API_BASE} ({exc})"


def get_cameras() -> list[str]:
    try:
        response = httpx.get(f"{API_BASE}/live/cameras", timeout=5)
        response.raise_for_status()
        return response.json().get("cameras", [])
    except httpx.HTTPError:
        return []


def get_live_frame(camera: str):
    """Return the latest annotated frame for a camera as a PIL image (or None)."""
    try:
        response = httpx.get(f"{API_BASE}/live/frame/{camera}", timeout=5)
        if response.status_code == 204:
            return None
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except httpx.HTTPError:
        return None


def get_live_status() -> dict:
    """Return {'running': bool, 'verdicts': {camera: {label, confidence}}}."""
    try:
        response = httpx.get(f"{API_BASE}/live/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return {"running": False, "verdicts": {}}
