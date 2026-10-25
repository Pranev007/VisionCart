"""Exercise Streamlit controls with a simulated camera; no hardware required."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from streamlit.testing.v1 import AppTest

from billing import save_bill


APP = Path(__file__).resolve().parents[1] / "app.py"


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    if app.exception:
        raise AssertionError(app.exception[0].message)


class AppTests(unittest.TestCase):
    def test_six_item_types_render_and_last_item_can_be_deleted(self):
        live = Mock()
        names = ["apple", "banana", "book", "bottle", "cup", "scissors"]
        live.read.return_value = (
            np.zeros((32, 32, 3), dtype=np.uint8), list(enumerate(names, start=1)),
        )
        with patch("live.LiveCheckout", return_value=live):
            app = AppTest.from_file(str(APP)).run(timeout=20)
            click(app, "Start camera")
            self.assertEqual(len(app.session_state["lines"]), 6)
            for name in names:
                self.assertTrue(any(button.label == f"Remove {name.title()}" for button in app.button))
            self.assertEqual(app.metric[0].value, "INR 300.00")
            click(app, "Remove Scissors")
            self.assertEqual(len(app.session_state["lines"]), 5)
            self.assertEqual(app.metric[0].value, "INR 250.00")
            click(app, "Stop camera")

    def test_navigation_and_settings_survive_page_changes(self):
        live = Mock()
        live.read.return_value = (np.zeros((32, 32, 3), dtype=np.uint8), [])
        with patch("live.LiveCheckout", return_value=live) as factory:
            app = AppTest.from_file(str(APP)).run(timeout=20)
            click(app, "Analytics")
            self.assertEqual(app.metric[0].label, "Completed checkouts")
            click(app, "History")
            click(app, "Settings")
            app.number_input[0].set_value(2)
            click(app, "Save settings")
            click(app, "Home")
            click(app, "Start camera")
            self.assertEqual(factory.call_args.args[1], 2)
            click(app, "Settings")
            live.close.assert_called_once()
            self.assertEqual(app.number_input[0].value, 2)

    def test_legacy_filter_can_switch_to_all_for_scissors(self):
        live = Mock()
        image = np.zeros((32, 32, 3), dtype=np.uint8)
        live.read.return_value = (image, [])
        with patch("live.LiveCheckout", return_value=live) as factory:
            app = AppTest.from_file(str(APP)).run(timeout=20)
            self.assertEqual(app.session_state["config"]["classes"], "all")
            app.session_state["config"] = {
                "camera": 1, "model": "yolov8n.pt", "confidence": .5,
                "classes": "bottle, cup, apple, banana, orange, book",
            }
            app.run()
            click(app, "Start camera")
            live.read.return_value = (image, [(1, "scissors")])
            click(app, "Detect all classes")
            self.assertEqual(factory.call_args.args[2], ["all"])
            self.assertEqual(app.session_state["lines"][0].name, "scissors")
            live.close.assert_called_once()
            click(app, "Stop camera")

    def test_live_bill_stop_checkout_and_new_transaction(self):
        live = Mock()
        live.read.return_value = (np.zeros((32, 32, 3), dtype=np.uint8), [(1, "apple"), (2, "apple"), (3, "bottle")])
        with tempfile.TemporaryDirectory() as directory:
            def export(lines, _output_dir):
                return save_bill(lines, Path(directory))

            with patch("live.LiveCheckout", return_value=live) as factory, patch("billing.save_bill", side_effect=export):
                app = AppTest.from_file(str(APP)).run(timeout=20)
                self.assertFalse(app.exception)
                click(app, "Start camera")
                self.assertEqual(factory.call_args.args[1], 1)
                self.assertEqual(app.metric[0].value, "INR 80.00")
                click(app, "Stop camera")
                live.close.assert_called_once()
                self.assertEqual(app.metric[0].value, "INR 80.00")
                click(app, "Checkout")
                self.assertEqual(app.metric[0].value, "INR 0.00")
                self.assertIsNone(app.session_state["frame"])
                self.assertEqual(len(list(Path(directory).glob("*.csv"))), 1)
                filename, data = app.session_state["receipt"]
                self.assertEqual((Path(directory) / filename).read_bytes(), data)
                self.assertFalse(app.session_state["cart"].seen_ids)
                live.read.return_value = (np.zeros((32, 32, 3), dtype=np.uint8), [])
                click(app, "Start camera")
                self.assertEqual(app.metric[0].value, "INR 0.00")
                click(app, "Stop camera")

    def test_failed_checkout_and_detection_errors_preserve_cart(self):
        live = Mock()
        live.read.return_value = (np.zeros((32, 32, 3), dtype=np.uint8), [(1, "apple")])
        with patch("live.LiveCheckout", return_value=live), patch("billing.save_bill", side_effect=OSError("disk unavailable")):
            app = AppTest.from_file(str(APP)).run(timeout=20)
            click(app, "Start camera")
            click(app, "Stop camera")
            click(app, "Checkout")
            self.assertEqual(app.metric[0].value, "INR 30.00")
            self.assertIn("disk unavailable", app.error[0].value)
            live.read.side_effect = RuntimeError("camera disconnected")
            click(app, "Start camera")
            self.assertIsNone(app.session_state["live"])
            self.assertEqual(app.metric[0].value, "INR 30.00")
            self.assertIn("camera disconnected", app.error[0].value)

    def test_unpriced_item_and_empty_cart_are_not_saved(self):
        live = Mock()
        live.read.return_value = (np.zeros((32, 32, 3), dtype=np.uint8), [(1, "custom_item")])
        with patch("live.LiveCheckout", return_value=live):
            app = AppTest.from_file(str(APP)).run(timeout=20)
            click(app, "Checkout")
            self.assertIn("cart is empty", app.error[0].value)
            click(app, "Start camera")
            self.assertEqual(app.metric[0].value, "Price needed")
            click(app, "Stop camera")
            click(app, "Checkout")
            self.assertIn("Set a price", app.error[0].value)
            self.assertEqual(len(app.session_state["lines"]), 1)

    def test_cart_survives_empty_frames_and_delete_does_not_readd_visible_item(self):
        live = Mock()
        image = np.zeros((32, 32, 3), dtype=np.uint8)
        live.read.return_value = (image, [(1, "scissors")])
        with patch("live.LiveCheckout", return_value=live):
            app = AppTest.from_file(str(APP)).run(timeout=20)
            click(app, "Start camera")
            self.assertEqual(app.metric[0].value, "INR 50.00")
            app.run()
            self.assertEqual(app.metric[0].value, "INR 50.00")
            live.read.return_value = (image, [])
            app.run()
            self.assertEqual(app.metric[0].value, "INR 50.00")
            live.read.return_value = (image, [(1, "scissors"), (2, "scissors")])
            app.run()
            self.assertEqual(app.metric[0].value, "INR 100.00")
            click(app, "Remove Scissors")
            self.assertEqual(app.metric[0].value, "INR 50.00")
            click(app, "Remove Scissors")
            self.assertEqual(app.metric[0].value, "INR 0.00")
            app.run()
            self.assertEqual(app.metric[0].value, "INR 0.00")
            live.read.return_value = (image, [(3, "scissors")])
            app.run()
            self.assertEqual(app.metric[0].value, "INR 50.00")
            click(app, "Settings")
            click(app, "Home")
            self.assertEqual(app.metric[0].value, "INR 50.00")


if __name__ == "__main__":
    unittest.main()
