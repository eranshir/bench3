"""Exception hierarchy for ledgerkit."""


class LedgerkitError(Exception):
    """Base class for everything this package raises."""


class CurrencyError(LedgerkitError):
    """Unknown currency, or an operation mixing two currencies."""


class CatalogError(LedgerkitError):
    """A SKU is not in the catalog, or is not sellable."""


class TenantError(LedgerkitError):
    """Unknown tenant, or a tenant with an unusable configuration."""


class RegionError(LedgerkitError):
    """No tax rule is registered for the region."""


class ValidationError(LedgerkitError):
    """An order or line failed validation."""
