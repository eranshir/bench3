import unittest
from stats import percentile


class T(unittest.TestCase):
    def test_documented_cases(self):
        self.assertEqual(percentile([1, 2, 3, 4], 50), 2)
        self.assertEqual(percentile([1, 2, 3, 4], 100), 4)
        self.assertEqual(percentile([1, 2, 3, 4], 0), 1)

    def test_unsorted_input(self):
        self.assertEqual(percentile([4, 1, 3, 2], 50), 2)

    def test_single(self):
        self.assertEqual(percentile([7], 50), 7)
        self.assertEqual(percentile([7], 100), 7)

    def test_nearest_rank_semantics(self):
        d = list(range(1, 11))  # 1..10
        self.assertEqual(percentile(d, 10), 1)
        self.assertEqual(percentile(d, 90), 9)

    def test_empty_still_raises(self):
        with self.assertRaises(ValueError):
            percentile([], 50)


if __name__ == "__main__":
    unittest.main()
