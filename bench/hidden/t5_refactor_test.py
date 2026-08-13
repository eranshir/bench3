import itertools
import unittest
import walker

TREE = {
    "value": "a",
    "children": [
        {"value": "b", "children": [{"value": "c", "children": []}]},
        {"value": "d", "children": []},
    ],
}


def deep(n):
    root = {"value": 0, "children": []}
    cur = root
    for i in range(1, n):
        nxt = {"value": i, "children": []}
        cur["children"].append(nxt)
        cur = nxt
    return root


class T(unittest.TestCase):
    def test_original_behaviour(self):
        self.assertEqual(walker.collect_values(TREE), ["a", "b", "c", "d"])
        self.assertEqual(walker.max_depth(TREE), 2)

    def test_generator_exists_and_yields_pairs(self):
        got = list(walker.iter_nodes(TREE))
        self.assertEqual(got, [("a", 0), ("b", 1), ("c", 2), ("d", 1)])

    def test_callback_walk_removed(self):
        self.assertFalse(hasattr(walker, "walk"))

    def test_lazy(self):
        it = walker.iter_nodes(deep(100000))
        self.assertEqual(next(iter(it)), (0, 0))

    def test_deep_no_recursion_error(self):
        self.assertEqual(walker.max_depth(deep(10000)), 9999)

    def test_is_generator(self):
        self.assertTrue(hasattr(walker.iter_nodes(TREE), "__next__"))


if __name__ == "__main__":
    unittest.main()
