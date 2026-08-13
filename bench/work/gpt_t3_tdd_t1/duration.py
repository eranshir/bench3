import re


_COMPONENT_RE = re.compile(r"(\d+)\s*([dhms])", re.IGNORECASE)
_SECONDS_PER_UNIT = {
    "d": 24 * 60 * 60,
    "h": 60 * 60,
    "m": 60,
    "s": 1,
}


def parse_duration(text):
    """Parse a duration string like '1h30m' into total seconds."""
    if not isinstance(text, str):
        raise ValueError("duration must be a string")

    position = 0
    total = 0
    matched_component = False

    for match in _COMPONENT_RE.finditer(text):
        if text[position:match.start()].strip():
            raise ValueError(f"invalid duration: {text!r}")

        value, unit = match.groups()
        total += int(value) * _SECONDS_PER_UNIT[unit.lower()]
        position = match.end()
        matched_component = True

    if not matched_component or text[position:].strip():
        raise ValueError(f"invalid duration: {text!r}")

    return total
