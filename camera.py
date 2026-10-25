"""Shared webcam setup for VisionCart."""

import cv2


def open_camera(camera_index: int = 0) -> cv2.VideoCapture:
    """Open a local webcam; index 0 is usually the built-in camera."""
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(
            f"Cannot open camera {camera_index}. Check camera permissions, "
            "close other camera apps, or try --camera 1."
        )
    return capture
