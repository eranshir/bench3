"""Pre-flight checks run before an order is priced."""
from . import fx
from .errors import ValidationError
from .money import CURRENCY_DECIMALS
from .tax import RATES as TAX_RATES


def check_currency(currency):
    if currency not in CURRENCY_DECIMALS:
        raise ValidationError(f"unsupported currency {currency!r}")
    if currency not in fx.RATES:
        raise ValidationError(f"no fx rate configured for {currency!r}")
    return True


def check_region(region):
    if region not in TAX_RATES:
        raise ValidationError(f"unsupported region {region!r}")
    return True


def check_line(line, catalog, currency):
    product = catalog.get(line.sku)
    if not product.sellable:
        raise ValidationError(f"{line.sku} is not sellable")
    if currency not in product.prices:
        raise ValidationError(f"{line.sku} has no {currency} price")
    if line.quantity <= 0:
        raise ValidationError(f"{line.sku}: quantity must be positive")
    return True


def check_order(order, catalog):
    check_currency(order.currency)
    check_region(order.region)
    for line in order.lines:
        check_line(line, catalog, order.currency)
    return True


def check_all(orders, catalog):
    problems = []
    for order in orders:
        try:
            check_order(order, catalog)
        except ValidationError as exc:
            problems.append((order.order_id, str(exc)))
    return problems
