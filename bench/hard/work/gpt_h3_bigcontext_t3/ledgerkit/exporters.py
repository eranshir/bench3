"""Report renderers."""
import csv
import io
import json

from .formatting import format_money, format_row, header, rule


def to_text(report):
    lines = [f"{report['name']} ({report['tenant']}) - "
             f"{report['orders']} orders",
             rule(), header(), rule()]
    lines.extend(format_row(row) for row in report["rows"])
    lines.append(rule())
    lines.append(f"{'TOTAL':<8} {format_money(report['total']):>55}")
    return "\n".join(lines)


def to_csv(report):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["order_id", "placed_at", "currency", "region",
                     "total", "reported"])
    for row in report["rows"]:
        writer.writerow([
            row["order_id"], row["placed_at"], row["currency"],
            row["region"],
            format_money(row["total"], with_symbol=False),
            format_money(row["reported"], with_symbol=False),
        ])
    writer.writerow([])
    writer.writerow(["TOTAL", "", report["currency"], "", "",
                     format_money(report["total"], with_symbol=False)])
    return buf.getvalue()


def to_json(report):
    payload = {
        "tenant": report["tenant"],
        "name": report["name"],
        "currency": report["currency"],
        "orders": report["orders"],
        "total": str(report["total"].amount),
        "rows": [
            {
                "order_id": row["order_id"],
                "placed_at": row["placed_at"],
                "currency": row["currency"],
                "region": row["region"],
                "total": str(row["total"].amount),
                "reported": str(row["reported"].amount),
            }
            for row in report["rows"]
        ],
    }
    return json.dumps(payload, indent=2)


FORMATS = {"text": to_text, "csv": to_csv, "json": to_json}


def render(report, fmt="text"):
    try:
        return FORMATS[fmt](report)
    except KeyError:
        raise ValueError(f"unknown format {fmt!r}; "
                         f"try one of {sorted(FORMATS)}") from None
