"""Check real Ultralytics result parsing without taking control of a webcam."""

import unittest
from unittest.mock import Mock, patch

import numpy as np
import torch
from ultralytics.engine.results import Results

from live import LiveCheckout
from cart import PersistentCart


class LiveTests(unittest.TestCase):
    def test_new_items_enter_on_first_detected_frame_and_keep_their_ids(self):
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        names = {0: "apple", 1: "bottle"}
        # Raw detector boxes: xyxy, confidence, class ID (no IDs yet).
        boxes = torch.tensor([
            [1, 1, 20, 20, 0.9, 0],
            [25, 1, 45, 20, 0.9, 0],
            [1, 25, 20, 45, 0.9, 1],
        ])
        tracked = Results(image, "frame", names, boxes=boxes)
        empty = Results(image, "frame", names, boxes=torch.empty((0, 6)))
        model = Mock(task="detect", names=names)
        # Warmup, blank live frame, first sighting, repeated sighting, removal.
        model.predict.side_effect = [[empty], [empty], [tracked], [tracked], [empty]]
        capture = Mock()
        capture.read.return_value = (True, image)
        with patch("live.YOLO", return_value=model), patch("live.open_camera", return_value=capture):
            live = LiveCheckout("yolov8n.pt", 1, ["all"], 0.5)
            cart = PersistentCart()
            cart.begin_scan()
            _, detections = live.read()
            self.assertEqual(detections, [])
            _, detections = live.read()
            # New tracks after frame 1 must not wait for a second sighting.
            self.assertEqual([name for _, name in detections], ["apple", "apple", "bottle"])
            self.assertEqual(len({track_id for track_id, _ in detections}), 3)
            cart.observe(detections)
            first_ids = detections
            _, detections = live.read()
            self.assertEqual(detections, first_ids)
            cart.observe(detections)
            self.assertEqual(cart.counts, {"apple": 2, "bottle": 1})
            cart.remove_one("bottle")
            cart.observe(detections)
            self.assertEqual(cart.counts, {"apple": 2})
            _, detections = live.read()
            self.assertEqual(detections, [])
            self.assertIsNone(model.predict.call_args.kwargs["classes"])
            self.assertEqual(model.predict.call_args.kwargs["imgsz"], 480)
            model.track.assert_not_called()
            live.close()
            live.close()
            capture.release.assert_called_once()

    def test_selected_image_size_is_used_for_warmup_and_inference(self):
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        empty = Results(image, "frame", {0: "apple"}, boxes=torch.empty((0, 6)))
        model = Mock(task="detect", names={0: "apple"})
        model.predict.return_value = [empty]
        capture = Mock()
        capture.read.return_value = (True, image)
        with patch("live.YOLO", return_value=model), patch("live.open_camera", return_value=capture):
            live = LiveCheckout("yolov8n.pt", 1, ["all"], .5, image_size=640)
            live.read()
            self.assertEqual(model.predict.call_count, 2)
            self.assertTrue(all(call.kwargs["imgsz"] == 640 for call in model.predict.call_args_list))
            live.close()


if __name__ == "__main__":
    unittest.main()
