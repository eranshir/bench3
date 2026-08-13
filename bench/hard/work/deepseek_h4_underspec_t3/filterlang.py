"""Filter expression language for the segmentation service.

A record is a plain dict. `evaluate` decides whether a record matches an
expression written by a non-engineer in the segment builder UI.

Supported syntax (there is no formal grammar; this is the language accepted):

  * Comparisons:  ==, !=, <>, <, <=, >, >=, =  (single = means equality)
  * Membership:   <field> contains <value>, <value> in <field>,
                  <value> not in <field>
  * Null checks:  <field> is null, <field> is not null  (also none/None-like)
  * Truth checks: <field> is true / is false / is not true / is not false
  * Regex match:  <field> matches <pattern>, <field> =~ <pattern>
  * Boolean:      and, or, not, with parentheses for grouping
  * Literals:     numbers (int/float), 'single' or "double" quoted strings,
                  true/false, null/none
  * Field names:  bare identifiers, with dots for nested dicts (a.b.c)

Field values that are absent, or of the wrong type for an operation, simply
do not match (they never crash a segment evaluation).  Missing fields read
as null.  Invalid expressions raise ValueError.
"""

import re


__all__ = ["evaluate"]


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
    (?P<WS>\s+)
  | (?P<NUMBER>\d+\.\d+|\d+)
  | (?P<STRING>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")
  | (?P<OP><=|>=|==|!=|<>|=~|~=|<|>|=|-|\+)
  | (?P<LPAREN>\()
  | (?P<RPAREN>\))
  | (?P<LBRACKET>\[)
  | (?P<RBRACKET>\])
  | (?P<COMMA>,)
  | (?P<IDENT>[A-Za-z_][A-Za-z0-9_.]*)
    """,
    re.VERBOSE,
)

_KEYWORDS = frozenset(
    {
        "and",
        "or",
        "not",
        "in",
        "is",
        "contains",
        "matches",
        "true",
        "false",
        "null",
        "none",
    }
)

_ESCAPES = {
    "\\": "\\",
    "'": "'",
    '"': '"',
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
}


def _tokenize(text):
    """Split `text` into a list of (kind, value) tokens."""
    tokens = []
    pos = 0
    for match in _TOKEN_RE.finditer(text):
        if match.start() != pos:
            raise ValueError(
                f"unexpected character {text[pos]!r} at position {pos} "
                f"in expression {text!r}"
            )
        pos = match.end()
        kind = match.lastgroup
        if kind == "WS":
            continue
        value = match.group()
        if kind == "NUMBER":
            value = float(value) if "." in value else int(value)
        elif kind == "STRING":
            value = _unescape(value[1:-1])
        tokens.append((kind, value))
    if pos != len(text):
        raise ValueError(
            f"unexpected character {text[pos]!r} at position {pos} "
            f"in expression {text!r}"
        )
    return tokens


def _unescape(raw):
    out = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\\":
            if i + 1 >= len(raw):
                raise ValueError("expression ends with a dangling backslash")
            out.append(_ESCAPES.get(raw[i + 1], raw[i + 1]))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# Parser: builds a tiny AST
# ---------------------------------------------------------------------------


class _Literal:
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value


class _List:
    __slots__ = ("items",)

    def __init__(self, items):
        self.items = items


class _Field:
    __slots__ = ("path",)

    def __init__(self, path):
        self.path = path


class _Not:
    __slots__ = ("operand",)

    def __init__(self, operand):
        self.operand = operand


class _And:
    __slots__ = ("left", "right")

    def __init__(self, left, right):
        self.left = left
        self.right = right


class _Or:
    __slots__ = ("left", "right")

    def __init__(self, left, right):
        self.left = left
        self.right = right


class _Compare:
    __slots__ = ("left", "op", "right")

    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class _Chain:
    """Chained comparison such as `10 < age < 30`."""

    __slots__ = ("operands", "ops")

    def __init__(self, operands, ops):
        self.operands = operands
        self.ops = ops


class _UnaryNeg:
    __slots__ = ("operand",)

    def __init__(self, operand):
        self.operand = operand


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -- token helpers ------------------------------------------------------

    def _peek(self, offset=0):
        index = self.pos + offset
        if index >= len(self.tokens):
            return None
        return self.tokens[index]

    def _next(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _keyword(self, offset=0):
        token = self._peek(offset)
        if token is not None and token[0] == "IDENT":
            return token[1].lower()
        return None

    def _match_keyword(self, word):
        if self._keyword() == word:
            self._next()
            return True
        return False

    def _expect(self, kind, what):
        token = self._peek()
        if token is None or token[0] != kind:
            self._error(what)
        return self._next()

    def _error(self, what):
        token = self._peek()
        if token is None:
            raise ValueError(f"unexpected end of expression while expecting {what}")
        raise ValueError(f"expected {what} but found {token[1]!r}")

    def _comparison_op(self):
        """Return the next comparison operator, or None if there isn't one."""
        token = self._peek()
        if token is None:
            return None
        kind, value = token
        if kind == "OP":
            return {
                "=": "==",
                "<>": "!=",
                "=~": "matches",
                "~=": "matches",
            }.get(value, value)
        if kind == "IDENT":
            word = value.lower()
            if word == "contains":
                return "contains"
            if word == "in":
                return "in"
            if word == "matches":
                return "matches"
            if word == "is":
                return "is not" if self._keyword(1) == "not" else "is"
            if word == "not" and self._keyword(1) == "in":
                return "not in"
        return None

    # -- grammar ------------------------------------------------------------

    def parse(self):
        if not self.tokens:
            raise ValueError("expression is empty")
        node = self._or()
        if self.pos != len(self.tokens):
            self._error("end of expression")
        return node

    def _or(self):
        node = self._and()
        while self._match_keyword("or"):
            node = _Or(node, self._and())
        return node

    def _and(self):
        node = self._not()
        while self._match_keyword("and"):
            node = _And(node, self._not())
        return node

    def _not(self):
        if self._match_keyword("not"):
            return _Not(self._not())
        return self._comparison()

    def _comparison(self):
        left = self._unary()
        ops = []
        while True:
            op = self._comparison_op()
            if op is None:
                break
            self._next()  # first token of the operator
            if op in ("is not", "not in"):
                self._next()  # the "not" / "in" part
            right = self._unary()
            ops.append((op, right))
        if not ops:
            return left
        if len(ops) == 1:
            return _Compare(left, ops[0][0], ops[0][1])
        operands = [left] + [right for _, right in ops]
        return _Chain(operands, [op for op, _ in ops])

    def _unary(self):
        token = self._peek()
        if token is not None and token[0] == "OP" and token[1] in ("-", "+"):
            self._next()
            return _UnaryNeg(self._unary()) if token[1] == "-" else self._unary()
        return self._atom()

    def _atom(self):
        token = self._peek()
        if token is None:
            self._error("a value")
        kind, value = token
        if kind == "NUMBER" or kind == "STRING":
            self._next()
            return _Literal(value)
        if kind == "LPAREN":
            self._next()
            node = self._or()
            self._expect("RPAREN", "')'")
            return node
        if kind == "LBRACKET":
            return self._list_literal()
        if kind == "IDENT":
            self._next()
            word = value.lower()
            if word == "true":
                return _Literal(True)
            if word == "false":
                return _Literal(False)
            if word in ("null", "none"):
                return _Literal(None)
            if word in _KEYWORDS:
                raise ValueError(
                    f"keyword {value!r} cannot be used as a field name "
                    f"in expression"
                )
            return _Field(value)
        self._error("a value")

    def _list_literal(self):
        self._next()  # '['
        items = []
        if self._peek() is not None and self._peek()[0] == "RBRACKET":
            self._next()
            return _List(items)
        while True:
            items.append(self._or())
            token = self._peek()
            if token is None or token[0] != "COMMA":
                break
            self._next()
        self._expect("RBRACKET", "']'")
        return _List(items)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def evaluate(expression, record):
    """Return True if `record` matches `expression`, else False."""
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    if not isinstance(record, dict):
        raise TypeError("record must be a dict")
    parser = _Parser(_tokenize(expression))
    return bool(_eval(parser.parse(), record))


def _eval(node, record):
    if isinstance(node, _Literal):
        return node.value
    if isinstance(node, _List):
        return [_eval(item, record) for item in node.items]
    if isinstance(node, _Field):
        return _resolve(record, node.path)
    if isinstance(node, _Not):
        return not bool(_eval(node.operand, record))
    if isinstance(node, _And):
        return _eval(node.left, record) and _eval(node.right, record)
    if isinstance(node, _Or):
        return _eval(node.left, record) or _eval(node.right, record)
    if isinstance(node, _Compare):
        return _compare(
            _eval(node.left, record), node.op, _eval(node.right, record)
        )
    if isinstance(node, _Chain):
        first = _eval(node.operands[0], record)
        for op, operand in zip(node.ops, node.operands[1:]):
            value = _eval(operand, record)
            if not _compare(first, op, value):
                return False
            first = value
        return True
    if isinstance(node, _UnaryNeg):
        value = _eval(node.operand, record)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return -value
        return None
    raise TypeError(f"unknown node {node!r}")


def _resolve(record, path):
    """Resolve a field path, reading missing values as null."""
    if path in record:
        return record[path]
    value = record
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _compare(left, op, right):
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    if op in ("<", "<=", ">", ">="):
        try:
            return {
                "<": left < right,
                "<=": left <= right,
                ">": left > right,
                ">=": left >= right,
            }[op]
        except TypeError:
            return False
    if op == "contains":
        return _contains(left, right)
    if op == "in":
        return _contains(right, left)
    if op == "not in":
        return not _contains(right, left)
    if op == "is":
        return _is(left, right)
    if op == "is not":
        return not _is(left, right)
    if op == "matches":
        return _matches(left, right)
    raise ValueError(f"unknown operator {op!r}")


def _contains(container, item):
    """`item` inside `container`; never raises on odd data types."""
    if container is None:
        return False
    if isinstance(container, str):
        return str(item) in container
    if isinstance(container, dict):
        try:
            return item in container
        except TypeError:
            return False
    try:
        return item in container
    except TypeError:
        return False


def _is(left, right):
    """Semantics for `is`/`is not`: identity for null/booleans, else ==."""
    if right is None:
        return left is None
    if right is True:
        return left is True
    if right is False:
        return left is False
    return left == right


def _matches(value, pattern):
    """Regex search; a bad pattern simply doesn't match."""
    try:
        return re.search(str(pattern), str(value)) is not None
    except (re.error, TypeError):
        return False
