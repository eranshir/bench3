import re


def parse_duration(text):
    """Parse a duration string like '1h30m' into total seconds."""
    cleaned = re.sub(r"\s+", "", text).lower()
    if not cleaned:
        raise ValueError(f"invalid duration: {text!r}")

    unit_seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    total = 0
    i = 0
    while i < len(cleaned):
        j = i
        while j < len(cleaned) and cleaned[j].isdigit():
            j += 1
        if j == i or j >= len(cleaned) or cleaned[j] not in unit_seconds:
            raise ValueError(f"invalid duration: {text!r}")
        total += int(cleaned[i:j]) * unit_seconds[cleaned[j]]
        i = j + 1
    return total
