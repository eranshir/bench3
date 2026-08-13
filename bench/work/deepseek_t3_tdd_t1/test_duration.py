import unittest
from duration import parse_duration


class T(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_duration("30s"), 30)
        self.assertEqual(parse_duration("5m"), 300)
        self.assertEqual(parse_duration("2h"), 7200)
        self.assertEqual(parse_duration("1d"), 86400)

    def test_compound(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("1d2h3m4s"), 93784)

    def test_whitespace_and_case(self):
        self.assertEqual(parse_duration(" 1H 30M "), 5400)

    def test_zero(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_invalid(self):
        for bad in ("", "abc", "10x", "h30m", "1.5h", "-5m"):
            with self.assertRaises(ValueError, msg=bad):
                parse_duration(bad)


if __name__ == "__main__":
    unittest.main()
