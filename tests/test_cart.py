"""Persistent transaction-cart rules, independent of camera or UI."""

import unittest

from cart import PersistentCart


class CartTests(unittest.TestCase):
    def test_repeated_frames_and_absence_keep_one_item(self):
        cart = PersistentCart()
        cart.begin_scan()
        for _ in range(100):
            cart.observe([(1, "apple")])
        cart.observe([])
        self.assertEqual(cart.counts, {"apple": 1})
        cart.observe([(2, "apple")])
        self.assertEqual(cart.counts, {"apple": 2})

    def test_delete_one_unit_tombstones_ids_but_allows_new_tracks(self):
        cart = PersistentCart()
        cart.begin_scan()
        visible = [(1, "apple"), (2, "apple")]
        cart.observe(visible)
        cart.remove_one("apple")
        cart.observe(visible)
        self.assertEqual(cart.counts, {"apple": 1})
        cart.remove_one("apple")
        cart.observe(visible)
        self.assertEqual(cart.counts, {})
        cart.observe([(3, "apple")])
        self.assertEqual(cart.counts, {"apple": 1})

    def test_class_changes_untracked_boxes_and_new_scan_ids(self):
        cart = PersistentCart()
        cart.begin_scan()
        cart.observe([(None, "apple")])
        self.assertEqual(cart.counts, {})
        cart.observe([(1, "apple"), (1, "apple")])
        cart.observe([(1, "orange")])
        self.assertEqual(cart.counts, {"apple": 1})
        cart.begin_scan()
        cart.observe([(1, "orange")])
        self.assertEqual(cart.counts, {"apple": 1, "orange": 1})

    def test_checkout_clear_starts_a_fresh_transaction(self):
        cart = PersistentCart()
        cart.begin_scan()
        cart.observe([(1, "apple")])
        cart.clear()
        self.assertFalse(cart.counts)
        self.assertFalse(cart.seen_ids)
        cart.begin_scan()
        cart.observe([(1, "apple")])
        self.assertEqual(cart.counts, {"apple": 1})


if __name__ == "__main__":
    unittest.main()
