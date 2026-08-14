"""Reference fix: a real CSV state machine."""


def parse_rows(text, delimiter=','):
    """Parse CSV text handling quotes, escaped quotes, embedded newlines,
    empty fields, and trailing/blank lines."""
    rows = []
    row = []
    field = []
    in_quotes = False
    any_content = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"'); i += 2; continue
                in_quotes = False; i += 1; continue
            field.append(ch); i += 1; continue
        if ch == '"':
            in_quotes = True; any_content = True; i += 1; continue
        if ch == delimiter:
            row.append(''.join(field)); field = []; any_content = True; i += 1; continue
        if ch == '\n':
            row.append(''.join(field)); field = []
            if any_content or len(row) != 1 or row[0] != '':
                rows.append(row)
            row = []; any_content = False; i += 1; continue
        if ch == '\r':
            i += 1; continue
        field.append(ch); any_content = True; i += 1
    if in_quotes:
        raise ValueError('unterminated quoted field')
    if field or row or any_content:
        row.append(''.join(field))
        rows.append(row)
    return rows
