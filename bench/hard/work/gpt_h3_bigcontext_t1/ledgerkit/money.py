"""Money values.

Every amount in the system is a Money: a Decimal paired with an ISO currency
code. Money is immutable; arithmetic returns new instances. Mixing currencies
raises rather than silently coercing.

Currencies differ in how many minor units they have. JPY has none, so a JPY
amount is only well formed when it is a whole number of yen. Anything that
rounds a Money for presentation or storage must respect CURRENCY_DECIMALS
rather than assuming two places.
"""
from decimal import ROUND_HALF_UP, Decimal

from .errors import CurrencyError

CURRENCY_DECIMALS = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "CHF": 2,
    "JPY": 0,
}


def decimals_for(currency):
    """Number of minor-unit digits for `currency`."""
    try:
        return CURRENCY_DECIMALS[currency]
    except KeyError:
        raise CurrencyError(f"unknown currency {currency!r}") from None


def exponent_for(currency):
    """The Decimal exponent to quantize `currency` to, e.g. Decimal('0.01')."""
    places = decimals_for(currency)
    return Decimal(1).scaleb(-places)


class Money:
    """An amount in a single currency."""

    __slots__ = ("amount", "currency")

    def __init__(self, amount, currency):
        if currency not in CURRENCY_DECIMALS:
            raise CurrencyError(f"unknown currency {currency!r}")
        self.amount = amount if isinstance(amount, Decimal) \
            else Decimal(str(amount))
        self.currency = currency

    # -- construction -----------------------------------------------------

    @classmethod
    def zero(cls, currency):
        return cls(Decimal("0"), currency)

    # -- arithmetic -------------------------------------------------------

    def _check(self, other):
        if self.currency != other.currency:
            raise CurrencyError(
                f"cannot combine {self.currency} and {other.currency}")

    def __add__(self, other):
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other):
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor):
        return Money(self.amount * Decimal(str(factor)), self.currency)

    __rmul__ = __mul__

    def __neg__(self):
        return Money(-self.amount, self.currency)

    # -- comparison -------------------------------------------------------

    def __eq__(self, other):
        return (isinstance(other, Money)
                and self.currency == other.currency
                and self.amount == other.amount)

    def __lt__(self, other):
        self._check(other)
        return self.amount < other.amount

    def __le__(self, other):
        self._check(other)
        return self.amount <= other.amount

    def __hash__(self):
        return hash((self.amount, self.currency))

    def __bool__(self):
        return self.amount != 0

    # -- rounding ---------------------------------------------------------

    def quantized(self):
        """Round to this currency's minor units, half away from zero."""
        return Money(
            self.amount.quantize(exponent_for(self.currency),
                                 rounding=ROUND_HALF_UP),
            self.currency)

    def is_quantized(self):
        return self == self.quantized()

    def __repr__(self):
        return f"Money({self.amount}, {self.currency!r})"

    def __str__(self):
        return f"{self.amount} {self.currency}"


def total(items, currency):
    """Sum an iterable of Money, returning zero in `currency` if empty."""
    acc = Money.zero(currency)
    for item in items:
        acc = acc + item
    return acc
