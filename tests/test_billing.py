"""Billing behavior checks: run with python -m unittest discover -s tests -v."""

import csv
import io
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from billing import build_bill, count_visible_items, grand_total, save_bill
from prices import ITEM_PRICES


class BillingTests(unittest.TestCase):
    def test_non_billable_detections_do_not_block_scissors_checkout(self):
        lines = build_bill({"person": 1, "dog": 1, "scissors": 2}, ITEM_PRICES)
        self.assertEqual([line.name for line in lines], ["scissors"])
        self.assertEqual(grand_total(lines), Decimal("100.00"))
        self.assertEqual(build_bill({"person": 1}, ITEM_PRICES), [])

    def test_counts_are_unique_in_current_frame_and_do_not_accumulate(self):
        visible = [(1, "apple"), (1, "apple"), (2, "apple"), (3, "bottle")]
        self.assertEqual(count_visible_items(visible), {"apple": 2, "bottle": 1})
        self.assertEqual(count_visible_items(visible), {"apple": 2, "bottle": 1})
        self.assertEqual(count_visible_items([(2, "apple")]), {"apple": 1})
        self.assertEqual(count_visible_items([]), {})

    def test_untracked_boxes_count_as_separate_items(self):
        self.assertEqual(count_visible_items([(None, "apple")] * 2), {"apple": 2})

    def test_decimal_totals_and_missing_prices(self):
        lines = build_bill({"apple": 3, "bottle": 1}, {"apple": "0.10", "bottle": "0.20"})
        self.assertEqual(grand_total(lines), Decimal("0.50"))
        self.assertEqual(grand_total([]), Decimal("0.00"))
        unpriced = build_bill({"pen": 1}, {})
        self.assertIsNone(unpriced[0].unit_price)
        with self.assertRaises(ValueError):
            grand_total(unpriced)

    def test_csv_matches_bill_and_receipts_have_unique_names(self):
        lines = build_bill({"apple": 2, "bottle": 1}, {"apple": "30", "bottle": "20"})
        with tempfile.TemporaryDirectory() as directory:
            path, data = save_bill(lines, Path(directory))
            self.assertEqual(path.read_bytes(), data)
            rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
            self.assertEqual(rows[0]["Quantity"], "2")
            self.assertEqual(rows[0]["Line Total"], "60.00")
            self.assertEqual(rows[-1]["Line Total"], "80.00")
            self.assertEqual(rows[-1]["Currency"], "INR")
            self.assertTrue(rows[-1]["Issued At"].endswith("+05:30"))
            second_path, _ = save_bill(lines, Path(directory))
            self.assertNotEqual(path, second_path)

    def test_incomplete_or_empty_bills_do_not_create_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipts"
            for lines in ([], build_bill({"pen": 1}, {})):
                with self.assertRaises(ValueError):
                    save_bill(lines, output)
            self.assertFalse(output.exists())

    def test_invalid_prices_and_write_failure(self):
        for price in ("-1", "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                build_bill({"apple": 1}, {"apple": price})
        lines = build_bill({"apple": 1}, {"apple": "30"})
        with tempfile.TemporaryDirectory() as directory:
            invalid_dir = Path(directory) / "file"
            invalid_dir.write_text("not a folder")
            with self.assertRaises(OSError):
                save_bill(lines, invalid_dir)
        self.assertEqual(grand_total(lines), Decimal("30.00"))


if __name__ == "__main__":
    unittest.main()
