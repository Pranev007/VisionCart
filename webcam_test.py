"""Phase 1: display the webcam without running object detection."""

import argparse

import cv2

from camera import open_camera


def run(camera_index: int = 0) -> None:
    capture = open_camera(camera_index)
    window_name = "VisionCart - Webcam Test (Q to quit)"
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        while True:
            success, frame = capture.read()
            if not success or frame is None:
                raise RuntimeError("Could not read a frame from the webcam.")

            cv2.imshow(window_name, frame)
            # waitKey also lets OpenCV process window events.
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        # Release the webcam even if a frame read or display fails.
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, default=0, help="Webcam index (default: 0)")
    args = parser.parse_args()
    try:
        run(args.camera)
    except KeyboardInterrupt:
        pass
