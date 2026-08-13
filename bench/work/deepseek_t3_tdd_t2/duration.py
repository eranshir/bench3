import re


def parse_duration(text):
    """Parse a duration string like '1h30m' into total seconds."""
    if not isinstance(text, str):
        raise ValueError("duration must be a string")

    cleaned = text.strip().upper()
    if not cleaned or not re.fullmatch(r"(?:\d+[DHMS]\s*)+", cleaned):
        raise ValueError(f"invalid duration: {text!r}")

    units = {"D": 86400, "H": 3600, "M": 60, "S": 1}
    total = 0
    for match in re.finditer(r"(\d+)([DHMS])", cleaned):
        total += int(match.group(1)) * units[match.group(2)]
    return total
