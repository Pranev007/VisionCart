"""One session's YOLO tracker and webcam, independent of the UI."""

import numpy as np
from ultralytics import YOLO

from camera import open_camera
from detect import resolve_class_ids
from tracking import CheckoutTracker


class LiveCheckout:
    def __init__(self, model_path: str, camera_index: int,
                 classes: list[str], confidence: float, image_size: int = 480):
        self.capture = None
        self.model = YOLO(model_path)
        if self.model.task != "detect":
            raise ValueError("Please select an object detection model.")
        self.class_ids = resolve_class_ids(self.model, classes)
        self.confidence = confidence
        self.image_size = image_size
        self.tracker = CheckoutTracker(confidence)
        # Pay model/predictor initialization cost during Start, before live scans.
        self.model.predict(
            source=np.zeros((480, 640, 3), dtype=np.uint8),
            classes=self.class_ids, conf=confidence, imgsz=image_size, verbose=False,
        )
        self.capture = open_camera(camera_index)

    def read(self):
        """Return an annotated BGR frame and (tracking ID, class name) pairs."""
        success, frame = self.capture.read()
        if not success or frame is None:
            raise RuntimeError("Could not read the webcam. Check its connection and restart.")
        result = self.model.predict(
            source=frame,
            classes=self.class_ids, conf=self.confidence, imgsz=self.image_size,
            verbose=False,
        )[0]
        detections = []
        boxes = result.boxes
        if boxes is not None:
            tracks = self.tracker.update(boxes.cpu().numpy(), frame)
            detections = [
                (int(track[4]), result.names[int(track[6])])
                for track in tracks
            ]
        return result.plot(), detections

    def close(self):
        """Idempotent cleanup for Stop, Checkout, and inference errors."""
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def __del__(self):
        # Best-effort cleanup if Streamlit discards a disconnected session.
        self.close()
