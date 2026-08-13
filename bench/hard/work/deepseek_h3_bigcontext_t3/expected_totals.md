# Expected settlement totals — May 2026

Reconciled by hand against the signed invoices. These figures are correct.
`python3 -m ledgerkit.cli report --tenant <id>` currently disagrees with them.

## acme — reports in USD

| order | placed | ccy | order total | reported (USD) |
|---|---|---|---|---|
| A-1001 | 2026-05-02 | USD | 244.68 | 244.68 |
| A-1002 | 2026-05-06 | USD | 1174.50 | 1174.50 |
| A-1003 | 2026-05-11 | EUR | 195.46 | 212.46 |
| A-1004 | 2026-05-19 | GBP | 341.28 | 432.00 |
| **TOTAL** | | | | **2063.64** |

## kitsune — reports in JPY

| order | placed | ccy | order total | reported (JPY) |
|---|---|---|---|---|
| K-3001 | 2026-05-04 | JPY | 98439 | 98439 |
| K-3002 | 2026-05-09 | JPY | 43120 | 43120 |
| K-3003 | 2026-05-17 | USD | 228.38 | 35856 |
| **TOTAL** | | | | **177415** |

Note that JPY has no minor units. A yen figure with a fractional part is
never a valid settlement figure.
