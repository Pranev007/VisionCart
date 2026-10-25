"""Phase 3: count detections, calculate prices, and export an invoice.

This module has no OpenCV or Streamlit dependency, so its logic can be tested
without a camera. Bills can be built from visible counts or a persistent cart.
"""

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Iterable, Mapping
from uuid import uuid4

from prices import CURRENCY


@dataclass(frozen=True)
class BillLine:
    name: str
    quantity: int
    unit_price: Decimal | None

    @property
    def line_total(self) -> Decimal | None:
        if self.unit_price is None:
            return None
        return self.unit_price * self.quantity


def count_visible_items(detections: Iterable[tuple[int | None, str]]) -> Counter:
    """Count each tracked ID once in this frame, never accumulate past frames.

    Untracked detections (ID None) count as individual current-frame boxes.
    """
    counts = Counter()
    seen_ids = set()
    for track_id, name in detections:
        if track_id is not None:
            if track_id in seen_ids:
                continue
            seen_ids.add(track_id)
        counts[name] += 1
    return counts


def build_bill(counts: Mapping[str, int], prices: Mapping[str, str | None]) -> list[BillLine]:
    """Price sale items; explicit None entries are non-billable detections.

    Unknown custom labels still appear as unpriced, preventing incomplete bills.
    """
    lines = []
    for name, quantity in sorted(counts.items()):
        if quantity <= 0:
            continue
        if name in prices and prices[name] is None:
            continue
        price = Decimal(str(prices[name])) if name in prices else None
        if price is not None:
            if not price.is_finite() or price < 0:
                raise ValueError(f"Invalid price for {name}: {prices[name]}")
            price = price.quantize(Decimal("0.01"))
        lines.append(BillLine(name, quantity, price))
    return lines


def grand_total(lines: list[BillLine]) -> Decimal:
    """Return a total only when every visible class has a configured price."""
    if any(line.unit_price is None for line in lines):
        raise ValueError("Set a price for every visible item before checkout.")
    return sum((line.line_total for line in lines), Decimal("0.00"))


def save_bill(lines: list[BillLine], output_dir: Path) -> tuple[Path, bytes]:
    """Save a new CSV, returning its path and exact bytes for browser download.

    The caller should clear the live cart only after this function succeeds.
    """
    if not lines:
        raise ValueError("The cart is empty. Place a priced item in view first.")
    total = grand_total(lines)
    issued_at = datetime.now(timezone(timedelta(hours=5, minutes=30), "IST"))
    bill_id = f"{issued_at:%Y%m%d_%H%M%S}_{uuid4().hex[:12]}"
    buffer = StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow([
        "Bill ID", "Issued At", "Currency", "Item Name", "Quantity",
        "Unit Price", "Line Total",
    ])
    for line in lines:
        writer.writerow([
            bill_id, issued_at.isoformat(timespec="seconds"), CURRENCY,
            line.name, line.quantity, f"{line.unit_price:.2f}",
            f"{line.line_total:.2f}",
        ])
    writer.writerow([
        bill_id, issued_at.isoformat(timespec="seconds"), CURRENCY,
        "GRAND TOTAL", "", "", f"{total:.2f}",
    ])
    data = buffer.getvalue().encode("utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"bill_{bill_id}.csv"
    # Exclusive creation protects an existing receipt from accidental overwrite.
    with path.open("xb") as receipt:
        receipt.write(data)
    return path, data
