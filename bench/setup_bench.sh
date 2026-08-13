#!/bin/bash
# Generates the benchmark task fixtures. Idempotent — safe to re-run.
# Each task has: a fixture dir, a PROMPT.txt, and a HIDDEN test the model never sees.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$ROOT/tasks" "$ROOT/hidden"
mkdir -p "$ROOT/tasks" "$ROOT/hidden"

# ---------------------------------------------------------------- T1: bugfix
mkdir -p "$ROOT/tasks/t1_bugfix"
cat > "$ROOT/tasks/t1_bugfix/stats.py" << 'PY'
def percentile(values, p):
    """Return the p-th percentile (0-100) using nearest-rank.

    Nearest-rank: the smallest value at or below which at least p% of the
    data falls. For p=50 over [1,2,3,4] that is 2.
    """
    if not values:
        raise ValueError("values must be non-empty")
    s = sorted(values)
    rank = int(p / 100 * len(s))
    return s[rank]
PY
cat > "$ROOT/tasks/t1_bugfix/PROMPT.txt" << 'TXT'
percentile() in stats.py is wrong. It uses nearest-rank as documented in its
docstring, but the rank computation is off: percentile([1,2,3,4], 50) returns 3
when the docstring says it must return 2, and percentile([1,2,3,4], 100) raises
IndexError instead of returning 4.

Fix the rank computation so it matches the documented nearest-rank definition.
Do not change the docstring or the function signature. Handle p=0 and p=100.

Verify with:
  python3 -c "from stats import percentile as q; print(q([1,2,3,4],50), q([1,2,3,4],100), q([1,2,3,4],0))"
It must print: 2 4 1
TXT
cat > "$ROOT/hidden/t1_bugfix_test.py" << 'PY'
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
PY

# ------------------------------------------------------------ T2: multi-file
mkdir -p "$ROOT/tasks/t2_multifile/app"
cat > "$ROOT/tasks/t2_multifile/app/__init__.py" << 'PY'
PY
cat > "$ROOT/tasks/t2_multifile/app/config.py" << 'PY'
DEFAULTS = {
    "host": "localhost",
    "port": 8000,
    "debug": False,
}


class Config:
    def __init__(self, values):
        self._values = values

    def get(self, key):
        return self._values[key]

    def as_dict(self):
        return dict(self._values)
PY
cat > "$ROOT/tasks/t2_multifile/app/loader.py" << 'PY'
from .config import DEFAULTS, Config


def load_config(overrides=None):
    values = dict(DEFAULTS)
    if overrides:
        values.update(overrides)
    return Config(values)
PY
cat > "$ROOT/tasks/t2_multifile/app/main.py" << 'PY'
from .loader import load_config


def describe():
    cfg = load_config()
    return f"{cfg.get('host')}:{cfg.get('port')} debug={cfg.get('debug')}"
PY
cat > "$ROOT/tasks/t2_multifile/PROMPT.txt" << 'TXT'
Add environment-variable overrides to this config system, threading the change
through the existing files in app/ (config.py, loader.py, main.py).

Requirements:
- An env var named APP_<KEY_UPPERCASE> overrides the matching default.
  e.g. APP_HOST overrides "host", APP_PORT overrides "port".
- Precedence, lowest to highest: DEFAULTS, then env vars, then the explicit
  `overrides` dict passed to load_config().
- Types must be coerced to match the type of the default value: "port" stays an
  int, "debug" stays a bool. For bools, the strings "1", "true", "True", "yes"
  are True; "0", "false", "False", "no" are False.
- Unknown APP_* env vars (no matching key in DEFAULTS) are ignored.
- Do not change the public API: load_config(overrides=None) -> Config, and
  Config.get / Config.as_dict must keep working as they do now.

Verify with:
  APP_PORT=9000 APP_DEBUG=true python3 -c "from app.main import describe; print(describe())"
It must print: localhost:9000 debug=True
TXT
cat > "$ROOT/hidden/t2_multifile_test.py" << 'PY'
import os
import unittest
from app.loader import load_config


class T(unittest.TestCase):
    def setUp(self):
        for k in list(os.environ):
            if k.startswith("APP_"):
                del os.environ[k]

    tearDown = setUp

    def test_defaults(self):
        c = load_config()
        self.assertEqual(c.get("host"), "localhost")
        self.assertEqual(c.get("port"), 8000)
        self.assertIs(c.get("debug"), False)

    def test_env_override_with_types(self):
        os.environ["APP_PORT"] = "9000"
        os.environ["APP_DEBUG"] = "true"
        c = load_config()
        self.assertEqual(c.get("port"), 9000)
        self.assertIsInstance(c.get("port"), int)
        self.assertIs(c.get("debug"), True)

    def test_bool_falsey_strings(self):
        for s in ("0", "false", "False", "no"):
            os.environ["APP_DEBUG"] = s
            self.assertIs(load_config().get("debug"), False, s)

    def test_explicit_overrides_win(self):
        os.environ["APP_PORT"] = "9000"
        self.assertEqual(load_config({"port": 1234}).get("port"), 1234)

    def test_unknown_env_ignored(self):
        os.environ["APP_NOPE"] = "x"
        self.assertNotIn("nope", load_config().as_dict())

    def test_api_unchanged(self):
        self.assertEqual(
            set(load_config().as_dict()), {"host", "port", "debug"}
        )


