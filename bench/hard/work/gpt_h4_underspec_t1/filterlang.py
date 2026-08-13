"""Filter expression language for the segmentation service.

A record is a plain dict. `evaluate` decides whether a record matches an
expression written by a non-engineer in the segment builder UI.

The language deliberately has no way to call functions or access Python
objects.  It supports boolean operators, comparisons, membership tests,
parentheses, scalar literals, list literals, and dotted paths into nested
dictionaries.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache


_MISSING = object()


@dataclass(frozen=True)
class _Token:
    kind: str
    value: object
    position: int


def _syntax_error(message, expression, position):
    """Create a useful, consistently formatted parse error."""
    pointer = " " * position + "^"
    return ValueError(f"{message} at position {position}\n{expression}\n{pointer}")


def _read_string(expression, start):
    quote = expression[start]
    chars = []
    i = start + 1
    escapes = {
        "\\": "\\",
        "'": "'",
        '"': '"',
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "b": "\b",
        "f": "\f",
        "/": "/",
    }

    while i < len(expression):
        char = expression[i]
        if char == quote:
            return "".join(chars), i + 1
        if char != "\\":
            chars.append(char)
            i += 1
            continue

        escape_position = i
        i += 1
        if i >= len(expression):
            raise _syntax_error("Unterminated escape sequence", expression, escape_position)
        escaped = expression[i]
        if escaped in escapes:
            chars.append(escapes[escaped])
            i += 1
        elif escaped in ("u", "U"):
            digits = 4 if escaped == "u" else 8
            raw = expression[i + 1 : i + 1 + digits]
            if len(raw) != digits or any(c not in "0123456789abcdefABCDEF" for c in raw):
                raise _syntax_error("Invalid Unicode escape", expression, escape_position)
            codepoint = int(raw, 16)
            try:
                chars.append(chr(codepoint))
            except ValueError:
                raise _syntax_error("Invalid Unicode escape", expression, escape_position) from None
            i += digits + 1
        else:
            raise _syntax_error(f"Unknown escape sequence \\{escaped}", expression, escape_position)

    raise _syntax_error("Unterminated string", expression, start)


def _tokenize(expression):
    tokens = []
    i = 0
    length = len(expression)

    while i < length:
        char = expression[i]
        if char.isspace():
            i += 1
            continue
        if char in "'\"":
            value, end = _read_string(expression, i)
            tokens.append(_Token("LITERAL", value, i))
            i = end
            continue
        if char in "()[],":
            tokens.append(_Token(char, char, i))
            i += 1
            continue

        matched = False
        for operator in ("==", "!=", ">=", "<=", "<>"):
            if expression.startswith(operator, i):
                tokens.append(_Token("OP", "!=" if operator == "<>" else operator, i))
                i += len(operator)
                matched = True
                break
        if matched:
            continue
        if char in "<>=":
            tokens.append(_Token("OP", "==" if char == "=" else char, i))
            i += 1
            continue

        # Signs are part of a number only where a value can begin.  Arithmetic
        # is intentionally not part of this language.
        may_have_sign = char in "+-" and i + 1 < length and (
            expression[i + 1].isdigit() or expression[i + 1] == "."
        )
        if char.isdigit() or (char == "." and i + 1 < length and expression[i + 1].isdigit()) or may_have_sign:
            start = i
            if expression[i] in "+-":
                i += 1
            digits_before = 0
            while i < length and expression[i].isdigit():
                digits_before += 1
                i += 1
            has_dot = i < length and expression[i] == "."
            if has_dot:
                i += 1
                while i < length and expression[i].isdigit():
                    i += 1
            if digits_before == 0 and not has_dot:
                raise _syntax_error("Invalid number", expression, start)
            has_exponent = i < length and expression[i] in "eE"
            if has_exponent:
                exponent_position = i
                i += 1
                if i < length and expression[i] in "+-":
                    i += 1
                exponent_start = i
                while i < length and expression[i].isdigit():
                    i += 1
                if exponent_start == i:
                    raise _syntax_error("Invalid number", expression, exponent_position)
            raw = expression[start:i]
            try:
                value = float(raw) if has_dot or has_exponent else int(raw)
            except ValueError:
                raise _syntax_error("Invalid number", expression, start) from None
            tokens.append(_Token("LITERAL", value, start))
            continue

        if char.isalpha() or char in "_$":
            start = i
            i += 1
            while i < length and (expression[i].isalnum() or expression[i] in "_.$-"):
                i += 1
            word = expression[start:i]
            lowered = word.lower()
            if lowered in ("and", "or", "not", "contains", "in", "is"):
                tokens.append(_Token(lowered.upper(), lowered, start))
            elif lowered in ("true", "false", "null", "none"):
                values = {"true": True, "false": False, "null": None, "none": None}
                tokens.append(_Token("LITERAL", values[lowered], start))
            else:
                tokens.append(_Token("IDENT", word, start))
            continue

        raise _syntax_error(f"Unexpected character {char!r}", expression, i)

    tokens.append(_Token("EOF", None, length))
    return tokens


class _Parser:
    def __init__(self, expression):
        self.expression = expression
        self.tokens = _tokenize(expression)
        self.index = 0

    @property
    def current(self):
        return self.tokens[self.index]

    def _accept(self, kind):
        if self.current.kind == kind:
            token = self.current
            self.index += 1
            return token
        return None

    def _expect(self, kind, description=None):
        token = self._accept(kind)
        if token is None:
            expected = description or kind
            raise _syntax_error(f"Expected {expected}", self.expression, self.current.position)
        return token

    def parse(self):
        if self.current.kind == "EOF":
            raise _syntax_error("Expression is empty", self.expression, 0)
        node = self._parse_or()
        if self.current.kind != "EOF":
            raise _syntax_error("Unexpected token", self.expression, self.current.position)
        return node

    def _parse_or(self):
        node = self._parse_and()
        while self._accept("OR"):
            node = ("or", node, self._parse_and())
        return node

    def _parse_and(self):
        node = self._parse_not()
        while self._accept("AND"):
            node = ("and", node, self._parse_not())
        return node

    def _parse_not(self):
        if self._accept("NOT"):
            return ("not", self._parse_not())
        return self._parse_comparison()

    def _comparison_operator(self):
        if self.current.kind == "OP":
            return self._accept("OP").value
        if self._accept("CONTAINS"):
            return "contains"
        if self._accept("IN"):
            return "in"
        if self._accept("IS"):
            return "is not" if self._accept("NOT") else "is"
        if self.current.kind == "NOT" and self.tokens[self.index + 1].kind in ("IN", "CONTAINS"):
            self.index += 1
            operator = self.current.value
            self.index += 1
            return "not " + operator
        return None

    def _parse_comparison(self):
        operands = [self._parse_primary()]
        operators = []
        while True:
            operator = self._comparison_operator()
            if operator is None:
                break
            operators.append(operator)
            operands.append(self._parse_primary())
        if not operators:
            return operands[0]
        return ("compare", tuple(operators), tuple(operands))

    def _parse_primary(self):
        token = self._accept("LITERAL")
        if token is not None:
            return ("literal", token.value)
        token = self._accept("IDENT")
        if token is not None:
            return ("field", token.value)
        if self._accept("("):
            node = self._parse_or()
            self._expect(")", "')'")
            return node
        if self._accept("["):
            values = []
            if not self._accept("]"):
                while True:
                    values.append(self._parse_or())
                    if self._accept("]"):
                        break
                    self._expect(",", "',' or ']'")
                    if self._accept("]"):  # Allow a trailing comma.
                        break
            return ("list", tuple(values))
        raise _syntax_error("Expected a value", self.expression, self.current.position)


def _field_value(record, path):
    # Prefer an exact key so existing flat records can legitimately contain a
    # dot.  Otherwise, dots provide convenient traversal of nested mappings.
    if path in record:
        return record[path]
    value = record
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _compare(operator, left, right):
    if left is _MISSING or right is _MISSING:
        return False
    if operator in ("is", "is not"):
        result = left is right if right is None else left == right
        return not result if operator == "is not" else result

    try:
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        if operator == "contains":
            return right in left
        if operator == "not contains":
            return right not in left
        if operator == "in":
            return left in right
        if operator == "not in":
            return left not in right
    except (TypeError, ValueError):
        # Badly shaped or mixed-type production records should fail closed,
        # rather than taking down evaluation for the whole segment.
        return False
    raise AssertionError(f"unknown comparison operator: {operator}")


def _evaluate_node(node, record):
    kind = node[0]
    if kind == "literal":
        return node[1]
    if kind == "field":
        return _field_value(record, node[1])
    if kind == "list":
        return [_evaluate_node(item, record) for item in node[1]]
    if kind == "not":
        value = _evaluate_node(node[1], record)
        return not (False if value is _MISSING else bool(value))
    if kind == "and":
        left = _evaluate_node(node[1], record)
        if left is _MISSING or not bool(left):
            return False
        right = _evaluate_node(node[2], record)
        return False if right is _MISSING else bool(right)
    if kind == "or":
        left = _evaluate_node(node[1], record)
        if left is not _MISSING and bool(left):
            return True
        right = _evaluate_node(node[2], record)
        return False if right is _MISSING else bool(right)
    if kind == "compare":
        operators, operand_nodes = node[1], node[2]
        left = _evaluate_node(operand_nodes[0], record)
        for operator, right_node in zip(operators, operand_nodes[1:]):
            right = _evaluate_node(right_node, record)
            if not _compare(operator, left, right):
                return False
            left = right
        return True
    raise AssertionError(f"unknown expression node: {kind}")


@lru_cache(maxsize=512)
def _parse(expression):
    """Cache the immutable parse tree when one segment tests many records."""
    return _Parser(expression).parse()


def evaluate(expression, record):
    """Return ``True`` if *record* matches *expression*, else ``False``.

    Invalid expression syntax raises :class:`ValueError`. Missing fields and
    comparisons between incompatible value types simply do not match.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping")
    tree = _parse(expression)
    result = _evaluate_node(tree, record)
    return False if result is _MISSING else bool(result)
