from decimal import Decimal, ROUND_HALF_UP


class Cart:
    def __init__(self, items=None):
        self.items = [] if items is None else items
        self._discount_multiplier = Decimal("1")

    def add(self, name, price, qty=1):
        self.items.append({"name": name, "price": price, "qty": qty})
        return self

    def subtotal(self):
        return self._rounded_total()

    def total(self):
        return self._rounded_total(self._discount_multiplier)

    def apply_discount(self, pct):
        pct = Decimal(str(pct))
        self._discount_multiplier *= (Decimal("100") - pct) / Decimal("100")
        return self

    def _rounded_total(self, multiplier=Decimal("1")):
        amount = sum(
            (Decimal(str(i["price"])) * Decimal(str(i["qty"])) for i in self.items),
            Decimal("0"),
        )
        return float((amount * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
