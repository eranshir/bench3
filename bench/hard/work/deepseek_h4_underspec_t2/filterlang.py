"""Filter expression language for the segmentation service.

A record is a plain dict. `evaluate` decides whether a record matches an
expression written by a non-engineer in the segment builder UI.

The original ticket defines no formal grammar, so the language is a small,
permissive subset that covers the ticket's cases and the natural ways an
author extends them:

    Logic:          and, or, not (any casing, usual precedence
                    not > and > or), plus parentheses for grouping.
    Comparisons:    ==, !=, <, <=, >, >=  (a single ``=`` is accepted as
                    an alias for ``==``).
    Membership:     ``field contains value`` -- substring match for
                    strings, item membership for lists/tuples/sets, key
                    lookup for dicts.  ``value in list`` is the same
                    operation with the operands reversed.
    Values:         numbers (30, 4.5, -2, 1e3), single- or double-quoted
                    strings with backslash escapes, True/False in any
                    casing, and None/null.
    Fields:         bare identifiers, optionally hyphenated or dotted
                    (``user.age`` walks nested dicts).  A field is looked
                    up by exact name first, then case-insensitively; a
                    missing field behaves like None.

Edge-case behavior:
    * Comparisons that don't make sense for the values involved (e.g.
      ``'abc' > 5`` or a missing field compared with ``<``) evaluate to
      False instead of raising, so one bad record can't break a run.
    * Malformed expressions raise ValueError so the segment builder UI
      can flag the problem while the expression is being authored.

Standard library only; no eval()/exec().
"""

import re


_TOKEN_RE = re.compile(
    r"""
      (?P<WS>\s+)
    | (?P<NUM>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)
    | (?P<STR>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")
    | (?P<OP>==|!=|>=|<=|>|<|=)
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<LBRACK>\[)
    | (?P<RBRACK>\])
    | (?P<COMMA>,)
    | (?P<MINUS>-)
    | (?P<IDENT>[^\W\d][\w-]*(?:\.[^\W\d][\w-]*)*)
    | (?P<BAD>.)
    """,
    re.VERBOSE,
)


_KEYWORDS = frozenset({"and", "or", "not", "contains", "in"})

_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "'": "'",
    '"': '"',
    "\\": "\\",
}


class _Token:
    __slots__ = ("kind", "value", "pos")

    def __init__(self, kind, value, pos):
        self.kind = kind
        self.value = value
        self.pos = pos


def _unescape(text):
    def replace(match):
        char = match.group(1)
        return _ESCAPES.get(char, "\\" + char)

    return re.sub(r"\\(.)", replace, text)


