"""Settlement reporting.

A tenant report converts every order total into the tenant's reporting
currency and sums them. Converted values remain unrounded until presentation,
and the sum is rounded once at the end to the reporting currency's minor
units.
"""

from . import fx, pricing
from .money import Money


def round_for_report(money):
    """Round a reporting figure for presentation and storage."""
    return money.quantized()


def order_row(order, catalog, tenant):
    """One line of the report."""
    total = pricing.order_total(order, catalog, tenant)
    converted = fx.convert(total, tenant.reporting_currency)
    return {
        "order_id": order.order_id,
        "placed_at": order.placed_at,
        "currency": order.currency,
        "region": order.region,
        "total": total,
        "reported": round_for_report(converted),
    }


def tenant_total(tenant, orders, catalog):
    """Total revenue for a tenant, in its reporting currency."""
    acc = Money.zero(tenant.reporting_currency)
    for order in orders:
        total = pricing.order_total(order, catalog, tenant)
        acc = acc + fx.convert(total, tenant.reporting_currency)
    return round_for_report(acc)


def tenant_report(tenant, orders, catalog):
    """Rows plus the tenant total."""
    rows = [order_row(o, catalog, tenant) for o in orders]
    return {
        "tenant": tenant.tenant_id,
        "name": tenant.name,
        "currency": tenant.reporting_currency,
        "orders": len(rows),
        "rows": rows,
        "total": tenant_total(tenant, orders, catalog),
    }


def totals_by_currency(orders, catalog, tenant):
    """Order totals grouped by the currency they were placed in."""
    buckets = {}
    for order in orders:
        total = pricing.order_total(order, catalog, tenant)
        if order.currency in buckets:
            buckets[order.currency] = buckets[order.currency] + total
        else:
            buckets[order.currency] = total
    return buckets
