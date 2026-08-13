"""Human-readable rendering of money and report rows."""
from .money import decimals_for

SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "CHF": "CHF ",
    "JPY": "¥",
}


def symbol(currency):
    return SYMBOLS.get(currency, currency + " ")


def format_money(money, with_symbol=True):
    """Render a Money at its currency's natural precision."""
    places = decimals_for(money.currency)
    text = f"{money.amount:,.{places}f}"
    return f"{symbol(money.currency)}{text}" if with_symbol else text


def format_row(row):
    return (f"{row['order_id']:<8} {row['placed_at']:<12} "
            f"{row['currency']:<4} {row['region']:<6} "
            f"{format_money(row['total']):>14} "
            f"{format_money(row['reported']):>14}")


def header():
    return (f"{'order':<8} {'placed':<12} {'ccy':<4} {'region':<6} "
            f"{'total':>14} {'reported':>14}")


def rule(width=64):
    return "-" * width
