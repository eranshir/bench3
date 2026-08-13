"""Command line entry point.

    python3 -m ledgerkit.cli report --tenant acme
    python3 -m ledgerkit.cli report --tenant kitsune --format json
    python3 -m ledgerkit.cli tenants
"""
import argparse
import sys

from . import catalog as catalog_module
from . import exporters, repository, reporting, tenants, validation
from .errors import LedgerkitError


def cmd_report(args):
    tenant = tenants.get(args.tenant)
    orders = repository.for_tenant(tenant.tenant_id)
    catalog = catalog_module.default_catalog()

    problems = validation.check_all(orders, catalog)
    if problems:
        for order_id, message in problems:
            print(f"invalid order {order_id}: {message}", file=sys.stderr)
        return 2

    report = reporting.tenant_report(tenant, orders, catalog)
    print(exporters.render(report, args.format))
    return 0


def cmd_tenants(args):
    for tenant in tenants.all_tenants():
        print(f"{tenant.tenant_id:<12} {tenant.name:<20} "
              f"reports in {tenant.reporting_currency}  "
              f"discounts: {tenant.describe_discounts()}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="ledgerkit")
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser("report", help="settlement report for a tenant")
    report.add_argument("--tenant", required=True, choices=tenants.ids())
    report.add_argument("--format", default="text",
                        choices=sorted(exporters.FORMATS))
    report.set_defaults(func=cmd_report)

    listing = sub.add_parser("tenants", help="list configured tenants")
    listing.set_defaults(func=cmd_tenants)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except LedgerkitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
