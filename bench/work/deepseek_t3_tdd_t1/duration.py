import re


_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_TOKEN = re.compile(r"(\d+)([smhd])")


def parse_duration(text):
    """Parse a duration string like '1h30m' into total seconds."""
    if not isinstance(text, str):
        raise ValueError("duration must be a string")
    compact = "".join(text.split()).lower()
    if not compact:
        raise ValueError("empty duration")
    total = 0
    pos = 0
    while pos < len(compact):
        match = _TOKEN.match(compact, pos)
        if match is None:
            raise ValueError(f"invalid duration: {text!r}")
        value = int(match.group(1))
        total += value * _UNIT_SECONDS[match.group(2)]
        pos = match.end()
    return total
