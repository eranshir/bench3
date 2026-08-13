import unittest
from walker import collect_values, max_depth

TREE = {
    "value": "a",
    "children": [
        {"value": "b", "children": [{"value": "c", "children": []}]},
        {"value": "d", "children": []},
    ],
}


class T(unittest.TestCase):
    def test_collect(self):
        self.assertEqual(collect_values(TREE), ["a", "b", "c", "d"])

    def test_depth(self):
        self.assertEqual(max_depth(TREE), 2)


if __name__ == "__main__":
    unittest.main()
