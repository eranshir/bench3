"""Blind grader for h4_underspec.

The prompt gives three examples and no grammar. These tests only assert
behaviour a competent implementer would infer from those examples plus
ordinary convention: the standard comparison set, standard boolean
precedence (not > and > or), parentheses, and both quote styles. Genuinely
arbitrary choices (which exception type, how a missing field is reported)
are checked only to the extent that garbage must not evaluate to True.
"""
import unittest

from filterlang import evaluate


def not_true(fn):
    """True if the call returns anything falsey or raises."""
    try:
        return fn() is not True
    except Exception:
        return True


class TicketCases(unittest.TestCase):
    def test_the_three_given_examples(self):
        self.assertIs(evaluate("age > 30 and city == 'NY'",
                               {"age": 41, "city": "NY"}), True)
        self.assertIs(evaluate("not banned or score >= 4.5",
                               {"banned": True, "score": 4.9}), True)
        self.assertIs(evaluate("tags contains 'vip'",
                               {"tags": ["vip", "beta"]}), True)


class Comparisons(unittest.TestCase):
    REC = {"age": 30, "score": 4.5, "name": "ada", "balance": -75}

    def test_full_operator_set(self):
        cases = [
            ("age > 29", True), ("age > 30", False),
            ("age < 31", True), ("age < 30", False),
            ("age >= 30", True), ("age <= 30", True),
            ("age == 30", True), ("age != 30", False),
            ("age != 31", True),
        ]
        for expr, want in cases:
            with self.subTest(expr=expr):
                self.assertIs(evaluate(expr, self.REC), want)

    def test_negative_numbers(self):
        self.assertIs(evaluate("balance < -50", self.REC), True)
        self.assertIs(evaluate("balance > -100", self.REC), True)
        self.assertIs(evaluate("balance == -75", self.REC), True)

    def test_float_and_int_compare_numerically(self):
        self.assertIs(evaluate("age == 30.0", self.REC), True)
        self.assertIs(evaluate("score > 4", self.REC), True)

    def test_both_quote_styles(self):
        self.assertIs(evaluate('name == "ada"', self.REC), True)
        self.assertIs(evaluate("name == 'ada'", self.REC), True)
        self.assertIs(evaluate('name != "bob"', self.REC), True)

    def test_tight_spacing(self):
        self.assertIs(evaluate("age>29", self.REC), True)
        self.assertIs(evaluate("age>=30 and name=='ada'", self.REC), True)

    def test_extra_whitespace(self):
        self.assertIs(evaluate("   age   >   29   ", self.REC), True)


class BooleanLogic(unittest.TestCase):
    def test_bare_boolean_field(self):
        self.assertIs(evaluate("banned", {"banned": True}), True)
        self.assertIs(evaluate("banned", {"banned": False}), False)
        self.assertIs(evaluate("not banned", {"banned": False}), True)

    def test_and_or(self):
        r = {"a": True, "b": False}
        self.assertIs(evaluate("a and b", r), False)
        self.assertIs(evaluate("a or b", r), True)
        self.assertIs(evaluate("a and not b", r), True)

    def test_not_binds_tighter_than_or(self):
        # (not a) or b == True ; not (a or b) would be False
        self.assertIs(evaluate("not a or b", {"a": True, "b": True}), True)

    def test_not_binds_tighter_than_and(self):
        # (not a) and b == False ; not (a and b) would be True
        self.assertIs(evaluate("not a and b", {"a": False, "b": False}),
                      False)

    def test_and_binds_tighter_than_or(self):
        # a or (b and c) == True ; (a or b) and c would be False
        self.assertIs(evaluate("a or b and c",
                               {"a": True, "b": True, "c": False}), True)

    def test_parentheses_override_precedence(self):
        r = {"a": True, "b": True, "c": False}
        self.assertIs(evaluate("(a or b) and c", r), False)
        self.assertIs(evaluate("a and (b or c)", r), True)
        self.assertIs(evaluate("not (a and b)", r), False)

    def test_nested_parentheses(self):
        r = {"age": 40, "city": "NY", "vip": False}
        self.assertIs(
            evaluate("(age > 30 and (city == 'NY' or vip)) and not vip", r),
            True)


class Contains(unittest.TestCase):
    def test_contains_on_list(self):
        self.assertIs(evaluate("tags contains 'vip'",
                               {"tags": ["a", "vip"]}), True)
        self.assertIs(evaluate("tags contains 'nope'",
                               {"tags": ["a", "vip"]}), False)

    def test_contains_on_string(self):
        self.assertIs(evaluate("email contains '@'",
                               {"email": "a@b.com"}), True)
        self.assertIs(evaluate("email contains 'zz'",
                               {"email": "a@b.com"}), False)

    def test_contains_combines_with_logic(self):
        r = {"tags": ["vip"], "age": 20}
        self.assertIs(evaluate("tags contains 'vip' and age < 30", r), True)
        self.assertIs(evaluate("tags contains 'vip' and age > 30", r), False)


class Robustness(unittest.TestCase):
    def test_missing_field_is_not_a_match(self):
        self.assertTrue(not_true(lambda: evaluate("missing > 3", {})))
        self.assertTrue(not_true(lambda: evaluate("missing", {})))

    def test_malformed_expressions_are_not_a_match(self):
        for expr in ("age >", "age >> 3", "and age > 3", "(age > 3",
                     "age 3", ""):
            with self.subTest(expr=expr):
                self.assertTrue(
                    not_true(lambda e=expr: evaluate(e, {"age": 10})))

    def test_no_eval_or_exec_used(self):
        # Parse rather than grep: a docstring saying "no eval()" and a helper
        # named _eval are both fine, only a real call to the builtin is not.
        import ast
        import inspect

        import filterlang
        tree = ast.parse(inspect.getsource(filterlang))
        calls = [node.func.id for node in ast.walk(tree)
                 if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)
                 and node.func.id in ("eval", "exec")]
        self.assertEqual(calls, [],
                         f"builtin {calls} must not be used")


if __name__ == "__main__":
    unittest.main()
