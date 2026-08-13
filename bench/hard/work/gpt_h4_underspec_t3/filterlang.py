"""A small, safe expression language for filtering dictionaries.

The language deliberately contains no function calls or attribute access.  It
supports boolean operators, comparisons, membership tests, literals, lists,
parentheses, and dotted paths through nested dictionaries.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import re
from typing import Any


class FilterSyntaxError(ValueError):
    """Raised when a filter expression is not valid."""


@dataclass(frozen=True)
class _Token:
    kind: str
    value: Any
    position: int


_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_KEYWORDS = {
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "contains": "CONTAINS",
    "in": "IN",
    "is": "IS",
    "true": "TRUE",
    "false": "FALSE",
    "null": "NULL",
    "none": "NULL",
}
_SINGLE_CHAR = {
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ",": "COMMA",
}


def _syntax(message: str, expression: str, position: int) -> FilterSyntaxError:
    pointer = " " * position + "^"
    return FilterSyntaxError(f"{message} at position {position}\n{expression}\n{pointer}")


def _read_string(expression: str, start: int) -> tuple[str, int]:
    quote = expression[start]
    chars: list[str] = []
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
        if i == len(expression):
            raise _syntax("Unterminated escape sequence", expression, escape_position)
        escaped = expression[i]
        if escaped in escapes:
            chars.append(escapes[escaped])
            i += 1
        elif escaped in {"u", "x"}:
            digits = 4 if escaped == "u" else 2
            raw = expression[i + 1 : i + 1 + digits]
            if len(raw) != digits or any(c not in "0123456789abcdefABCDEF" for c in raw):
                raise _syntax("Invalid hexadecimal escape", expression, escape_position)
            chars.append(chr(int(raw, 16)))
            i += digits + 1
        else:
            raise _syntax(f"Unknown escape sequence \\{escaped}", expression, escape_position)

    raise _syntax("Unterminated string", expression, start)


def _tokenize(expression: str) -> list[_Token]:
    tokens: list[_Token] = []
    i = 0

    while i < len(expression):
        char = expression[i]
        if char.isspace():
            i += 1
            continue

        if char in "'\"":
            value, end = _read_string(expression, i)
            tokens.append(_Token("LITERAL", value, i))
            i = end
            continue

        # A leading sign belongs to a number only where a value can begin.
        signed = char in "+-" and i + 1 < len(expression) and (
            expression[i + 1].isdigit() or expression[i + 1] == "."
        )
        number_start = i + 1 if signed else i
        number_match = _NUMBER.match(expression, number_start)
        if number_match and (signed or char.isdigit() or char == "."):
            raw = expression[i : number_match.end()]
            try:
                value = float(raw) if any(c in raw for c in ".eE") else int(raw)
            except ValueError:
                raise _syntax("Invalid number", expression, i) from None
            tokens.append(_Token("LITERAL", value, i))
            i = number_match.end()
            continue

        two_chars = expression[i : i + 2]
        if two_chars in {"==", "!=", "<=", ">=", "&&", "||"}:
            kind = {"&&": "AND", "||": "OR"}.get(two_chars, "COMPARE")
            tokens.append(_Token(kind, two_chars, i))
            i += 2
            continue
        if char in "<>=":
            tokens.append(_Token("COMPARE", "==" if char == "=" else char, i))
            i += 1
            continue
        if char == "!":
            tokens.append(_Token("NOT", "!", i))
            i += 1
            continue
        if char in _SINGLE_CHAR:
            tokens.append(_Token(_SINGLE_CHAR[char], char, i))
            i += 1
            continue

        if char.isalpha() or char == "_":
            end = i + 1
            while end < len(expression) and (
                expression[end].isalnum() or expression[end] in "_.-"
            ):
                end += 1
            word = expression[i:end]
            keyword = _KEYWORDS.get(word.casefold())
            tokens.append(_Token(keyword or "IDENT", word, i))
            i = end
            continue

        raise _syntax(f"Unexpected character {char!r}", expression, i)

    tokens.append(_Token("EOF", None, len(expression)))
    return tokens


class _Missing:
    def __bool__(self) -> bool:
        return False


_MISSING = _Missing()


def _lookup(record: Mapping[str, Any], path: str) -> Any:
    # Prefer an exact key.  This preserves records that genuinely use dots in
    # field names while still making ``customer.address.city`` convenient.
    if path in record:
        return record[path]

    value: Any = record
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _contains(container: Any, item: Any) -> bool:
    if container is _MISSING:
        return False
    if isinstance(container, str) and not isinstance(item, str):
        return False
    try:
        return item in container
    except (TypeError, ValueError):
        return False


def _equal(left: Any, right: Any) -> bool:
    if left is _MISSING or right is _MISSING:
        return False
    # bool is a subclass of int in Python, but treating true as 1 is surprising
    # in a language intended for hand-authored audience segments.
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    try:
        return bool(left == right)
    except (TypeError, ValueError):
        return False


def _compare(operator: str, left: Any, right: Any) -> bool:
    # An absent field is not evidence for any comparison, including a negated
    # one.  Authors can still test its truthiness explicitly with ``not field``.
    if left is _MISSING or right is _MISSING:
        return False
    if operator == "==":
        return _equal(left, right)
    if operator == "!=":
        return not _equal(left, right)
    if operator == "contains":
        return _contains(left, right)
    if operator == "not contains":
        return not _contains(left, right)
    if operator == "in":
        return _contains(right, left)
    if operator == "not in":
        return not _contains(right, left)
    if operator == "is":
        return _equal(left, right)
    if operator == "is not":
        return not _equal(left, right)
    if isinstance(left, bool) or isinstance(right, bool):
        return False
    try:
        if operator == "<":
            return bool(left < right)
        if operator == "<=":
            return bool(left <= right)
        if operator == ">":
            return bool(left > right)
        if operator == ">=":
            return bool(left >= right)
        raise AssertionError(f"unknown comparison operator: {operator}")
    except (TypeError, ValueError):
        return False


class _Parser:
    def __init__(self, expression: str, record: Mapping[str, Any]):
        self.expression = expression
        self.record = record
        self.tokens = _tokenize(expression)
        self.index = 0

    @property
    def current(self) -> _Token:
        return self.tokens[self.index]

    def _take(self, kind: str) -> _Token:
        token = self.current
        if token.kind != kind:
            raise _syntax(f"Expected {kind.lower()}, found {self._describe(token)}",
                          self.expression, token.position)
        self.index += 1
        return token

    @staticmethod
    def _describe(token: _Token) -> str:
        return "end of expression" if token.kind == "EOF" else repr(token.value)

    def parse(self) -> Any:
        if self.current.kind == "EOF":
            raise _syntax("Expression is empty", self.expression, 0)
        result = self._or()
        if self.current.kind != "EOF":
            raise _syntax(f"Unexpected token {self._describe(self.current)}",
                          self.expression, self.current.position)
        return result

    def _or(self) -> Any:
        left = self._and()
        while self.current.kind == "OR":
            self.index += 1
            right = self._and()  # Always parse the RHS, even when short-circuiting.
            left = bool(left) or bool(right)
        return left

    def _and(self) -> Any:
        left = self._not()
        while self.current.kind == "AND":
            self.index += 1
            right = self._not()
            left = bool(left) and bool(right)
        return left

    def _not(self) -> Any:
        if self.current.kind == "NOT":
            self.index += 1
            return not bool(self._not())
        return self._comparison()

    def _comparison_operator(self) -> str | None:
        token = self.current
        if token.kind == "COMPARE":
            self.index += 1
            return token.value
        if token.kind == "IS" and self.tokens[self.index + 1].kind == "NOT":
            self.index += 2
            return "is not"
        if token.kind in {"CONTAINS", "IN", "IS"}:
            self.index += 1
            return token.value.casefold()
        if token.kind == "NOT" and self.tokens[self.index + 1].kind in {"CONTAINS", "IN"}:
            self.index += 2
            return "not " + self.tokens[self.index - 1].value.casefold()
        return None

    def _comparison(self) -> Any:
        left = self._primary()
        results: list[bool] = []
        while True:
            operator = self._comparison_operator()
            if operator is None:
                break
            right = self._primary()
            results.append(_compare(operator, left, right))
            left = right
        return all(results) if results else left

    def _primary(self) -> Any:
        token = self.current
        if token.kind == "LITERAL":
            self.index += 1
            return token.value
        if token.kind == "TRUE":
            self.index += 1
            return True
        if token.kind == "FALSE":
            self.index += 1
            return False
        if token.kind == "NULL":
            self.index += 1
            return None
        if token.kind == "IDENT":
            self.index += 1
            return _lookup(self.record, token.value)
        if token.kind == "LPAREN":
            self.index += 1
            value = self._or()
            self._take("RPAREN")
            return value
        if token.kind == "LBRACKET":
            return self._list()
        raise _syntax(f"Expected a value, found {self._describe(token)}",
                      self.expression, token.position)

    def _list(self) -> list[Any]:
        self.index += 1
        values: list[Any] = []
        if self.current.kind == "RBRACKET":
            self.index += 1
            return values
        while True:
            values.append(self._primary())
            if self.current.kind != "COMMA":
                break
            self.index += 1
            if self.current.kind == "RBRACKET":  # Allow a trailing comma.
                break
        self._take("RBRACKET")
        return values


def evaluate(expression: str, record: Mapping[str, Any]) -> bool:
    """Return whether *record* matches *expression*.

    Examples of accepted expressions::

        age > 30 and city == 'NY'
        not banned or score >= 4.5
        tags contains 'vip'
        country in ['US', 'CA'] and profile.active is true

    Invalid expressions raise :class:`FilterSyntaxError`.  Missing fields and
    comparisons between incompatible value types simply do not match.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping")
    return bool(_Parser(expression, record).parse())
