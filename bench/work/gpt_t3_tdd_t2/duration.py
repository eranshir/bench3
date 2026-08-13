import re


_DURATION_PART = re.compile(r"(\d+)\s*([smhd])", re.IGNORECASE)
_SECONDS_PER_UNIT = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 24 * 60 * 60,
}


def parse_duration(text):
    """Parse a duration string like '1h30m' into total seconds."""
    if not isinstance(text, str):
        raise ValueError("duration must be a string")

    position = 0
    total = 0
    found_part = False

    while position < len(text):
        # Whitespace is allowed before, after, and between duration parts.
        while position < len(text) and text[position].isspace():
            position += 1

        if position == len(text):
            break

        match = _DURATION_PART.match(text, position)
        if match is None:
            raise ValueError(f"invalid duration: {text!r}")

        amount, unit = match.groups()
        total += int(amount) * _SECONDS_PER_UNIT[unit.lower()]
        found_part = True
        position = match.end()

    if not found_part:
        raise ValueError(f"invalid duration: {text!r}")

    return total
