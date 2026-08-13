"""Product catalog.

Prices are stored in the currency the product is sold in. A product sold in
more than one currency has one entry per currency; the order's currency
selects which entry applies.
"""
from decimal import Decimal

from .errors import CatalogError
from .money import Money


class Product:
    __slots__ = ("sku", "name", "prices", "sellable")

    def __init__(self, sku, name, prices, sellable=True):
        self.sku = sku
        self.name = name
        # currency -> Decimal unit price
        self.prices = {c: Decimal(str(p)) for c, p in prices.items()}
        self.sellable = sellable

    def price_in(self, currency):
        if not self.sellable:
            raise CatalogError(f"{self.sku} is not sellable")
        if currency not in self.prices:
            raise CatalogError(f"{self.sku} has no price in {currency}")
        return Money(self.prices[currency], currency)

    def currencies(self):
        return sorted(self.prices)

    def __repr__(self):
        return f"Product({self.sku!r})"


PRODUCTS = [
    Product("WIDGET-S", "Widget, small",
            {"USD": "12.50", "EUR": "11.50", "GBP": "9.90", "JPY": "1960"}),
    Product("WIDGET-L", "Widget, large",
            {"USD": "42.00", "EUR": "38.60", "GBP": "33.20", "JPY": "6590"}),
    Product("GADGET", "Gadget",
            {"USD": "199.99", "EUR": "183.99", "GBP": "158.00",
             "JPY": "31400"}),
    Product("SPROCKET", "Sprocket, boxed",
            {"USD": "7.25", "EUR": "6.67", "GBP": "5.73", "JPY": "1140"}),
    Product("SUPPORT-YR", "Support, annual",
            {"USD": "1200.00", "EUR": "1104.00", "GBP": "948.00",
             "JPY": "188400"}),
    Product("LEGACY-KIT", "Legacy kit", {"USD": "88.00"}, sellable=False),
]


class Catalog:
    def __init__(self, products=None):
        self._by_sku = {p.sku: p for p in (products or PRODUCTS)}

    def get(self, sku):
        try:
            return self._by_sku[sku]
        except KeyError:
            raise CatalogError(f"unknown sku {sku!r}") from None

    def price(self, sku, currency):
        return self.get(sku).price_in(currency)

    def skus(self):
        return sorted(self._by_sku)

    def __len__(self):
        return len(self._by_sku)


def default_catalog():
    return Catalog()
