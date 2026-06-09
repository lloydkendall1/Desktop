"""
Feature extraction — shared by BOTH training and runtime.

This is a direct port of the logic in Front_view.ipynb (angle_between,
ANGLE_DEFS, extract_features) with one deliberate improvement:

    The notebook rebuilt the feature column order at runtime by reading the
    training CSV back from disk (`feat_ord = pd.read_csv(...).columns`).
    That couples the device to a CSV file. Here, `feature_names()` reproduces
    that exact order in code, so the runtime needs only the .pkl model, not
    the CSV. The order is identical to the notebook's dict-insertion order,
    so a scaler/model trained by the notebook still lines up positionally.

Keep this module the single source of truth: if you ever change the angles,
retrain with the same code so training and inference never drift apart.
"""

import math

import numpy as np

LANDMARK_COUNT = 33  # MediaPipe Pose Landmarker (full body)

# (column_name, index_A, index_B_vertex, index_C) — vertex is the joint.
# Indices match the 33-landmark model.
ANGLE_DEFS = [
    ("angle_left_elbow", 11, 13, 15),     # shoulder -> elbow -> wrist
    ("angle_right_elbow", 12, 14, 16),
    ("angle_left_shoulder", 13, 11, 23),  # elbow -> shoulder -> hip
    ("angle_right_shoulder", 14, 12, 24),
    ("angle_left_hip", 11, 23, 25),       # shoulder -> hip -> knee
    ("angle_right_hip", 12, 24, 26),
    ("angle_left_knee", 23, 25, 27),      # hip -> knee -> ankle
    ("angle_right_knee", 24, 26, 28),
]


def angle_between(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle in degrees at joint B, formed by vectors B->A and B->C (x,y only)."""
    ba = a[:2] - b[:2]
    bc = c[:2] - b[:2]
    cos_a = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return math.degrees(math.acos(np.clip(cos_a, -1.0, 1.0)))


def feature_names() -> list[str]:
    """
    The exact column order the model/scaler were trained on:
    lm0_x, lm0_y, lm0_z, lm0_vis, lm1_x, ... lm32_vis, then the 8 angles.
    33 * 4 + 8 = 140 features.
    """
    names: list[str] = []
    for i in range(LANDMARK_COUNT):
        names += [f"lm{i}_x", f"lm{i}_y", f"lm{i}_z", f"lm{i}_vis"]
    names += [name for name, *_ in ANGLE_DEFS]
    return names


def landmarks_to_features(landmarks) -> dict:
    """
    Build the 140-feature dict from one person's landmark list.
    `landmarks` is a list of objects with .x, .y, .z, .visibility
    (exactly what result.pose_landmarks[0] gives you).
    """
    row: dict[str, float] = {}
    for i, lm in enumerate(landmarks):
        row[f"lm{i}_x"] = lm.x
        row[f"lm{i}_y"] = lm.y
        row[f"lm{i}_z"] = lm.z
        row[f"lm{i}_vis"] = lm.visibility

    coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])
    for feat_name, ia, ib, ic in ANGLE_DEFS:
        row[feat_name] = angle_between(coords[ia], coords[ib], coords[ic])
    return row


def result_to_feature_vector(result) -> np.ndarray | None:
    """
    Turn a MediaPipe PoseLandmarkerResult into a (1, 140) array ready for
    scaler.transform(...). Returns None if no pose was detected.
    """
    if not result.pose_landmarks:
        return None
    row = landmarks_to_features(result.pose_landmarks[0])
    return np.array([[row[name] for name in feature_names()]])
