"""Blind grader for h3_bigcontext.

Three defects are planted, in three different modules:
  fx.cross_rate       - inverted, so cross-currency conversion goes the wrong way
  pricing.order_total - taxes the pre-discount subtotal
  reporting           - rounds every currency to 2dp, which is wrong for JPY

expected_totals.md shows correct figures for acme and kitsune only. These
tests also cover borealis and northwind, whose figures the model never saw,
plus unit-level behaviour of each defective function. A fix that special-cases
the two published tenants fails here.
"""
import unittest
from decimal import Decimal

from ledgerkit import catalog as catalog_module
from ledgerkit import (discounts, fx, orders, pricing, reporting, repository,
                       tenants)
from ledgerkit.money import Money


class FxDirection(unittest.TestCase):
    """RATES is units-per-USD, so EUR->USD must divide by the EUR rate."""

    def test_cross_rate_is_target_over_source(self):
        self.assertAlmostEqual(
            fx.cross_rate("EUR", "USD"),
            Decimal("1") / Decimal("0.92"), places=9)
        self.assertAlmostEqual(
            fx.cross_rate("USD", "EUR"), Decimal("0.92"), places=9)

    def test_eur_is_worth_more_than_a_dollar(self):
        got = fx.convert(Money(Decimal("100"), "EUR"), "USD")
        self.assertEqual(got.quantized().amount, Decimal("108.70"))

    def test_usd_to_jpy(self):
        got = fx.convert(Money(Decimal("100"), "USD"), "JPY")
        self.assertEqual(got.quantized().amount, Decimal("15700"))

    def test_round_trip_is_identity(self):
        start = Money(Decimal("250"), "GBP")
        back = fx.convert(fx.convert(start, "JPY"), "GBP")
        self.assertAlmostEqual(back.amount, start.amount, places=6)

    def test_same_currency_is_a_no_op(self):
        m = Money(Decimal("12.34"), "USD")
        self.assertEqual(fx.convert(m, "USD"), m)


class TaxAfterDiscount(unittest.TestCase):
    def setUp(self):
        self.catalog = catalog_module.default_catalog()
        self.tenant = tenants.Tenant("t", "T", "us-ca", "USD",
                                     [discounts.PercentageDiscount(10)])
        self.order = orders.Order(
            "X-1", "t", "USD", "us-ca",
            [orders.OrderLine("GADGET", 1)], "2026-05-01")

    def test_tax_is_charged_on_the_discounted_amount(self):
        # 199.99 - 10% = 179.991, +8.75% tax = 195.74021... -> 195.74
        self.assertEqual(
            pricing.order_total(self.order, self.catalog, self.tenant).amount,
            Decimal("195.74"))

    def test_breakdown_components_reconcile_with_the_total(self):
        parts = pricing.price_breakdown(self.order, self.catalog, self.tenant)
        self.assertEqual((parts["taxable"] + parts["tax"]).quantized(),
                         parts["total"])
        self.assertEqual(parts["subtotal"] - parts["discount"],
                         parts["taxable"])

    def test_zero_discount_tenant_is_unaffected(self):
        plain = tenants.Tenant("p", "P", "us-ca", "USD", [])
        # 199.99 + 8.75% = 217.489125 -> 217.49
        self.assertEqual(
            pricing.order_total(self.order, self.catalog, plain).amount,
            Decimal("217.49"))

    def test_zero_tax_region_is_just_the_discounted_subtotal(self):
        free = orders.Order("X-2", "t", "USD", "us-or",
                            [orders.OrderLine("GADGET", 1)], "2026-05-01")
        self.assertEqual(
            pricing.order_total(free, self.catalog, self.tenant).amount,
            Decimal("179.99"))


