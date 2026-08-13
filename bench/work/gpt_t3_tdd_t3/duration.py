import re


_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 24 * 60 * 60,
}

_DURATION_RE = re.compile(r"(?:\d+[smhd])+", re.IGNORECASE)
_PART_RE = re.compile(r"(\d+)([smhd])", re.IGNORECASE)


def parse_duration(text):
    """Parse a duration string like '1h30m' into total seconds."""
    compact = re.sub(r"\s+", "", text)
    if not compact or _DURATION_RE.fullmatch(compact) is None:
        raise ValueError(f"invalid duration: {text!r}")

    return sum(
        int(amount) * _UNIT_SECONDS[unit.lower()]
        for amount, unit in _PART_RE.findall(compact)
    )
