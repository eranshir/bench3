"""A small, safe expression language for the segmentation service.

The language deliberately contains no function calls, attribute access, or
arithmetic.  Its useful subset is::

    expression  := expression "or" expression
                 | expression "and" expression
                 | "not" expression
                 | value comparison value
                 | "(" expression ")"
    comparison  := == | = | != | > | >= | < | <=
                 | contains | not contains | in | not in
                 | startswith | endswith | is [not]
    value       := field | string | number | true | false | null | list

Keywords are case-insensitive.  A dotted field name first tries an exact key
and then traverses nested dictionaries (``customer.plan``).  Missing fields
and type-incompatible comparisons simply do not match.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
import re


@dataclass(frozen=True)
class _Token:
    kind: str
    value: object
    position: int


_NUMBER = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_KEYWORDS = {
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "contains": "CONTAINS",
    "contain": "CONTAINS",
    "in": "IN",
    "startswith": "STARTSWITH",
    "starts_with": "STARTSWITH",
    "endswith": "ENDSWITH",
    "ends_with": "ENDSWITH",
    "starts": "STARTS",
    "ends": "ENDS",
    "with": "WITH",
    "does": "DOES",
    "is": "IS",
    "true": "LITERAL",
    "false": "LITERAL",
    "null": "LITERAL",
    "none": "LITERAL",
}


def _syntax(message, expression, position):
    pointer = " " * position + "^"
    return ValueError(f"{message} at character {position}\n{expression}\n{pointer}")


def _read_string(expression, start):
    """Read one quoted string without delegating to Python's evaluator."""
    quote = expression[start]
    result = []
    i = start + 1
    simple_escapes = {
        "\\": "\\",
        "'": "'",
        '"': '"',
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "b": "\b",
        "f": "\f",
        "v": "\v",
        "0": "\0",
    }
    while i < len(expression):
        char = expression[i]
        if char == quote:
            return "".join(result), i + 1
        if char != "\\":
            result.append(char)
            i += 1
            continue

        escape_position = i
        i += 1
        if i == len(expression):
            raise _syntax("Unterminated string escape", expression, escape_position)
        escaped = expression[i]
        if escaped in simple_escapes:
            result.append(simple_escapes[escaped])
            i += 1
            continue
        widths = {"x": 2, "u": 4, "U": 8}
        if escaped in widths:
            width = widths[escaped]
            digits = expression[i + 1:i + 1 + width]
            if len(digits) != width or any(c not in "0123456789abcdefABCDEF" for c in digits):
                raise _syntax("Invalid hexadecimal string escape", expression, escape_position)
            codepoint = int(digits, 16)
            try:
                result.append(chr(codepoint))
            except ValueError as exc:
                raise _syntax("Invalid Unicode code point", expression, escape_position) from exc
            i += width + 1
            continue
        raise _syntax(f"Unknown string escape \\{escaped}", expression, escape_position)
    raise _syntax("Unterminated string", expression, start)


def _tokenize(expression):
    tokens = []
    i = 0
    while i < len(expression):
        char = expression[i]
        if char.isspace():
            i += 1
        elif char in "'\"":
            value, end = _read_string(expression, i)
            tokens.append(_Token("LITERAL", value, i))
            i = end
        elif char.isdigit() or (char in "-." and i + 1 < len(expression)
                                and expression[i + 1].isdigit()):
            match = _NUMBER.match(expression, i)
            if not match:
                raise _syntax("Invalid number", expression, i)
            text = match.group(0)
            value = float(text) if any(c in text for c in ".eE") else int(text)
            tokens.append(_Token("LITERAL", value, i))
            i = match.end()
        elif char.isalpha() or char == "_":
            end = i + 1
            while end < len(expression) and (
                    expression[end].isalnum() or expression[end] in "_."):
                end += 1
            name = expression[i:end]
            kind = _KEYWORDS.get(name.lower(), "FIELD")
            if kind == "LITERAL":
                value = {"true": True, "false": False,
                         "null": None, "none": None}[name.lower()]
            else:
                value = name
            tokens.append(_Token(kind, value, i))
            i = end
        elif expression.startswith((">=", "<=", "==", "!=", "<>"), i):
            operator = expression[i:i + 2]
            tokens.append(_Token("COMPARE", "!=" if operator == "<>" else operator, i))
            i += 2
        elif char in "=><":
            tokens.append(_Token("COMPARE", "==" if char == "=" else char, i))
            i += 1
        elif char == "(":
            tokens.append(_Token("LPAREN", char, i))
            i += 1
        elif char == ")":
            tokens.append(_Token("RPAREN", char, i))
            i += 1
        elif char == "[":
            tokens.append(_Token("LBRACKET", char, i))
            i += 1
        elif char == "]":
            tokens.append(_Token("RBRACKET", char, i))
            i += 1
        elif char == ",":
            tokens.append(_Token("COMMA", char, i))
            i += 1
        else:
            raise _syntax(f"Unexpected character {char!r}", expression, i)
    tokens.append(_Token("EOF", None, len(expression)))
    return tokens


