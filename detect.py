"""Phase 2: detect selected grocery classes in a local webcam feed."""

import argparse

import cv2
from ultralytics import YOLO

from camera import open_camera


DEFAULT_CLASSES = ["bottle", "cup", "apple"]


def resolve_class_ids(model: YOLO, class_names: list[str]) -> list[int] | None:
    """Look up labels in this model, so custom models can use different IDs."""
    name_to_id = {name.lower(): class_id for class_id, name in model.names.items()}
    requested = [name.strip().lower() for name in class_names]
    # None disables Ultralytics' class filter and includes every model class.
    if requested == ["all"]:
        return None
    missing = [name for name in requested if name not in name_to_id]
    if missing:
        raise ValueError(
            f"Classes absent from this model: {', '.join(missing)}. "
            f"Available classes: {', '.join(model.names.values())}. "
            "Use --classes with labels your model was trained to detect."
        )
    if not requested:
        raise ValueError("Select at least one class.")
    return [name_to_id[name] for name in requested]


def detect_frame(model: YOLO, frame, class_ids: list[int] | None, confidence: float):
    """Return one frame's Results object for drawing and future cart logic."""
    # OpenCV supplies a BGR NumPy image, which Ultralytics accepts directly.
    return model.predict(
        source=frame,
        classes=class_ids,
        conf=confidence,
        imgsz=640,
        verbose=False,
    )[0]


def run(
    model_path: str = "yolov8n.pt",
    camera_index: int = 0,
    class_names: list[str] | None = None,
    confidence: float = 0.5,
) -> None:
    if not 0 < confidence <= 1:
        raise ValueError("Confidence must be greater than 0 and at most 1.")

    # Load once, outside the loop. The default weights download on first use.
    model = YOLO(model_path)
    if model.task != "detect":
        raise ValueError("Use an object detection model, such as yolov8n.pt or best.pt.")
    class_ids = resolve_class_ids(
        model, DEFAULT_CLASSES if class_names is None else class_names
    )
    capture = open_camera(camera_index)
    window_name = "VisionCart - Grocery Detection (Q to quit)"
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        while True:
            success, frame = capture.read()
            if not success or frame is None:
                raise RuntimeError("Could not read a frame from the webcam.")

            result = detect_frame(model, frame, class_ids, confidence)
            # Draw the filtered boxes, class names, and confidence scores.
            annotated_frame = result.plot()
            cv2.imshow(window_name, annotated_frame)

            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="yolov8n.pt", help="Detection model weights")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index (default: 0)")
    parser.add_argument(
        "--classes", nargs="+", default=DEFAULT_CLASSES,
        help="Labels to display, or 'all' for every model class; quote multiword labels",
    )
    parser.add_argument("--confidence", type=float, default=0.5)
    args = parser.parse_args()
    try:
        run(args.model, args.camera, args.classes, args.confidence)
    except KeyboardInterrupt:
        pass
