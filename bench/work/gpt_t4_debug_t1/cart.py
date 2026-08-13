class Cart:
    def __init__(self, items=None):
        self.items = [] if items is None else items
        self._discount_multiplier = 1.0

    def add(self, name, price, qty=1):
        self.items.append({"name": name, "price": price, "qty": qty})
        return self

    def subtotal(self):
        return round(sum(i["price"] * i["qty"] for i in self.items), 2)

    def total(self):
        undiscounted = sum(i["price"] * i["qty"] for i in self.items)
        return round(undiscounted * self._discount_multiplier, 2)

    def apply_discount(self, pct):
        self._discount_multiplier *= (100 - pct) / 100
        return self
