class Cart:
    def __init__(self, items=None):
        self.items = [] if items is None else items

    def add(self, name, price, qty=1):
        self.items.append({
            "name": name,
            "price": price,
            "discounted_price": price,
            "qty": qty,
        })
        return self

    def total(self):
        return round(sum(i["discounted_price"] * i["qty"] for i in self.items), 2)

    def subtotal(self):
        return round(sum(i["price"] * i["qty"] for i in self.items), 2)

    def apply_discount(self, pct):
        for i in self.items:
            i["discounted_price"] *= (100 - pct) / 100
        return self
