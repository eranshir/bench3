from decimal import Decimal, ROUND_HALF_UP


class Cart:
    def __init__(self, items=None):
        self.items = [] if items is None else items
        self._discount_multiplier = Decimal("1")

    def add(self, name, price, qty=1):
        self.items.append({"name": name, "price": price, "qty": qty})
        return self

    @staticmethod
    def _round_money(amount):
        return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def subtotal(self):
        amount = sum(
            (Decimal(str(i["price"])) * Decimal(str(i["qty"])) for i in self.items),
            Decimal("0"),
        )
        return self._round_money(amount)

    def total(self):
        amount = sum(
            (Decimal(str(i["price"])) * Decimal(str(i["qty"])) for i in self.items),
            Decimal("0"),
        )
        return self._round_money(amount * self._discount_multiplier)

    def apply_discount(self, pct):
        self._discount_multiplier *= (Decimal("100") - Decimal(str(pct))) / Decimal("100")
        return self