class _Parser:
    def __init__(self, expression):
        self.expression = expression
        self.tokens = _tokenize(expression)
        self.index = 0

    @property
    def current(self):
        return self.tokens[self.index]

    def accept(self, kind):
        if self.current.kind == kind:
            token = self.current
            self.index += 1
            return token
        return None

    def expect(self, kind, description):
        token = self.accept(kind)
        if token is None:
            raise _syntax(f"Expected {description}", self.expression,
                          self.current.position)
        return token

    def parse(self):
        if self.current.kind == "EOF":
            raise _syntax("Expression cannot be empty", self.expression, 0)
        node = self.parse_or()
        self.expect("EOF", "end of expression")
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.accept("OR"):
            node = ("or", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.accept("AND"):
            node = ("and", node, self.parse_not())
        return node

    def parse_not(self):
        if self.accept("NOT"):
            return ("not", self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        operands = [self.parse_value()]
        operators = []
        while True:
            operator = self._comparison_operator()
            if operator is None:
                break
            operators.append(operator)
            operands.append(self.parse_value())
        if not operators:
            return operands[0]
        return ("compare", operators, operands)

    def _comparison_operator(self):
        token = self.accept("COMPARE")
        if token:
            return token.value
        if self.accept("CONTAINS"):
            return "contains"
        if self.accept("IN"):
            return "in"
        if self.accept("STARTSWITH"):
            return "startswith"
        if self.accept("ENDSWITH"):
            return "endswith"
        if self.accept("STARTS"):
            self.expect("WITH", "'with' after 'starts'")
            return "startswith"
        if self.accept("ENDS"):
            self.expect("WITH", "'with' after 'ends'")
            return "endswith"
        if self.accept("DOES"):
            self.expect("NOT", "'not' after 'does'")
            self.expect("CONTAINS", "'contain' after 'does not'")
            return "not_contains"
        if self.accept("IS"):
            return "is_not" if self.accept("NOT") else "is"
        if self.current.kind == "NOT" and self.tokens[self.index + 1].kind in {
                "CONTAINS", "IN"}:
            self.index += 1
            kind = self.current.kind
            self.index += 1
            return "not_contains" if kind == "CONTAINS" else "not_in"
        return None

    def parse_value(self):
        token = self.accept("LITERAL")
        if token:
            return ("literal", token.value)
        token = self.accept("FIELD")
        if token:
            if token.value.startswith(".") or token.value.endswith(".") or ".." in token.value:
                raise _syntax("Invalid dotted field name", self.expression, token.position)
            return ("field", token.value)
        if self.accept("LPAREN"):
            node = self.parse_or()
            self.expect("RPAREN", "')'")
            return node
        if self.accept("LBRACKET"):
            values = []
            if not self.accept("RBRACKET"):
                while True:
                    values.append(self.parse_value())
                    if self.accept("RBRACKET"):
                        break
                    self.expect("COMMA", "',' or ']'")
            return ("list", values)
        raise _syntax("Expected a value", self.expression, self.current.position)


_MISSING = object()


def _field_value(record, name):
    # Exact lookup permits existing records with keys that happen to contain a
    # dot.  Traversal is the fallback for conventional nested records.
    if name in record:
        return record[name]
    value = record
    for part in name.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _contains(container, member):
    if container is _MISSING or member is _MISSING:
        return None
    if isinstance(container, str) and not isinstance(member, str):
        return None
    try:
        return member in container
    except (TypeError, ValueError):
        return None


def _compare(operator, left, right):
    if left is _MISSING or right is _MISSING:
        return False
    try:
        if operator == "==" or operator == "is":
            return left == right
        if operator == "!=" or operator == "is_not":
            return left != right
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        if operator in {"contains", "not_contains"}:
            result = _contains(left, right)
            return result is not None and (result if operator == "contains" else not result)
        if operator in {"in", "not_in"}:
            result = _contains(right, left)
            return result is not None and (result if operator == "in" else not result)
        if operator == "startswith":
            return isinstance(left, str) and isinstance(right, str) and left.startswith(right)
        if operator == "endswith":
            return isinstance(left, str) and isinstance(right, str) and left.endswith(right)
    except (TypeError, ValueError, OverflowError):
        return False
    return False


def _run(node, record):
    kind = node[0]
    if kind == "literal":
        return node[1]
    if kind == "field":
        return _field_value(record, node[1])
    if kind == "list":
        return [_run(item, record) for item in node[1]]
    if kind == "not":
        return not _truthy(_run(node[1], record))
    if kind == "and":
        return _truthy(_run(node[1], record)) and _truthy(_run(node[2], record))
    if kind == "or":
        return _truthy(_run(node[1], record)) or _truthy(_run(node[2], record))
    if kind == "compare":
        operators, operand_nodes = node[1], node[2]
        left = _run(operand_nodes[0], record)
        for operator, operand_node in zip(operators, operand_nodes[1:]):
            right = _run(operand_node, record)
            if not _compare(operator, left, right):
                return False
            left = right
        return True
    raise AssertionError(f"Unknown parse node: {kind}")


def _truthy(value):
    return False if value is _MISSING else bool(value)


@lru_cache(maxsize=512)
def _parse(expression):
    """Cache popular segment definitions without allowing unbounded growth."""
    return _Parser(expression).parse()


def evaluate(expression, record):
    """Return whether *record* matches *expression*.

    Invalid expression syntax raises :class:`ValueError`.  A missing field or
    an incompatible comparison evaluates to ``False`` so that a bad/migrating
    record cannot accidentally enter a segment.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping")
    tree = _parse(expression)
    return _truthy(_run(tree, record))
