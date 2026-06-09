"""
Opens the webcam(s) and hands out frames. On the laptop that's one camera;
on the Pi it's two (front + side). The rest of the system addresses cameras
by name ("front", "side"), so adding the second camera is a config change in
config.CAMERAS, not a code change here.
"""

import cv2

from services.config import CAMERAS


class Camera:
    def __init__(self, name: str, index: int):
        self.name = name
        self.index = index
        self.cap = cv2.VideoCapture(index)

    def is_open(self) -> bool:
        return self.cap is not None and self.cap.isOpened()

    def read(self):
        """Return a BGR frame, or None if the grab failed."""
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()


class CameraManager:
    def __init__(self, cameras: dict | None = None):
        cameras = cameras if cameras is not None else CAMERAS
        self.cameras: dict[str, Camera] = {}
        for name, cfg in cameras.items():
            cam = Camera(name, cfg["index"])
            if not cam.is_open():
                print(f"[camera] WARNING: '{name}' (index {cfg['index']}) did not open.")
            self.cameras[name] = cam

    def read_all(self) -> dict:
        """{name: BGR frame or None} for every configured camera."""
        return {name: cam.read() for name, cam in self.cameras.items()}

    def release_all(self) -> None:
        for cam in self.cameras.values():
            cam.release()
