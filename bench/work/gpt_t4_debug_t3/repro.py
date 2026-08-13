from cart import Cart

a = Cart()
a.add("widget", 10.0)
b = Cart()
print("cart b should be empty, got:", b.items)

c = Cart()
c.add("thing", 100.0)
c.apply_discount(10)
c.apply_discount(10)
print("expected 81.0 after two 10% discounts, got:", c.total())
