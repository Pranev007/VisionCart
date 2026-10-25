"""ByteTrack adapter that exposes new IDs on their first detected frame."""

from types import SimpleNamespace

import numpy as np
from ultralytics.trackers.byte_tracker import BYTETracker


class CheckoutTracker(BYTETracker):
    """Use ByteTrack association, with immediate enrollment for checkout.

    Keep the detector confidence threshold rather than lowering it to add items
    sooner. The tradeoff is that a one-frame false positive can enter the cart.
    """

    def __init__(self, confidence: float):
        super().__init__(SimpleNamespace(
            track_high_thresh=confidence,
            track_low_thresh=min(0.1, confidence / 2),
            new_track_thresh=confidence,
            track_buffer=30,
            match_thresh=0.8,
            fuse_score=True,
        ))

    def update(self, results, img=None):
        super().update(results, img)
        current = []
        for track in self.tracked_stracks:
            # Never emit predictions for objects absent from the current frame.
            if track.frame_id != self.frame_id:
                continue
            track.is_activated = True
            current.append(track.result)
        # xyxy, tracking ID, confidence, class ID, source detection index.
        return np.asarray(current, dtype=np.float32).reshape(-1, 8)
