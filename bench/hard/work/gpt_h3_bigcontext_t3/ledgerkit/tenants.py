"""Tenant configuration.

Each tenant reports in one currency. Orders may be placed in any currency the
catalog prices; the report converts them into the tenant's reporting
currency.
"""
from decimal import Decimal

from .discounts import FixedDiscount, PercentageDiscount, ThresholdDiscount
from .errors import TenantError
from .money import Money


class Tenant:
    __slots__ = ("tenant_id", "name", "home_region", "reporting_currency",
                 "discount_rules")

    def __init__(self, tenant_id, name, home_region, reporting_currency,
                 discount_rules=()):
        self.tenant_id = tenant_id
        self.name = name
        self.home_region = home_region
        self.reporting_currency = reporting_currency
        self.discount_rules = list(discount_rules)

    def describe_discounts(self):
        if not self.discount_rules:
            return "none"
        return "; ".join(rule.describe() for rule in self.discount_rules)

    def __repr__(self):
        return f"Tenant({self.tenant_id!r}, {self.reporting_currency})"


TENANTS = [
    Tenant("acme", "Acme Industrial", "us-ca", "USD",
           [PercentageDiscount(10)]),
    Tenant("borealis", "Borealis GmbH", "eu-de", "EUR", []),
    Tenant("kitsune", "Kitsune KK", "jp", "JPY",
           [ThresholdDiscount(Money(Decimal("50000"), "JPY"), 5)]),
    Tenant("northwind", "Northwind Ltd", "uk", "GBP",
           [FixedDiscount(Money(Decimal("25.00"), "GBP"))]),
]

_BY_ID = {t.tenant_id: t for t in TENANTS}


def get(tenant_id):
    try:
        return _BY_ID[tenant_id]
    except KeyError:
        raise TenantError(f"unknown tenant {tenant_id!r}") from None


def all_tenants():
    return list(TENANTS)


def ids():
    return sorted(_BY_ID)
