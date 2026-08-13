# Hard suite

Built 2026-08-01, after the first suite saturated at 30/30 for both models.
Each task targets a specific gap that run exposed.

| Task | Probes | Planted defects |
|---|---|---|
| `h1_perf` | algorithmic complexity under a wall-clock budget | two O(n·w) functions that must become sub-quadratic without changing semantics |
| `h2_concurrency` | races and lock-order deadlock | unsynchronised read-modify-write, lock-order inversion, check-then-act on an empty queue |
| `h3_bigcontext` | navigating ~1,000 lines across 15 modules | inverted fx cross-rate, tax charged pre-discount, JPY rounded to 2dp |
| `h4_underspec` | inferring a spec from three examples | none — implement from scratch with no grammar given |
| `h5_longhorizon` | many sequential tool calls | four chained failures, each masking the next |

## Validation

Both directions were checked for every task, the same discipline the first
suite used. "Buggy" is the shipped fixture; "fixed" is a reference solution
written for validation only and not shipped.

| Task | Buggy fixture | Reference fix |
|---|---|---|
| `h1_perf` | 2 perf failures (10.0s vs 4s budget, 19.9s vs 4s) | correctness suite passes; budgets sized for O(n log w) |
| `h2_concurrency` | 5 failures | 7/7 in 1.2s |
| `h3_bigcontext` | 12 test methods fail (+6 subtests) | 18/18 |
| `h4_underspec` | 25 errors on the stub | 20/20 |
| `h5_longhorizon` | 15 failures/errors | 16/16 |

No task is accidentally pre-passing, and every task is demonstrably solvable.

## Design notes worth knowing

- **h1 budgets are machine-relative.** 4s on this M-series Mac, against a
  naive baseline of 10s and 19.9s. Re-measure before trusting them elsewhere.
  A `bisect.insort` solution (~0.3s) passes legitimately even though it is not
  asymptotically better; the task asks for speed, not for a specific
  algorithm.
- **h2 races do not reproduce naively on Python 3.14.** CPython only checks
  the eval breaker at calls and backward jumps, so a straight-line
  read-modify-write pair is effectively atomic — a plain counter race scored
  400000/400000. The fixture therefore puts a real Python-level loop between
  read and write, and the grader adds `test_deposit_is_mutually_exclusive`,
  which wraps `balances` in a dict that yields the GIL on every read. That
  probe is deterministic and cannot be evaded by rewriting the body to avoid
  a loop.
- **h2 grading runs every threaded scenario in a child process** with a 45s
  timeout. A deadlocked `WorkerPool` leaves non-daemon threads alive, so an
  in-process check would hang the grader rather than fail it. Budget ~135s of
  grading for a failing run, ~2s for a passing one.
- **h3 publishes correct figures for acme and kitsune only.** borealis and
  northwind are graded but unpublished, so special-casing the two visible
  tenants fails. kitsune is in the published set deliberately: without a JPY
  tenant the zero-decimal rounding bug would not be discoverable.
- **h4 grades only inferable behaviour.** Standard precedence
  (`not` > `and` > `or`), parentheses, the full comparison set, both quote
  styles. Genuinely arbitrary choices — which exception type, how a missing
  field is signalled — are only checked to the extent that garbage must not
  evaluate to `True`. The no-`eval` check is word-boundary matched, so a
  helper named `_eval` is fine.
- **h5's third link is a stale dev database.** Fixing the schema is not enough
  because `CREATE TABLE IF NOT EXISTS` will not alter the file the previous
  failing run already created. This is realistic and discoverable from the
  error, but it is a real fourth step.

## Running

```bash
./run_hard.sh deepseek 1        # all 5 tasks, trial 1
./run_hard.sh gpt      1
./run_hard.sh deepseek 1 h3_bigcontext    # single task
```

`LIMIT=900` caps each agent run (seconds); a kill lands as
`notes=timeout_900s`. `EFFORT=high` is pinned for both models by default, as
in the first suite. Results append to `results_hard.csv`, which adds a
`grade_seconds` column so slow grading is not mistaken for slow modelling.

Analyse with `../analyze.py hard/results_hard.csv` and
`../claims.py hard/results_hard.csv`.

## Two grader bugs found during the first batch

Both scored *correct* DeepSeek solutions as failures. Both are fixed; all
affected runs were re-graded from their saved work directories with
`regrade.py`, without re-running any model. Recording them because both are
easy to reintroduce.

1. **h3's synthetic case sat on a rounding knife-edge.** The expected total
   was 17062-equivalent at exactly `.5`: the unrounded sum was
   `18427.4999…`, which Decimal's 28-significant-digit context rounds to
   `18427.500…`, which then rounds half-up to 18428. A model that summed
   per-row-rounded figures instead got 18427. That graded a rounding
   *aggregation policy*, not the three planted defects. Fixed by choosing data
   where both aggregation orders agree and the fraction sits 0.28 off the
   boundary. The four real tenants were never affected — verified explicitly.
2. **h4's no-`eval` check was a regex over source text.** It matched the
   phrase "no eval()/exec()" inside a model's own module docstring. Replaced
   with an `ast` walk for `Call` nodes to `Name` `eval`/`exec`, which ignores
   docstrings, comments, helpers named `_eval`, and `self.eval(...)`.

Without these fixes DeepSeek would have scored 12/15 instead of 14/15. The
lesson generalises: when a grader must reject something, assert on structure
(parse it) rather than on text, and keep expected numeric values away from
rounding boundaries.

## Calibration data point

One real DeepSeek run on `h4_underspec` before the batch: **197s, 77,189
tokens, 19/20** — it failed only on trailing whitespace in
`"   age   >   29   "`. Compare with the easy suite, where DeepSeek's median
run was 23s and 54,765 tokens. The hard suite costs roughly 8x the wall-clock
and 1.4x the tokens per task, and it discriminates.
