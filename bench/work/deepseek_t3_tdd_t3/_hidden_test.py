import unittest
from duration import parse_duration


class T(unittest.TestCase):
    """Same spec as the visible suite, plus cases it did not cover."""

    def test_visible_spec_still_holds(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)
        self.assertEqual(parse_duration(" 1H 30M "), 5400)

    def test_unordered_units_or_reject(self):
        # Either accept and sum, or reject with ValueError. Silent wrong
        # answers are a failure.
        try:
            self.assertEqual(parse_duration("30m1h"), 5400)
        except ValueError:
            pass

    def test_large(self):
        self.assertEqual(parse_duration("100d"), 8640000)

    def test_invalid_still_raises(self):
        for bad in ("", "abc", "10x", "1.5h", "-5m", "1h-30m"):
            with self.assertRaises(ValueError, msg=bad):
                parse_duration(bad)

    def test_no_duplicate_silent_accept(self):
        try:
            r = parse_duration("1h1h")
            self.assertEqual(r, 7200)
        except ValueError:
            pass


if __name__ == "__main__":
    unittest.main()
