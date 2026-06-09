"""
The single in-memory object that the live loop writes to and (in step 3) the
API reads from. Built thread-safe now so step 3 is trivial: a background thread
captures + classifies and calls set_frame/set_verdict, while FastAPI request
handlers call get_frame/get_verdict.

In step 2 we only exercise the write side from run_local.py.
"""

import threading

from services.config import MIN_PROB


class RuntimeState:
    def __init__(self):
        self._lock = threading.Lock()
        self._frames: dict[str, bytes] = {}            # camera name -> latest JPEG bytes
        self._verdicts: dict[str, tuple[str, float]] = {}  # camera name -> (label, confidence)
        self.min_prob: float = MIN_PROB                # live strictness (Settings tab edits this)
        self.running: bool = False                     # is a capture session active?

    # --- frames ---
    def set_frame(self, camera: str, jpeg_bytes: bytes) -> None:
        with self._lock:
            self._frames[camera] = jpeg_bytes

    def get_frame(self, camera: str) -> bytes | None:
        with self._lock:
            return self._frames.get(camera)

    # --- verdicts ---
    def set_verdict(self, camera: str, label: str, confidence: float) -> None:
        with self._lock:
            self._verdicts[camera] = (label, confidence)

    def get_verdict(self, camera: str) -> tuple[str, float] | None:
        with self._lock:
            return self._verdicts.get(camera)

    def all_verdicts(self) -> dict:
        with self._lock:
            return dict(self._verdicts)


# Module-level singleton — import this everywhere.
state = RuntimeState()
