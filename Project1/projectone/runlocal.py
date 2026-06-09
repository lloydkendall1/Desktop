"""
Step 2 proof-of-life. Run on the machine with the camera attached:

    python run_local.py

It opens your webcam, runs MediaPipe pose, classifies each frame with your
trained model, and reports the verdict.

- If a desktop display is available it shows a live OpenCV window.
- If you're headless (e.g. the Pi over SSH, no monitor) it prints the verdict
  ~once a second and writes an annotated snapshot to debug/last_frame_<cam>.jpg
  so you can still see what the camera sees.

Quit: ESC or q in the window (GUI mode), or Ctrl+C (headless mode).
Force headless even on a desktop with:  RUN_LOCAL_HEADLESS=1 python run_local.py

Needs two files in backend/assets/ :
    - pose_landmarker_lite.task   (MediaPipe model from Google)
    - front_view.pkl              (your trained bundle)
"""

import os
import sys
import time

# Quieten the noisy MediaPipe / TensorFlow-Lite startup logging.
# (Must be set BEFORE importing cv2 / mediapipe.)
os.environ.setdefault("GLOG_minloglevel", "3")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import cv2

# Make the `services` package importable when running from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from services.alert_dispatcher import get_dispatcher  # noqa: E402
from services.camera_manager import CameraManager       # noqa: E402
from services.config import CAMERAS, POSE_TASK_MODEL     # noqa: E402
from services.pose_estimator import PoseEstimator        # noqa: E402
from services.posture_classifier import PostureClassifier  # noqa: E402
from services.runtime_state import state                 # noqa: E402

# Classes your DB marks as 'bad' — a buzz-worthy posture.
BAD_CLASSES = {"Forward Slouch", "Slump"}
DEBUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug")


def has_display() -> bool:
    """True if an OpenCV GUI window can actually be opened on this machine."""
    if os.environ.get("RUN_LOCAL_HEADLESS"):
        return False
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return True
    # Linux: a window needs an X or Wayland display.
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def main() -> None:
    if not os.path.exists(POSE_TASK_MODEL):
        print(f"Missing MediaPipe model: {POSE_TASK_MODEL}")
        print("Download pose_landmarker_lite.task into backend/assets/ first.")
        return

    gui = has_display()
    if gui:
        print("Display detected -> GUI mode. Press ESC or q in the window to quit.")
    else:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        print("No display detected -> HEADLESS mode.")
        print(f"  verdicts print below; snapshots -> {DEBUG_DIR}/last_frame_<cam>.jpg")
        print("  press Ctrl+C to stop.")

    cameras = CameraManager()
    estimator = PoseEstimator()
    dispatcher = get_dispatcher()

    classifiers = {}
    for name, cfg in CAMERAS.items():
        if os.path.exists(cfg["model"]):
            classifiers[name] = PostureClassifier(cfg["model"])
        else:
            print(f"[warn] no model for '{name}' at {cfg['model']} - frames show without a verdict.")

    last_report = 0.0  # throttles headless console/disk output
    try:
        while True:
            frames = cameras.read_all()
            tick = {}  # name -> (annotated_frame, label, conf)

            for name, frame in frames.items():
                if frame is None:
                    continue

                result = estimator.detect(frame)
                annotated = estimator.draw(frame, result)

                label, conf = ("no model", 0.0)
                if name in classifiers:
                    label, conf = classifiers[name].predict(result)
                    state.set_verdict(name, label, conf)
                    if label in BAD_CLASSES:
                        dispatcher.buzz(300)  # prints on laptop, real buzzer on Pi

                cv2.putText(
                    annotated, f"{name}: {label} ({conf:.0%})",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
                )
                tick[name] = (annotated, label, conf)

                if gui:
                    cv2.imshow(f"Slouch Punisher - {name}", annotated)

            if gui:
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):  # ESC or q
                    break
            else:
                now = time.time()
                if now - last_report >= 1.0:
                    for name, (annotated, label, conf) in tick.items():
                        print(f"  {name}: {label} ({conf:.0%})")
                        cv2.imwrite(os.path.join(DEBUG_DIR, f"last_frame_{name}.jpg"), annotated)
                    last_report = now
                time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        cameras.release_all()
        estimator.close()
        if gui:
            cv2.destroyAllWindows()
        print("\nstopped, camera released")


if __name__ == "__main__":
    main()
