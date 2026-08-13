"""Orders and order lines."""
from .errors import ValidationError


class OrderLine:
    __slots__ = ("sku", "quantity")

    def __init__(self, sku, quantity):
        if quantity <= 0:
            raise ValidationError(f"quantity must be positive, got {quantity}")
        self.sku = sku
        self.quantity = quantity

    def __repr__(self):
        return f"OrderLine({self.sku!r}, {self.quantity})"


class Order:
    __slots__ = ("order_id", "tenant_id", "currency", "region", "lines",
                 "placed_at")

    def __init__(self, order_id, tenant_id, currency, region, lines,
                 placed_at):
        if not lines:
            raise ValidationError(f"order {order_id} has no lines")
        self.order_id = order_id
        self.tenant_id = tenant_id
        self.currency = currency
        self.region = region
        self.lines = list(lines)
        self.placed_at = placed_at

    def quantity(self):
        return sum(line.quantity for line in self.lines)

    def skus(self):
        return [line.sku for line in self.lines]

    def __repr__(self):
        return (f"Order({self.order_id!r}, tenant={self.tenant_id!r}, "
                f"{self.currency}, {len(self.lines)} lines)")
