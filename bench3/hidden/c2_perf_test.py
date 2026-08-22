import random
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from analytics import rolling_median, window_distinct_counts


def brute_median(v, w):
    out = []
    for i in range(len(v) - w + 1):
        s = sorted(v[i:i + w])
        m = len(s) // 2
        out.append(float(s[m]) if len(s) % 2 else (s[m - 1] + s[m]) / 2.0)
    return out


def brute_distinct(v, w):
    return [len(set(v[i:i + w])) for i in range(len(v) - w + 1)]


class T(unittest.TestCase):
    def test_correct_small_median(self):
        v = [3, 1, 4, 1, 5, 9, 2, 6]
        self.assertEqual(rolling_median(v, 3), brute_median(v, 3))
        self.assertEqual(rolling_median(v, 4), brute_median(v, 4))

    def test_correct_small_distinct(self):
        v = [1, 1, 2, 3, 1, 2, 2, 4]
        self.assertEqual(window_distinct_counts(v, 3), brute_distinct(v, 3))
        self.assertEqual(window_distinct_counts(v, 5), brute_distinct(v, 5))

    def test_correct_random(self):
        random.seed(11)
        for _ in range(5):
            v = [random.randint(0, 20) for _ in range(random.randint(1, 60))]
            w = random.randint(1, len(v))
            self.assertEqual(rolling_median(v, w), brute_median(v, w))
            self.assertEqual(window_distinct_counts(v, w), brute_distinct(v, w))

    def test_validation(self):
        for fn in (rolling_median, window_distinct_counts):
            with self.assertRaises(ValueError):
                fn([1, 2, 3], 0)
            with self.assertRaises(ValueError):
                fn([1, 2, 3], 4)

    def test_edge_cases(self):
        v = [5]
        self.assertEqual(rolling_median(v, 1), [5.0])
        self.assertEqual(window_distinct_counts(v, 1), [1])
        self.assertEqual(rolling_median([2, 1], 1), [2.0, 1.0])
        self.assertEqual(window_distinct_counts([7, 7, 7], 2), [1, 1])

    def test_perf_budget(self):
        """The whole point: sub-quadratic. Generous machine-relative budgets."""
        random.seed(7)
        n, w = 150_000, 2_500
        data = [random.randint(0, 1000) for _ in range(n)]
        t0 = time.time(); rolling_median(data, w); t1 = time.time()
        t2 = time.time(); window_distinct_counts(data, w); t3 = time.time()
        self.assertLess(t1 - t0, 3.0, "rolling_median too slow: %.1fs" % (t1 - t0))
        self.assertLess(t3 - t2, 3.0, "window_distinct_counts too slow: %.1fs" % (t3 - t2))


if __name__ == "__main__":
    unittest.main()
