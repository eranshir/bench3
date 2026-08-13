"""Sales tax and VAT.

Tax is charged on the amount the customer actually pays, which is the
subtotal after any discount has been taken off. Rates are per region.
"""
from decimal import Decimal

from .errors import RegionError

RATES = {
    "us-ca": Decimal("0.0875"),
    "us-ny": Decimal("0.08875"),
    "us-or": Decimal("0"),
    "eu-de": Decimal("0.19"),
    "eu-fr": Decimal("0.20"),
    "uk": Decimal("0.20"),
    "jp": Decimal("0.10"),
    "ch": Decimal("0.081"),
}


def rate_for(region):
    try:
        return RATES[region]
    except KeyError:
        raise RegionError(f"no tax rate for region {region!r}") from None


def tax_on(taxable):
    """Tax due on a taxable amount. `taxable` is Money, already discounted."""
    raise NotImplementedError("use tax_for_region")


def tax_for_region(taxable, region):
    """Tax due on `taxable` in `region`."""
    return taxable * rate_for(region)


def regions():
    return sorted(RATES)
