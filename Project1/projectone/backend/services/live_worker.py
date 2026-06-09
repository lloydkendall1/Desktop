"""
The live capture + inference loop, as a background thread for the backend.

Same logic as run_local.py, but instead of showing a window it:
  - encodes each annotated frame to JPEG and stores it in runtime_state
  - stores the (label, confidence) verdict in runtime_state
  - fires the buzzer on a 'bad' posture (with a cooldown so it doesn't spam)

The FastAPI app starts this on startup and stops it on shutdown. The API's
/live endpoints just read whatever this thread last wrote — they never touch
the camera or the model themselves.
"""

import os
import threading
import time

import cv2

from services.alert_dispatcher import get_dispatcher
from services.camera_manager import CameraManager
from services.config import CAMERAS, POSE_TASK_MODEL
from services.pose_estimator import PoseEstimator
from services.posture_classifier import PostureClassifier
from services.runtime_state import state

# Postures worth buzzing about. Tolerates both naming styles for now; the
# model-name -> DB-name mapping gets tidied up at step 4.
BAD_CLASSES = {"Forward Slouch", "Slump", "forward_slouch", "slump"}

BUZZ_COOLDOWN_S = 3.0   # don't re-buzz the same camera more often than this
FRAME_INTERVAL_S = 0.04  # ~25 fps cap per loop


class LiveWorker:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_buzz: dict[str, float] = {}

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        # NOTE: everything that touches MediaPipe is created and used inside
        # this thread, which is what the Tasks API expects.
        if not os.path.exists(POSE_TASK_MODEL):
            print(f"[live] Missing MediaPipe model: {POSE_TASK_MODEL} - worker not started.")
            return

        cameras = CameraManager()
        estimator = PoseEstimator()
        dispatcher = get_dispatcher()

        classifiers: dict[str, PostureClassifier] = {}
        for name, cfg in CAMERAS.items():
            if os.path.exists(cfg["model"]):
                classifiers[name] = PostureClassifier(cfg["model"])
            else:
                print(f"[live] no model for '{name}' at {cfg['model']} - streaming without a verdict.")

        state.running = True
        print("[live] worker started.")
        try:
            while not self._stop.is_set():
                frames = cameras.read_all()
                for name, frame in frames.items():
                    if frame is None:
                        continue

                    result = estimator.detect(frame)
                    annotated = estimator.draw(frame, result)

                    label, conf = ("no model", 0.0)
                    if name in classifiers:
                        label, conf = classifiers[name].predict(result)
                        if label in BAD_CLASSES:
                            self._maybe_buzz(dispatcher, name)

                    cv2.putText(
                        annotated, f"{label} ({conf:.0%})",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
                    )

                    ok, buf = cv2.imencode(".jpg", annotated)
                    if ok:
                        state.set_frame(name, buf.tobytes())
                    state.set_verdict(name, label, conf)

                time.sleep(FRAME_INTERVAL_S)
        finally:
            state.running = False
            cameras.release_all()
            estimator.close()
            print("[live] worker stopped, cameras released.")

    def _maybe_buzz(self, dispatcher, camera: str) -> None:
        now = time.time()
        if now - self._last_buzz.get(camera, 0.0) >= BUZZ_COOLDOWN_S:
            dispatcher.buzz(300)
            self._last_buzz[camera] = now


# Module-level singleton the app starts/stops.
worker = LiveWorker()
