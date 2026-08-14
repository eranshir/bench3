"""A small CSV-ish parser. The current implementation is naive and wrong on
standard CSV edge cases."""


def parse_rows(text, delimiter=','):
    """Parse text into a list of rows (each a list of fields).

    Must handle: quoted fields containing the delimiter, quoted fields
    containing newlines, escaped quotes ("" inside a quoted field), empty
    fields, and trailing newlines. Returns a list of lists of str."""
    rows = []
    for line in text.strip().split('\n'):
        # BUG 1: naive split breaks quoted commas
        # BUG 2: no multi-line quoted fields
        # BUG 3: no escape handling for ""
        # BUG 4: trailing empty fields dropped by split
        rows.append(line.split(delimiter))
    return rows