def _tokenize(text):
    tokens = []
    pos = 0
    while pos < len(text):
        match = _TOKEN_RE.match(text, pos)
        kind = match.lastgroup if match else None
        if kind is None or kind == "BAD":
            raise ValueError(
                "invalid character %r at position %d in expression %r"
                % (text[pos], pos, text)
            )
        raw = match.group()
        if kind == "WS":
            pos = match.end()
            continue
        if kind == "NUM":
            value = int(raw) if raw.isdigit() else float(raw)
        elif kind == "STR":
            value = _unescape(raw[1:-1])
        else:
            value = raw
        tokens.append(_Token(kind, value, pos))
        pos = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens, record):
        self.tokens = tokens
        self.record = record
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def next_token(self):
        token = self.peek()
        if token is None:
            raise ValueError("unexpected end of expression")
        self.pos += 1
        return token

    def accept(self, kind):
        token = self.peek()
        if token is not None and token.kind == kind:
            self.pos += 1
            return token
        return None

    def accept_keyword(self, word):
        token = self.peek()
        if (
            token is not None
            and token.kind == "IDENT"
            and token.value.lower() == word
        ):
            self.pos += 1
            return True
        return False

    def expect(self, kind):
        token = self.accept(kind)
        if token is None:
            got = self.peek()
            where = got.pos if got else "end of expression"
            raise ValueError("expected %s at position %s" % (kind, where))
        return token

    def parse_or(self):
        value = self.parse_and()
        while self.accept_keyword("or"):
            right = self.parse_and()
            value = bool(value) or bool(right)
        return value

    def parse_and(self):
        value = self.parse_not()
        while self.accept_keyword("and"):
            right = self.parse_not()
            value = bool(value) and bool(right)
        return value

    def parse_not(self):
        if self.accept_keyword("not"):
            return not bool(self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_operand()
        token = self.peek()
        if token is not None and token.kind == "OP":
            op = self.next_token().value
            right = self.parse_operand()
            return self._compare(left, op, right)
        if self.accept_keyword("contains"):
            right = self.parse_operand()
            return self._contains(left, right)
        if self.accept_keyword("in"):
            right = self.parse_operand()
            return self._contains(right, left)
        return left

    def parse_operand(self):
        token = self.peek()
        if token is None:
            raise ValueError("unexpected end of expression")
        if token.kind == "MINUS":
            self.next_token()
            value = self.parse_operand()
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return -value
            raise ValueError(
                "unary '-' may only be applied to a number at position %d"
                % token.pos
            )
        if token.kind == "LPAREN":
            self.next_token()
            value = self.parse_or()
            self.expect("RPAREN")
            return value
        if token.kind == "LBRACK":
            return self.parse_list()
        if token.kind in ("NUM", "STR"):
            self.next_token()
            return token.value
        if token.kind == "IDENT":
            self.next_token()
            lower = token.value.lower()
            if lower == "true":
                return True
            if lower == "false":
                return False
            if lower in ("none", "null"):
                return None
            if lower in _KEYWORDS:
                raise ValueError(
                    "unexpected keyword %r at position %d"
                    % (token.value, token.pos)
                )
            return self.lookup(token.value)
        raise ValueError(
            "unexpected token %r at position %d" % (token.value, token.pos)
        )

    def parse_list(self):
        self.next_token()  # consume '['
        items = []
        if self.accept("RBRACK"):
            return items
        while True:
            items.append(self.parse_or())
            if self.accept("RBRACK"):
                return items
            self.expect("COMMA")

    def lookup(self, name):
        """Resolve a field name against the record.

        Tries the exact name first (which lets a literal key like
        "user.age" win over nested lookup), then falls back to a dotted
        path into nested dicts, matching each path segment
        case-insensitively.  A missing field resolves to None.
        """
        record = self.record
        if name in record:
            return record[name]
        current = record
        for part in name.split("."):
            if not isinstance(current, dict):
                return None
            if part in current:
                current = current[part]
                continue
            fallback = None
            for key, value in current.items():
                if isinstance(key, str) and key.lower() == part.lower():
                    fallback = value
                    break
            if fallback is None:
                return None
            current = fallback
        return current

    @staticmethod
    def _compare(left, op, right):
        if op in ("==", "="):
            return left == right
        if op == "!=":
            return left != right
        # Ordering only makes sense for comparable scalar types; never
        # order booleans (True == 1 in Python, which surprises authors).
        if isinstance(left, bool) or isinstance(right, bool):
            return False
        try:
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            if op == ">=":
                return left >= right
        except TypeError:
            return False
        return False  # pragma: no cover - the tokenizer only emits these ops

    @staticmethod
    def _contains(container, item):
        try:
            return item in container
        except TypeError:
            return False


def evaluate(expression, record):
    """Return True if `record` matches `expression`, else False."""
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    if not isinstance(record, dict):
        raise TypeError("record must be a dict")
    tokens = _tokenize(expression)
    parser = _Parser(tokens, record)
    result = parser.parse_or()
    token = parser.peek()
    if token is not None:
        raise ValueError(
            "unexpected token %r at position %d" % (token.value, token.pos)
        )
    return bool(result)