if __name__ == "__main__":
    unittest.main()
PY

# ----------------------------------------------------------- T3: from tests
mkdir -p "$ROOT/tasks/t3_tdd"
cat > "$ROOT/tasks/t3_tdd/duration.py" << 'PY'
def parse_duration(text):
    """Parse a duration string like '1h30m' into total seconds."""
    raise NotImplementedError
PY
cat > "$ROOT/tasks/t3_tdd/test_duration.py" << 'PY'
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
PY
cat > "$ROOT/tasks/t3_tdd/PROMPT.txt" << 'TXT'
Implement parse_duration() in duration.py so that the existing test suite in
test_duration.py passes in full.

Do NOT modify test_duration.py — the tests define the spec. Read them.

Verify with:
  python3 -m unittest test_duration -v
All tests must pass.
TXT
cat > "$ROOT/hidden/t3_tdd_test.py" << 'PY'
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
PY

# -------------------------------------------------------- T4: subtle debug
mkdir -p "$ROOT/tasks/t4_debug"
cat > "$ROOT/tasks/t4_debug/cart.py" << 'PY'
class Cart:
    def __init__(self, items=[]):
        self.items = items

    def add(self, name, price, qty=1):
        self.items.append({"name": name, "price": price, "qty": qty})
        return self

    def total(self):
        return sum(i["price"] * i["qty"] for i in self.items)

    def apply_discount(self, pct):
        for i in self.items:
            i["price"] = i["price"] * (100 - pct) / 100
        return self
PY
cat > "$ROOT/tasks/t4_debug/repro.py" << 'PY'
from cart import Cart

a = Cart()
a.add("widget", 10.0)
b = Cart()
print("cart b should be empty, got:", b.items)

c = Cart()
c.add("thing", 100.0)
c.apply_discount(10)
c.apply_discount(10)
print("expected 81.0 after two 10% discounts, got:", c.total())
PY
cat > "$ROOT/tasks/t4_debug/PROMPT.txt" << 'TXT'
Run `python3 repro.py`. It demonstrates two bugs in cart.py.

Bug 1: a freshly constructed Cart is not empty — it shares state with previously
constructed carts.

Bug 2: repeated apply_discount calls compound in a way that loses precision and
mutates the original price irrecoverably, so the cart can never report its
pre-discount total.

Fix both:
- Each Cart must start with its own independent, empty item list.
- Keep the original unit price intact. Add a `subtotal()` method returning the
  pre-discount total, while `total()` returns the discounted total. Discounts
  must remain compounding (two 10% discounts leave 81% of the original).
- Round money to 2 decimal places when reporting totals.

Do not change the constructor signature Cart(items=None) -> Cart beyond what is
needed to fix bug 1; callers pass no arguments.

Verify with: python3 repro.py
It must show cart b empty and a total of 81.0.
TXT
cat > "$ROOT/hidden/t4_debug_test.py" << 'PY'
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
PY

# --------------------------------------------------------- T5: refactor
mkdir -p "$ROOT/tasks/t5_refactor"
cat > "$ROOT/tasks/t5_refactor/walker.py" << 'PY'
def walk(tree, visit):
    """Depth-first walk, calling visit(node_value, depth) on each node.

    A tree node is {"value": X, "children": [...]}.
    """
    def _go(node, depth):
        visit(node["value"], depth)
        for child in node.get("children", []):
            _go(child, depth + 1)

    _go(tree, 0)


def collect_values(tree):
    out = []
    walk(tree, lambda v, d: out.append(v))
    return out


def max_depth(tree):
    seen = []
    walk(tree, lambda v, d: seen.append(d))
    return max(seen)
PY
cat > "$ROOT/tasks/t5_refactor/test_walker.py" << 'PY'
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
PY
cat > "$ROOT/tasks/t5_refactor/PROMPT.txt" << 'TXT'
Refactor walker.py to replace the callback-based walk() with a generator named
iter_nodes(tree) that yields (value, depth) tuples in the same depth-first order.

Requirements:
- Rewrite collect_values() and max_depth() to consume iter_nodes().
- Remove the callback-based walk() entirely.
- iter_nodes must be lazy: it must not build the full node list up front.
  Taking the first item from an infinitely deep tree must not hang.
- Make it iterative rather than recursive, so a 10,000-deep tree does not blow
  the Python recursion limit.
- The existing tests in test_walker.py must still pass unmodified.

Verify with:
  python3 -m unittest test_walker -v
All tests must pass.
TXT
cat > "$ROOT/hidden/t5_refactor_test.py" << 'PY'
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
PY

echo "Created $(ls -1 "$ROOT/tasks" | wc -l | tr -d ' ') tasks in $ROOT/tasks"
ls -1 "$ROOT/tasks"
