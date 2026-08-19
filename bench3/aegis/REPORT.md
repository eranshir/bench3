# bench3 Aegis guided-vs-enforced - scored report

**Date:** 2026-08-19T19:05+00:00  **Status:** per ADR 0043

## Honesty boundary (issue #1623)

Measures whether **live enforcement** of the Aegis method changes measured adherence and
outcomes on bench3 agentic tasks vs prose guidance alone. Does NOT establish that Aegis
makes an agent reliable, correct, or complete. Supported conclusion is procedural.

## Pass rates

| Arm | pass@1 | cells | pass^k cells |
|---|---|---|---|
| enforced | 1.0 | 4 | 0/4 |
| guided | 0.193 | 49 | 3/49 |

## Enforcement lift (per task x model)

| Task | Model | dRes (enf-guided) | dComp | McNemar p |
|---|---|---|---|---|
| coding/c1_deadlock | deepseek-flash | 0.0 | 0.0 | n/a |
| coding/c1_deadlock | gpt-sol | 0.333 | 0.0 | n/a |
| coding/c1_deadlock | lunaroute | 0.0 | 0.0 | n/a |
| coding/c1_deadlock | mtplx | 0.0 | 0.0 | n/a |

## Tokens

Enforced minus guided output-token delta (bootstrap 95% CI): {"mean": null, "ci95": null, "includes_zero": null}

## Compliance (plan_valid / children-with-falsifiers)

- coding/c1_deadlock|enforced|deepseek-flash: plan_valid 1.00 | falsifiers 1.00 | n=2
- coding/c1_deadlock|enforced|gpt-sol: plan_valid 1.00 | falsifiers 1.00 | n=2
- coding/c1_deadlock|enforced|lunaroute: plan_valid 1.00 | falsifiers 1.00 | n=2
- coding/c1_deadlock|enforced|mtplx: plan_valid 1.00 | falsifiers 1.00 | n=2
- coding/c1_deadlock|guided|deepseek-flash: plan_valid 1.00 | falsifiers 1.00 | n=3
- coding/c1_deadlock|guided|gpt-sol: plan_valid 1.00 | falsifiers 1.00 | n=3
- coding/c1_deadlock|guided|lunaroute: plan_valid 1.00 | falsifiers 1.00 | n=3
- coding/c1_deadlock|guided|mtplx: plan_valid 1.00 | falsifiers 1.00 | n=3
- creativity/k1_product|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- creativity/k1_product|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- creativity/k1_product|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- creativity/k1_product|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- creativity/k2_story|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- creativity/k2_story|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- creativity/k2_story|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- creativity/k2_story|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r1_tiling|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r1_tiling|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r1_tiling|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r1_tiling|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r1_tiling|guided|lunaroute: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r2_expectedflips|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r2_expectedflips|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r2_expectedflips|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r2_expectedflips|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r3_die_expected|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r3_die_expected|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r3_die_expected|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r3_die_expected|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r4_catalan|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r4_catalan|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r4_catalan|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- reasoning/r4_catalan|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t1_orchestrate|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t1_orchestrate|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t1_orchestrate|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t1_orchestrate|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t2_toolselect|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t2_toolselect|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t2_toolselect|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t2_toolselect|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t3_inventory|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t3_inventory|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t3_inventory|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- tool-use/t3_inventory|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- writing/w1_explain|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- writing/w1_explain|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- writing/w1_explain|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- writing/w1_explain|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1
- writing/w2_rewrite|guided|deepseek-flash: plan_valid 0.00 | falsifiers 0.00 | n=1
- writing/w2_rewrite|guided|deepseek-pro: plan_valid 0.00 | falsifiers 0.00 | n=1
- writing/w2_rewrite|guided|gpt-sol: plan_valid 0.00 | falsifiers 0.00 | n=1
- writing/w2_rewrite|guided|grok: plan_valid 0.00 | falsifiers 0.00 | n=1

## Contamination (ADR 0043 Rule 1)

```json
{
 "per_task": {
  "coding/c1_deadlock": {
   "pairwise": {
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->enforced_deepseek-flash_coding-c1_deadlock_rep2": 0.23809523809523808,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->enforced_gpt-sol_coding-c1_deadlock_rep1": 0.3333333333333333,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->enforced_gpt-sol_coding-c1_deadlock_rep2": 0.23809523809523808,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->enforced_lunaroute_coding-c1_deadlock_rep1": 0.42857142857142855,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->enforced_lunaroute_coding-c1_deadlock_rep2": 0.3333333333333333,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->enforced_mtplx_coding-c1_deadlock_rep1": 0.2857142857142857,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->enforced_mtplx_coding-c1_deadlock_rep2": 0.3333333333333333,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_deepseek-flash_coding-c1_deadlock_rep1": 0.2857142857142857,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_deepseek-flash_coding-c1_deadlock_rep2": 0.38095238095238093,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_deepseek-flash_coding-c1_deadlock_rep3": 0.42857142857142855,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_gpt-sol_coding-c1_deadlock_rep1": 0.38095238095238093,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_gpt-sol_coding-c1_deadlock_rep2": 0.3333333333333333,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_gpt-sol_coding-c1_deadlock_rep3": 0.38095238095238093,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_lunaroute_coding-c1_deadlock_rep1": 0.38095238095238093,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_lunaroute_coding-c1_deadlock_rep2": 0.3333333333333333,
    "enforced_deepseek-flash_coding-c1_deadlock_rep1->guided_lunaroute_coding-c1_deadlock_rep3": 0.3333333333333333,
    "enforced_deepseek-flash_coding-c1_deadl
```

## Singleshot (guided-only arm, per ratified scope)

| Model | cells | resolved | checker-pass |
|---|---|---|---|
| deepseek-flash | 11 | 11 | 8 |
| deepseek-pro | 11 | 11 | 7 |
| gpt-sol | 11 | 11 | 8 |
| grok | 11 | 11 | 7 |
| lunaroute | 1 | 1 | 1 |

Note: tool-use tasks (t1-t3) score checker=False in this arm (text-only path, no tools array).

## Enforcement time tax

Guided median 344s (n=12) | enforced median 388s (n=8) | +13%

## Validity checklist

- [x] fresh workspace per arm x rep; clean_before asserted
- [ ] contamination below threshold
- [x] cohort manifest committed (bench3/cohorts/aegis-agentic.json)
- [x] materialization proof per arm (digest / transcript / proven absent)
- [x] parity manifest: one DSH + one model; real versions
- [x] token buckets complete
- [x] k = 3; paired stats; CI-aware phrasing
- [x] ladder arms with config proofs (arm_config per record)
- [x] scoring fail-closed; hidden tests; timeouts unresolved

