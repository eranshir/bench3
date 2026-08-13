"""Filter expression language for the segmentation service.

A record is a plain dict. `evaluate` decides whether a record matches an
expression written by a non-engineer in the segment builder UI.

Supported syntax (keywords are case-insensitive):

  * comparisons:  ==  !=  <  <=  >  >=   (a single `=` means `==`)
  * boolean:      and  or  not, with standard precedence and parentheses
  * membership:   contains, in, not contains, not in
  * strings:      starts with, ends with, matches <regex>
  * presence:     is null, is not null, is empty, is not empty,
                  is defined, is not defined, exists, not exists
  * literals:     numbers, 'single' / "double" quoted strings,
                  true/false, null (also none/nil)
  * fields:       plain names or dotted paths (user.age), with optional
                  [n] list indexing (items[0].price)

An absent field evaluates to a missing sentinel: it is falsy in boolean
context, compares False against any comparison, and counts as null / not
defined in presence checks.  On the right-hand side of a comparison, an
unquoted identifier that is not a record field is treated as a string
literal, so `city == NY` works like `city == 'NY'`.
"""

import re
from collections.abc import Mapping


class _Missing:
    """Singleton returned for fields that are absent from the record."""

    def __bool__(self):
        return False

    def __repr__(self):
        return "<missing>"


_MISSING = _Missing()


_TOKEN_RE = re.compile(
    r"""
    \s*(?:
        (?P<number>-?\d+(?:\.\d+)?)
      | (?P<string>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")
      | (?P<op><=|>=|==|!=|=|<|>)
      | (?P<lparen>\()
      | (?P<rparen>\))
      | (?P<lbracket>\[)
      | (?P<rbracket>\])
      | (?P<comma>,)
      | (?P<dot>\.)
      | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<error>.)
    )
    """,
    re.VERBOSE,
)


_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'", '"': '"'}


class _Token:
    __slots__ = ("kind", "value")

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f"_Token({self.kind!r}, {self.value!r})"


def _tokenize(text):
    tokens = []
    pos = 0
    while pos < len(text):
        match = _TOKEN_RE.match(text, pos)
        if match is None or match.end() == pos:
            raise ValueError(
                f"invalid character at position {pos} in filter expression {text!r}"
            )
        kind = match.lastgroup
        if kind == "error":
            raise ValueError(
                f"invalid character {match.group()!r} at position {pos} "
                f"in filter expression {text!r}"
            )
        tokens.append(_Token(kind, match.group(kind)))
        pos = match.end()
    tokens.append(_Token("eof", None))
    return tokens


def _parse_number(text):
    return float(text) if "." in text else int(text)


