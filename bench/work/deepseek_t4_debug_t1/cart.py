class Cart:
    def __init__(self, items=None):
        self.items = [] if items is None else items
        self._discount_factor = 1.0

    def add(self, name, price, qty=1):
        self.items.append({"name": name, "price": price, "qty": qty})
        return self

    def subtotal(self):
        return round(sum(i["price"] * i["qty"] for i in self.items), 2)

    def total(self):
        return round(self.subtotal() * self._discount_factor, 2)

    def apply_discount(self, pct):
        self._discount_factor *= (100 - pct) / 100
        return self
