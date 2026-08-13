"""Currency conversion.

RATES is quoted as *units of the currency per one USD*. USD is the base and
is therefore exactly 1. To read it: one USD buys 0.92 EUR, or 157 JPY.

Rates are a static table here. In the real service they come from the
treasury feed, refreshed hourly; the shape of the table is the same.
"""
from decimal import Decimal

from .errors import CurrencyError
from .money import Money

BASE = "USD"

RATES = {
    "USD": Decimal("1"),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.79"),
    "CHF": Decimal("0.88"),
    "JPY": Decimal("157"),
}


def rate_for(currency):
    """Units of `currency` per one USD."""
    try:
        return RATES[currency]
    except KeyError:
        raise CurrencyError(f"no fx rate for {currency!r}") from None


def cross_rate(from_currency, to_currency):
    """Multiplier that takes an amount in `from_currency` to `to_currency`."""
    source = rate_for(from_currency)
    target = rate_for(to_currency)
    return source / target


def convert(money, to_currency):
    """Convert `money` into `to_currency`. Unrounded on purpose.

    Callers decide when to round, because rounding at every hop compounds
    error across a multi-order report.
    """
    if money.currency == to_currency:
        return money
    return Money(money.amount * cross_rate(money.currency, to_currency),
                 to_currency)


def to_base(money):
    """Convert into the base currency (USD)."""
    return convert(money, BASE)


def supported():
    return sorted(RATES)