class ReportRounding(unittest.TestCase):
    def test_jpy_rounds_to_whole_yen(self):
        got = reporting.round_for_report(Money(Decimal("123.456"), "JPY"))
        self.assertEqual(got.amount, Decimal("123"))
        self.assertEqual(got.amount.as_tuple().exponent, 0)

    def test_usd_still_rounds_to_cents(self):
        got = reporting.round_for_report(Money(Decimal("123.456"), "USD"))
        self.assertEqual(got.amount, Decimal("123.46"))

    def test_half_rounds_away_from_zero(self):
        self.assertEqual(
            reporting.round_for_report(Money(Decimal("0.5"), "JPY")).amount,
            Decimal("1"))


class PublishedTenants(unittest.TestCase):
    """The two tenants whose figures are in expected_totals.md."""

    def setUp(self):
        self.catalog = catalog_module.default_catalog()

    def total_for(self, tenant_id):
        tenant = tenants.get(tenant_id)
        return reporting.tenant_total(
            tenant, repository.for_tenant(tenant_id), self.catalog)

    def test_acme(self):
        self.assertEqual(self.total_for("acme").amount, Decimal("2063.64"))

    def test_kitsune(self):
        got = self.total_for("kitsune")
        self.assertEqual(got.amount, Decimal("177415"))
        self.assertEqual(got.amount.as_tuple().exponent, 0,
                         "a JPY settlement figure must be whole yen")


class UnpublishedTenants(unittest.TestCase):
    """Figures the model never saw. Special-casing acme/kitsune fails here."""

    def setUp(self):
        self.catalog = catalog_module.default_catalog()

    def total_for(self, tenant_id):
        tenant = tenants.get(tenant_id)
        return reporting.tenant_total(
            tenant, repository.for_tenant(tenant_id), self.catalog)

    def test_borealis(self):
        self.assertEqual(self.total_for("borealis").amount,
                         Decimal("3354.77"))

    def test_northwind(self):
        self.assertEqual(self.total_for("northwind").amount,
                         Decimal("1547.96"))

    def test_selected_converted_rows(self):
        catalog = self.catalog
        expected = {
            ("acme", "A-1003"): Decimal("212.46"),
            ("acme", "A-1004"): Decimal("432.00"),
            ("borealis", "B-2003"): Decimal("2403.96"),
            ("northwind", "N-4003"): Decimal("170.79"),
            ("northwind", "N-4004"): Decimal("66.36"),
            ("kitsune", "K-3003"): Decimal("35856"),
        }
        for (tenant_id, order_id), want in expected.items():
            with self.subTest(order=order_id):
                tenant = tenants.get(tenant_id)
                row = reporting.order_row(repository.get(order_id), catalog,
                                          tenant)
                self.assertEqual(row["reported"].amount, want)


class SyntheticTenant(unittest.TestCase):
    """A configuration that does not exist in the repository at all."""

    def test_threshold_discount_in_jpy_with_mixed_currency_orders(self):
        catalog = catalog_module.default_catalog()
        tenant = tenants.Tenant(
            "synth", "Synthetic", "jp", "JPY",
            [discounts.ThresholdDiscount(Money(Decimal("10000"), "JPY"), 20)])
        book = [
            orders.Order("S-1", "synth", "JPY", "jp",
                         [orders.OrderLine("WIDGET-L", 2)], "2026-05-01"),
            orders.Order("S-2", "synth", "EUR", "eu-fr",
                         [orders.OrderLine("SPROCKET", 4)], "2026-05-02"),
        ]
        # S-1: 13180 JPY, -20% = 10544, +10% tax = 11598.4 -> 11598
        # S-2: 26.68 EUR, no discount (currency mismatch), +20% = 32.02
        #      32.02 EUR -> JPY at 157/0.92 = 5464.28...
        # Total 17062.28. Deliberately not near a .5 boundary: summing the
        # unrounded conversions and summing the per-row rounded ones both give
        # 17062, so this grades the three planted defects rather than a
        # rounding-aggregation preference.
        total = reporting.tenant_total(tenant, book, catalog)
        self.assertEqual(total.currency, "JPY")
        self.assertEqual(total.amount.as_tuple().exponent, 0)
        self.assertEqual(total.amount, Decimal("17062"))


if __name__ == "__main__":
    unittest.main()
