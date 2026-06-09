"""
Central config for the services layer: where the model files live, the
per-camera mapping, and runtime thresholds. Everything is overridable via
environment variables so the Pi and the laptop can differ without code changes.
"""

import os

# backend/services/config.py  ->  backend/
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.getenv("ASSETS_DIR", os.path.join(BACKEND_DIR, "assets"))

# The MediaPipe Pose Landmarker .task file (downloaded from Google, ~29 MB).
POSE_TASK_MODEL = os.getenv(
    "POSE_TASK_MODEL", os.path.join(ASSETS_DIR, "pose_landmarker_lite.task")
)

# One entry per camera: which webcam index it is and which trained
# classifier (.pkl bundle) interprets its view. Add "side" once that model
# exists; the rest of the code already loops over whatever is defined here.
CAMERAS = {
    "front": {
        "index": int(os.getenv("FRONT_CAM_INDEX", "0")),
        "model": os.getenv("FRONT_MODEL", os.path.join(ASSETS_DIR, "front_view.pkl")),
    },
    "side": {
        "index": int(os.getenv("SIDE_CAM_INDEX", "2")),
        "model": os.getenv("SIDE_MODEL", os.path.join(ASSETS_DIR, "side_view.pkl")),
    },
}

# Below this probability the classifier says "uncertain" instead of guessing.
# (This is the MIN_PROB from your validation notebook. The Settings tab will
# let the user raise it to make the device stricter.)
MIN_PROB = float(os.getenv("MIN_PROB", "0.4"))

# Returned when MediaPipe finds no person in frame. Matches the "Not There"
# row seeded in init.sql, so it slots straight into the database later.
NO_POSE_LABEL = "Not There"
UNCERTAIN_LABEL = "uncertain"
