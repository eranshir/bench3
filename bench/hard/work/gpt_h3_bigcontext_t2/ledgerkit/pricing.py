"""Order pricing.

The pricing chain, in order:

    subtotal  = sum of unit price * quantity, in the order's currency
    discount  = the tenant's discount rules applied to the subtotal
    taxable   = subtotal - discount
    tax       = taxable * the region's rate
    total     = taxable + tax

The total is rounded once, at the end, to the order currency's minor units.
Nothing upstream of that rounds, so a long order does not accumulate
per-line rounding drift.
"""
from . import tax as tax_module
from .discounts import total_discount
from .money import Money, total as sum_money


def line_subtotal(line, catalog, currency):
    """Unit price times quantity, in `currency`."""
    unit = catalog.price(line.sku, currency)
    return unit * line.quantity


def order_subtotal(order, catalog):
    """Sum of the order's line subtotals, before discount and tax."""
    return sum_money(
        (line_subtotal(line, catalog, order.currency) for line in order.lines),
        order.currency)


def order_discount(order, catalog, tenant):
    """The discount this tenant's rules give on this order."""
    return total_discount(tenant.discount_rules, order_subtotal(order,
                                                                catalog))


def order_tax(order, catalog, tenant):
    """Tax due on this order."""
    subtotal = order_subtotal(order, catalog)
    discount = total_discount(tenant.discount_rules, subtotal)
    taxable = subtotal - discount
    return tax_module.tax_for_region(taxable, order.region)


def order_total(order, catalog, tenant):
    """What the customer pays, rounded to the order currency."""
    subtotal = order_subtotal(order, catalog)
    discount = total_discount(tenant.discount_rules, subtotal)
    taxable = subtotal - discount
    tax = tax_module.tax_for_region(taxable, order.region)
    return (taxable + tax).quantized()


def price_breakdown(order, catalog, tenant):
    """Every component of the price, for the invoice renderer."""
    subtotal = order_subtotal(order, catalog)
    discount = total_discount(tenant.discount_rules, subtotal)
    taxable = subtotal - discount
    tax = tax_module.tax_for_region(taxable, order.region)
    return {
        "subtotal": subtotal,
        "discount": discount,
        "taxable": taxable,
        "tax": tax,
        "total": order_total(order, catalog, tenant),
    }


def unit_price(sku, currency, catalog):
    return catalog.price(sku, currency)


def zero_for(order):
    return Money.zero(order.currency)
