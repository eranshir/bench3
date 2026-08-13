class Cart:
    def __init__(self, items=[]):
        self.items = items

    def add(self, name, price, qty=1):
        self.items.append({"name": name, "price": price, "qty": qty})
        return self

    def total(self):
        return sum(i["price"] * i["qty"] for i in self.items)

    def apply_discount(self, pct):
        for i in self.items:
            i["price"] = i["price"] * (100 - pct) / 100
        return self
