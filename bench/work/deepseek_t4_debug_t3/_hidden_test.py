import unittest
from cart import Cart


class T(unittest.TestCase):
    def test_no_shared_state(self):
        a = Cart()
        a.add("w", 10.0)
        self.assertEqual(Cart().items, [])

    def test_compounding_discount(self):
        c = Cart().add("t", 100.0)
        c.apply_discount(10)
        c.apply_discount(10)
        self.assertAlmostEqual(c.total(), 81.0, places=2)

    def test_subtotal_preserved(self):
        c = Cart().add("t", 100.0)
        c.apply_discount(10)
        self.assertAlmostEqual(c.subtotal(), 100.0, places=2)

    def test_qty(self):
        c = Cart().add("t", 10.0, qty=3)
        self.assertAlmostEqual(c.total(), 30.0, places=2)

    def test_rounding(self):
        c = Cart().add("t", 10.0, qty=3)
        c.apply_discount(33)
        self.assertEqual(round(c.total(), 2), c.total())

    def test_chaining_preserved(self):
        self.assertIsInstance(Cart().add("a", 1.0).apply_discount(0), Cart)


if __name__ == "__main__":
    unittest.main()
