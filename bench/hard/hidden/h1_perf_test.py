"""Blind grader for h1_perf.

Correctness is checked against a brute-force reference that encodes the
ORIGINAL semantics, so an implementation that is fast but subtly different
fails. Performance is checked with wall-clock budgets set well above what a
correct sub-quadratic solution needs and well below what the shipped
quadratic version takes.
"""
import random
import time
import unittest

import analytics


def ref_median(values, window):
    out = []
    for i in range(len(values) - window + 1):
        chunk = sorted(values[i:i + window])
        mid = window // 2
        if window % 2:
            out.append(float(chunk[mid]))
        else:
            out.append((chunk[mid - 1] + chunk[mid]) / 2.0)
    return out


def ref_distinct(values, window):
    return [len(set(values[i:i + window]))
            for i in range(len(values) - window + 1)]


class Correctness(unittest.TestCase):
    def test_matches_reference_random(self):
        rng = random.Random(1234)
        for trial in range(40):
            n = rng.randint(1, 60)
            vals = [rng.randint(-20, 20) for _ in range(n)]
            w = rng.randint(1, n)
            self.assertEqual(analytics.rolling_median(vals, w),
                             ref_median(vals, w), f"median trial {trial}")
            self.assertEqual(analytics.window_distinct_counts(vals, w),
                             ref_distinct(vals, w), f"distinct trial {trial}")

    def test_even_window_averages_two_middles(self):
        self.assertEqual(analytics.rolling_median([1, 2, 3, 4], 2),
                         [1.5, 2.5, 3.5])
        self.assertEqual(analytics.rolling_median([5, 1, 9, 3], 4), [4.0])

    def test_window_of_one(self):
        self.assertEqual(analytics.rolling_median([3, 1, 2], 1),
                         [3.0, 1.0, 2.0])
        self.assertEqual(analytics.window_distinct_counts([3, 1, 2], 1),
                         [1, 1, 1])

    def test_window_larger_than_series_is_empty(self):
        self.assertEqual(analytics.rolling_median([1, 2], 5), [])
        self.assertEqual(analytics.window_distinct_counts([1, 2], 5), [])

    def test_empty_series(self):
        self.assertEqual(analytics.rolling_median([], 3), [])
        self.assertEqual(analytics.window_distinct_counts([], 3), [])

    def test_non_positive_window_raises(self):
        for w in (0, -1):
            with self.assertRaises(ValueError):
                analytics.rolling_median([1, 2, 3], w)
            with self.assertRaises(ValueError):
                analytics.window_distinct_counts([1, 2, 3], w)

    def test_duplicates_and_negatives(self):
        vals = [-5, -5, -5, 2, 2, 7, -1]
        for w in (2, 3, 4):
            self.assertEqual(analytics.rolling_median(vals, w),
                             ref_median(vals, w))
            self.assertEqual(analytics.window_distinct_counts(vals, w),
                             ref_distinct(vals, w))

    def test_floats_accepted(self):
        vals = [1.5, -2.25, 8.0, 3.125, 3.125]
        self.assertEqual(analytics.rolling_median(vals, 3),
                         ref_median(vals, 3))


class Performance(unittest.TestCase):
    """Budgets are generous for an O(n log w) / O(n) solution and

    unreachable for the shipped O(n*w) one."""

    def test_rolling_median_is_subquadratic(self):
        rng = random.Random(7)
        series = [rng.randint(0, 10_000) for _ in range(100_000)]
        t = time.perf_counter()
        got = analytics.rolling_median(series, 1001)
        elapsed = time.perf_counter() - t
        self.assertEqual(len(got), 99_000)
        # spot-check correctness on the large input at both ends and middle
        for i in (0, 1, 4321, 50_000, 98_999):
            self.assertAlmostEqual(
                got[i], ref_median(series[i:i + 1001], 1001)[0], places=9,
                msg=f"wrong median at window {i}")
        self.assertLess(elapsed, 4.0,
                        f"rolling_median took {elapsed:.1f}s (budget 4s)")

    def test_distinct_counts_is_subquadratic(self):
        rng = random.Random(7)
        series = [rng.randint(0, 500) for _ in range(200_000)]
        t = time.perf_counter()
        got = analytics.window_distinct_counts(series, 2001)
        elapsed = time.perf_counter() - t
        self.assertEqual(len(got), 198_000)
        for i in (0, 999, 100_000, 197_999):
            self.assertEqual(got[i], len(set(series[i:i + 2001])),
                             f"wrong distinct count at window {i}")
        self.assertLess(elapsed, 4.0,
                        f"window_distinct_counts took {elapsed:.1f}s "
                        f"(budget 4s)")


if __name__ == "__main__":
    unittest.main()
