"""In-memory order store.

Stands in for the orders table. The settlement report reads through this.
"""
from .errors import TenantError
from .orders import Order, OrderLine

ORDERS = [
    Order("A-1001", "acme", "USD", "us-ca",
          [OrderLine("WIDGET-S", 4), OrderLine("GADGET", 1)],
          "2026-05-02"),
    Order("A-1002", "acme", "USD", "us-ca",
          [OrderLine("SUPPORT-YR", 1)], "2026-05-06"),
    Order("A-1003", "acme", "EUR", "eu-de",
          [OrderLine("WIDGET-L", 3), OrderLine("SPROCKET", 10)],
          "2026-05-11"),
    Order("A-1004", "acme", "GBP", "uk",
          [OrderLine("GADGET", 2)], "2026-05-19"),

    Order("B-2001", "borealis", "EUR", "eu-de",
          [OrderLine("WIDGET-L", 12)], "2026-05-03"),
    Order("B-2002", "borealis", "EUR", "eu-de",
          [OrderLine("SPROCKET", 40), OrderLine("WIDGET-S", 6)],
          "2026-05-14"),
    Order("B-2003", "borealis", "USD", "us-ny",
          [OrderLine("SUPPORT-YR", 2)], "2026-05-21"),

    Order("K-3001", "kitsune", "JPY", "jp",
          [OrderLine("GADGET", 3)], "2026-05-04"),
    Order("K-3002", "kitsune", "JPY", "jp",
          [OrderLine("WIDGET-S", 20)], "2026-05-09"),
    Order("K-3003", "kitsune", "USD", "us-ca",
          [OrderLine("WIDGET-L", 5)], "2026-05-17"),

    Order("N-4001", "northwind", "GBP", "uk",
          [OrderLine("SUPPORT-YR", 1), OrderLine("SPROCKET", 8)],
          "2026-05-05"),
    Order("N-4002", "northwind", "GBP", "uk",
          [OrderLine("WIDGET-S", 15)], "2026-05-12"),
    Order("N-4003", "northwind", "EUR", "ch",
          [OrderLine("GADGET", 1)], "2026-05-23"),
    Order("N-4004", "northwind", "USD", "us-or",
          [OrderLine("WIDGET-L", 2)], "2026-05-27"),
]


def for_tenant(tenant_id):
    """Every order belonging to `tenant_id`, in placement order."""
    found = [o for o in ORDERS if o.tenant_id == tenant_id]
    if not found:
        raise TenantError(f"no orders for tenant {tenant_id!r}")
    return found


def all_orders():
    return list(ORDERS)


def get(order_id):
    for order in ORDERS:
        if order.order_id == order_id:
            return order
    raise KeyError(order_id)


def count():
    return len(ORDERS)
