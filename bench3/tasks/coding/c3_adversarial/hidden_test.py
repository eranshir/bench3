import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scheduler import schedule


def brute(intervals):
    """Exact answer by trying every subset (small n only)."""
    n = len(intervals)
    best = 0
    for mask in range(1 << n):
        chosen = [intervals[i] for i in range(n) if mask >> i & 1]
        ok = True
        for i in range(len(chosen)):
            for j in range(i + 1, len(chosen)):
                a, b = chosen[i], chosen[j]
                if a[0] < b[1] and b[0] < a[1]:
                    ok = False
        if ok:
            best = max(best, len(chosen))
    return best


class T(unittest.TestCase):
    def test_classic_counterexample(self):
        self.assertEqual(schedule([(0, 10), (1, 2), (2, 3)]), 2)

    def test_long_early_blocks_many(self):
        self.assertEqual(schedule([(0, 8), (1, 2), (2, 3), (3, 4), (4, 5)]), 4)

    def test_touching_is_ok(self):
        self.assertEqual(schedule([(0, 1), (1, 2), (2, 3)]), 3)

    def test_single(self):
        self.assertEqual(schedule([(5, 10)]), 1)
        self.assertEqual(schedule([]), 0)

    def test_random_vs_brute(self):
        random.seed(42)
        for _ in range(20):
            n = random.randint(1, 8)
            ivs = []
            for _ in range(n):
                s = random.randint(0, 10)
                e = random.randint(s + 1, s + 6)
                ivs.append((s, e))
            self.assertEqual(schedule(ivs), brute(ivs), 'mismatch on %s' % ivs)

    def test_identical_starts(self):
        self.assertEqual(schedule([(0, 5), (0, 3), (0, 4)]), 1)


if __name__ == "__main__":
    unittest.main()
