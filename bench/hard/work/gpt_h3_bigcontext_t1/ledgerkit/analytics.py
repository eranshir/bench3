"""Derived figures the finance team asks for alongside the totals."""
from decimal import Decimal

from . import fx, pricing
from .money import Money


def average_order_value(orders, catalog, tenant):
    """Mean order total in the tenant's reporting currency, unrounded."""
    if not orders:
        return Money.zero(tenant.reporting_currency)
    acc = Money.zero(tenant.reporting_currency)
    for order in orders:
        total = pricing.order_total(order, catalog, tenant)
        acc = acc + fx.convert(total, tenant.reporting_currency)
    return acc * (Decimal("1") / Decimal(len(orders)))


def largest_order(orders, catalog, tenant):
    """The order with the highest converted total."""
    best, best_value = None, None
    for order in orders:
        value = fx.convert(pricing.order_total(order, catalog, tenant),
                           tenant.reporting_currency)
        if best_value is None or best_value < value:
            best, best_value = order, value
    return best


def units_sold(orders):
    counts = {}
    for order in orders:
        for line in order.lines:
            counts[line.sku] = counts.get(line.sku, 0) + line.quantity
    return counts


def discount_ratio(orders, catalog, tenant):
    """Total discount as a fraction of total subtotal, in order currencies."""
    subtotals, discounts = {}, {}
    for order in orders:
        sub = pricing.order_subtotal(order, catalog)
        dis = pricing.order_discount(order, catalog, tenant)
        ccy = order.currency
        subtotals[ccy] = subtotals.get(ccy, Money.zero(ccy)) + sub
        discounts[ccy] = discounts.get(ccy, Money.zero(ccy)) + dis
    out = {}
    for ccy, sub in subtotals.items():
        out[ccy] = (discounts[ccy].amount / sub.amount) if sub.amount else \
            Decimal("0")
    return out
