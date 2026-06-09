"""
Thin wrapper around MediaPipe's Pose Landmarker (Tasks API).

Mirrors what your validation notebook's live loop actually did: RunningMode.IMAGE
plus landmarker.detect() per frame. That treats each frame independently (no
temporal smoothing), which is simple and is the path you already confirmed works.
If you later want smoother tracking you can switch to RunningMode.VIDEO with
detect_for_video(timestamp_ms) — but that's an optimisation, not needed now.
"""

import cv2
import numpy as np
from mediapipe import Image, ImageFormat
from mediapipe.tasks.python.core import base_options as bo
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)

from services.config import POSE_TASK_MODEL


class PoseEstimator:
    def __init__(self, model_path: str = POSE_TASK_MODEL):
        options = PoseLandmarkerOptions(
            base_options=bo.BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        self.landmarker = PoseLandmarker.create_from_options(options)

    def detect(self, frame_bgr: np.ndarray):
        """Run pose detection on a BGR frame (as cv2 gives it). Returns the result."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_img = Image(image_format=ImageFormat.SRGB, data=rgb)
        return self.landmarker.detect(mp_img)

    @staticmethod
    def draw(frame_bgr: np.ndarray, result) -> np.ndarray:
        """
        Draw the detected landmarks onto the BGR frame (in place) and return it.
        Simple circles, like your notebook's live loop — no fragile drawing_utils
        import. Coordinates are normalised, so they scale to the frame size.
        """
        if not result.pose_landmarks:
            return frame_bgr
        h, w = frame_bgr.shape[:2]
        for lm in result.pose_landmarks[0]:
            cv2.circle(frame_bgr, (int(lm.x * w), int(lm.y * h)), 4, (0, 255, 0), -1)
        return frame_bgr

    def close(self) -> None:
        self.landmarker.close()