def _decode_string(raw):
    body = raw[1:-1]
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            out.append(_ESCAPES.get(body[i + 1], body[i + 1]))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _to_number(value):
    """Coerce ints, floats, and numeric strings to a comparable number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            text = value.strip()
            if not text or text.lower() in ("inf", "-inf", "nan", "+inf"):
                return None
            if any(ch in text for ch in ".eE"):
                return float(text)
            return int(text)
        except ValueError:
            return None
    return None


def _equal(a, b):
    if a is _MISSING or b is _MISSING:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    anum = _to_number(a)
    bnum = _to_number(b)
    if anum is not None and bnum is not None and (
        isinstance(a, (int, float)) or isinstance(b, (int, float))
    ):
        return anum == bnum
    return a == b


def _ordered_compare(a, b, op):
    anum = _to_number(a)
    bnum = _to_number(b)
    if anum is not None and bnum is not None and (
        isinstance(a, (int, float)) or isinstance(b, (int, float))
    ):
        a, b = anum, bnum
    elif not (isinstance(a, str) and isinstance(b, str)):
        return False
    try:
        if op == "<":
            return a < b
        if op == "<=":
            return a <= b
        if op == ">":
            return a > b
        if op == ">=":
            return a >= b
    except TypeError:
        return False
    return False


class _Parser:
    def __init__(self, text):
        self._tokens = _tokenize(text)
        self._pos = 0

    def _peek(self, offset=0):
        index = self._pos + offset
        if index >= len(self._tokens):
            return self._tokens[-1]
        return self._tokens[index]

    def _next(self):
        token = self._peek()
        if token.kind != "eof":
            self._pos += 1
        return token

    def _accept(self, kind):
        token = self._peek()
        if token.kind == kind:
            self._pos += 1
            return token
        return None

    def _accept_kw(self, *words):
        token = self._peek()
        if token.kind == "ident" and token.value.lower() in words:
            self._pos += 1
            return token
        return None

    def _peek_kw(self, *words):
        token = self._peek()
        return token.kind == "ident" and token.value.lower() in words

    def _expect(self, kind, what=None):
        token = self._next()
        if token.kind != kind:
            got = f"{token.value!r}" if token.value is not None else token.kind
            raise ValueError(f"expected {what or kind}, got {got}")
        return token

    def parse(self):
        node = self._parse_or()
        token = self._peek()
        if token.kind != "eof":
            raise ValueError(f"unexpected token {token.value!r}")
        return node

    def _parse_or(self):
        node = self._parse_and()
        while self._accept_kw("or"):
            node = _Or(node, self._parse_and())
        return node

    def _parse_and(self):
        node = self._parse_not()
        while self._accept_kw("and"):
            node = _And(node, self._parse_not())
        return node

    def _parse_not(self):
        if self._accept_kw("not"):
            return _Not(self._parse_not())
        return self._parse_comparison()

    def _parse_comparison(self):
        left = self._parse_operand()
        token = self._peek()

        if (
            token.kind == "eof"
            or token.kind in ("rparen", "rbracket", "comma")
            or self._peek_kw("and", "or")
        ):
            return left

        negate = False
        if self._accept_kw("not"):
            negate = True
            token = self._peek()

        if self._accept_kw("is"):
            not_flag = bool(self._accept_kw("not"))
            if self._accept_kw("null"):
                return _IsNull(left, not_flag)
            if self._accept_kw("empty"):
                return _IsEmpty(left, not_flag)
            if self._accept_kw("defined", "exists"):
                return _IsDefined(left, not_flag)
            raise ValueError(
                f"expected null/empty/defined after 'is', got {self._peek().value!r}"
            )

        if token.kind == "op":
            self._next()
            return _Compare(left, token.value, self._parse_operand())

        if self._accept_kw("contains"):
            return _Contains(left, self._parse_operand(), negate)
        if self._accept_kw("in"):
            return _In(left, self._parse_in_target(), negate)
        if self._accept_kw("matches"):
            return _Matches(left, self._parse_operand(), negate)
        if self._accept_kw("starts"):
            self._expect_word("with")
            return _StartsWith(left, self._parse_operand(), negate)
        if self._accept_kw("ends"):
            self._expect_word("with")
            return _EndsWith(left, self._parse_operand(), negate)
        if self._accept_kw("defined", "exists"):
            return _IsDefined(left, negate)

        if negate:
            raise ValueError(
                f"expected an operator after 'not', got {self._peek().value!r}"
            )
        raise ValueError(f"expected an operator, got {token.value!r}")

    def _expect_word(self, word):
        token = self._next()
        if not (token.kind == "ident" and token.value.lower() == word):
            raise ValueError(f"expected {word!r}, got {token.value!r}")
        return token

    def _parse_in_target(self):
        if self._peek().kind == "lbracket":
            return self._parse_operand()
        if self._peek().kind == "lparen":
            self._next()
            items = [self._parse_operand()]
            while self._accept("comma"):
                items.append(self._parse_operand())
            self._expect("rparen", "')'")
            return _List(items)
        return self._parse_operand()

    def _parse_operand(self):
        token = self._next()
        if token.kind == "number":
            return _Literal(_parse_number(token.value))
        if token.kind == "string":
            return _Literal(_decode_string(token.value))
        if token.kind == "lparen":
            node = self._parse_or()
            self._expect("rparen", "')'")
            return node
        if token.kind == "lbracket":
            items = []
            if self._peek().kind != "rbracket":
                while True:
                    items.append(self._parse_operand())
                    if not self._accept("comma"):
                        break
            self._expect("rbracket", "']'")
            return _List(items)
        if token.kind == "ident":
            lower = token.value.lower()
            if lower == "true":
                return _Literal(True)
            if lower == "false":
                return _Literal(False)
            if lower in ("null", "none", "nil"):
                return _Literal(None)

            path = [token.value]
            original = token.value
            while True:
                if self._accept("dot"):
                    name = self._next()
                    if name.kind != "ident":
                        raise ValueError(
                            f"expected a field name after '.', got {name.value!r}"
                        )
                    path.append(name.value)
                    original += "." + name.value
                elif self._peek().kind == "lbracket":
                    self._next()
                    index = self._next()
                    if index.kind != "number" or "." in index.value:
                        raise ValueError("list index must be an integer")
                    self._expect("rbracket", "']'")
                    path.append(int(index.value))
                    original += "[" + index.value + "]"
                else:
                    break
            return _Field(path, original)
        raise ValueError(f"expected a value, got {token.value!r}")


class _Literal:
    def __init__(self, value):
        self.value = value

    def test(self, record):
        return self.value


class _List:
    def __init__(self, items):
        self.items = items

    def test(self, record):
        return [item.test(record) for item in self.items]


class _Field:
    def __init__(self, path, original):
        self.path = path
        self.original = original

    def test(self, record):
        current = record
        for segment in self.path:
            if isinstance(segment, int):
                if isinstance(current, (list, tuple)) and -len(current) <= segment < len(current):
                    current = current[segment]
                else:
                    return _MISSING
            elif isinstance(current, Mapping) and segment in current:
                current = current[segment]
            else:
                return _MISSING
        return current


def _as_value(node, record, fallback=False):
    value = node.test(record)
    if fallback and isinstance(node, _Field) and value is _MISSING:
        return node.original
    return value


class _Compare:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def test(self, record):
        left = _as_value(self.left, record)
        right = _as_value(self.right, record, fallback=True)
        if left is _MISSING or right is _MISSING:
            return False
        if self.op in ("==", "="):
            return _equal(left, right)
        if self.op == "!=":
            return not _equal(left, right)
        return _ordered_compare(left, right, self.op)


class _Contains:
    def __init__(self, left, right, negate=False):
        self.left = left
        self.right = right
        self.negate = negate

    def test(self, record):
        left = _as_value(self.left, record)
        right = _as_value(self.right, record, fallback=True)
        if left is _MISSING or right is _MISSING or left is None or right is None:
            result = False
        elif isinstance(left, str):
            result = isinstance(right, str) and right in left
        elif isinstance(left, (list, tuple, set, frozenset)):
            result = right in left
        elif isinstance(left, Mapping):
            result = right in left
        else:
            result = False
        return result if not self.negate else not result


class _In:
    def __init__(self, left, right, negate=False):
        self.left = left
        self.right = right
        self.negate = negate

    def test(self, record):
        left = _as_value(self.left, record)
        right = _as_value(self.right, record, fallback=True)
        if left is _MISSING or right is _MISSING or right is None:
            result = False
        elif isinstance(right, str):
            result = isinstance(left, str) and left in right
        elif hasattr(right, "__contains__"):
            result = left in right
        else:
            result = False
        return result if not self.negate else not result


class _Matches:
    def __init__(self, left, right, negate=False):
        self.left = left
        self.right = right
        self.negate = negate

    def test(self, record):
        left = _as_value(self.left, record)
        right = _as_value(self.right, record, fallback=True)
        result = False
        if left is not _MISSING and right is not _MISSING:
            if isinstance(left, str) and isinstance(right, str):
                try:
                    result = re.search(right, left) is not None
                except re.error:
                    result = False
        return result if not self.negate else not result


class _StartsWith:
    def __init__(self, left, right, negate=False):
        self.left = left
        self.right = right
        self.negate = negate

    def test(self, record):
        left = _as_value(self.left, record)
        right = _as_value(self.right, record, fallback=True)
        result = (
            left is not _MISSING
            and right is not _MISSING
            and isinstance(left, str)
            and isinstance(right, str)
            and left.startswith(right)
        )
        return result if not self.negate else not result


class _EndsWith:
    def __init__(self, left, right, negate=False):
        self.left = left
        self.right = right
        self.negate = negate

    def test(self, record):
        left = _as_value(self.left, record)
        right = _as_value(self.right, record, fallback=True)
        result = (
            left is not _MISSING
            and right is not _MISSING
            and isinstance(left, str)
            and isinstance(right, str)
            and left.endswith(right)
        )
        return result if not self.negate else not result


class _IsNull:
    def __init__(self, node, negated=False):
        self.node = node
        self.negated = negated

    def test(self, record):
        value = self.node.test(record)
        result = value is None or value is _MISSING
        return result if not self.negated else not result


class _IsEmpty:
    def __init__(self, node, negated=False):
        self.node = node
        self.negated = negated

    def test(self, record):
        value = self.node.test(record)
        result = (
            value is None
            or value is _MISSING
            or (hasattr(value, "__len__") and len(value) == 0)
        )
        return result if not self.negated else not result


class _IsDefined:
    def __init__(self, node, negated=False):
        self.node = node
        self.negated = negated

    def test(self, record):
        result = self.node.test(record) is not _MISSING
        return result if not self.negated else not result


class _Not:
    def __init__(self, node):
        self.node = node

    def test(self, record):
        return not bool(self.node.test(record))


class _And:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def test(self, record):
        return bool(self.left.test(record)) and bool(self.right.test(record))


class _Or:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def test(self, record):
        return bool(self.left.test(record)) or bool(self.right.test(record))


def evaluate(expression, record):
    """Return True if `record` matches `expression`, else False."""
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    return bool(_Parser(expression).parse().test(record))
