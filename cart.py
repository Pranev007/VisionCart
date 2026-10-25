"""A transaction cart that remembers scanned tracker IDs after items disappear."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class PersistentCart:
    counts: Counter = field(default_factory=Counter)
    seen_ids: set[tuple[int, int]] = field(default_factory=set)
    scan_number: int = 0

    def begin_scan(self):
        # A new model/camera session can reuse tracker IDs from an older session.
        self.scan_number += 1

    def observe(self, detections: Iterable[tuple[int | None, str]]):
        """Add each new confirmed track once, retaining items absent later.

        Wait for an ID instead of counting untracked boxes on every frame.
        """
        for track_id, name in detections:
            if track_id is None:
                continue
            key = (self.scan_number, track_id)
            if key not in self.seen_ids:
                self.seen_ids.add(key)
                self.counts[name] += 1

    def remove_one(self, name: str):
        """Remove one unit without letting the same visible ID add it back."""
        if self.counts[name] > 1:
            self.counts[name] -= 1
        else:
            self.counts.pop(name, None)
        # Deliberately retain seen_ids as tombstones for manually removed items.

    def clear(self):
        self.counts.clear()
        self.seen_ids.clear()
        self.scan_number = 0
