# DeepSeek V4-Flash vs GPT-5.6-Sol in Codex CLI

**A controlled comparison of coding-agent accuracy, latency and cost**

Author: Claude Code session, 2026-08-01/02
Status: complete. Supersedes `REPORT.md`, which is the running narrative log.
Raw data: `bench/results.csv`, `bench/hard/results_hard.csv`, `bench/**/runs/`

---

## Executive summary

Two coding agents were run over ten tasks, three trials each, graded blind
against tests they never saw. Sixty runs total, in two batches.

1. **On well-specified work the two models are indistinguishable in
   accuracy.** Across both suites they went 29/30 and 30/30. The first suite
   saturated completely at 30/30 for both, and a purpose-built harder suite —
   sub-quadratic rewrites, deadlock, three bugs across a 993-line package,
   four chained failures — separated them by exactly one run.
2. **DeepSeek is consistently faster and consistently heavier.** It won
   wall-clock on 9 of 10 tasks (1.7–2.2× on medians) while consuming 2.0–3.0×
   the tokens.
3. **DeepSeek's measured cost for all 30 of its runs was $0.39.** GPT's
   equivalent is modelled, not measured: those runs billed against a ChatGPT
   subscription, so marginal out-of-pocket was $0. Modelled at API list price,
   GPT's 861,298 tokens cost $4.31–$25.84 depending on the input/output mix.
4. **The cost ratio depends entirely on an assumption that cannot be
   measured here.** Per passing task the advantage is ~10× at the conservative
   floor and ~40–64× at reasoning-heavy mixes. Quoting a single number without
   naming the mix is not meaningful.
5. **The one differentiating task was the only underspecified one.** The
   boundary this experiment located is specification quality, not difficulty —
   but it rests on a single failure and should be treated as a hypothesis.
6. **Two bugs in my own graders wrongly failed correct DeepSeek solutions.**
   Both were found, fixed, and re-graded. Uncorrected, DeepSeek would have
   scored 12/15 on the hard suite instead of 14/15 — grader noise was about to
   be twice the size of the real signal.

---

## 1. Question and scope

The original brief: determine whether DeepSeek V4-Flash-0731 is good enough to
displace GPT-5.6-Sol for some share of Codex CLI work, and at what cost ratio.
The requested deliverable was a recommendation "with a boundary, not a winner"
— something of the form "DeepSeek for this shape of work, GPT for that shape."

That framing survived, but the first suite could not support it, because no
boundary appeared. The experiment was therefore extended with a second,
harder suite designed specifically to find one. Both are reported here.

**Out of scope:** model quality on non-coding tasks, IDE/interactive use,
multi-turn collaboration, and anything touching Nexar code or data. This work
is personal-scope: no git remote, key in the macOS Keychain rather than
aegis-secret. Pointing it at Nexar code would make it a vendor/data-handling
decision requiring a CISO request in `getnexar/ciso-requests` first.

---

## 2. Systems under test

| | DeepSeek arm | GPT arm |
|---|---|---|
| Model | `deepseek-v4-flash` | `gpt-5.6-sol` |
| Invocation | `deepcodex` (wrapper) | `codex` |
| CLI | codex-cli 0.144.1 | codex-cli 0.144.1 |
| Auth | API key, macOS Keychain service `deepseek-api-key` | ChatGPT OAuth |
| Billing | per token, real money | subscription quota |
| Context window | 1,000,000 (configured) | 272,000 |
| Effort (native default) | `high` | `xhigh` |
| Effort (as run) | `high` | `high` |

Both arms run the **same CLI binary**, differing only in profile. That is the
central control in this design: harness behaviour, tool surface, sandboxing,
prompt scaffolding and patch application are identical, so differences are
attributable to the model rather than the agent framework.

`deepcodex` is a small `sh` wrapper that pulls the key from the Keychain,
exports it, and `exec`s `codex --profile deepseek "$@"`. It is an executable
rather than a shell function so it works from non-interactive shells. The
DeepSeek profile needs a hand-authored model catalog
(`~/.codex/deepseek.models.json`) because Codex ships none; the critical field
is `"tool_mode": "standard"` — GPT's `"code_mode_only"` makes Codex emit a
custom `exec` tool that DeepSeek rejects outright.

Environment: macOS (Darwin 25.5.0), Apple silicon, Python 3.14.4.

### Effort pinning

The two profiles default differently (`high` vs `xhigh`). Comparing them
as-configured would confound the model difference with an effort difference,
especially on latency. Both arms were therefore pinned to `high` via
`-c model_reasoning_effort="high"` on every run. The effort used is recorded
per row, so mixed runs would stay analysable. **GPT was thus run below its own
default**, which is a deliberate matching choice and a limitation: whether
`xhigh` would buy GPT anything is untested.

---

## 3. Harness design

### 3.1 Execution

Each run is one invocation:

```
cd <fresh copy of fixture>
$CMD -c model_reasoning_effort="high" exec \
     --sandbox workspace-write --skip-git-repo-check "$PROMPT" < /dev/null
```

- **Fresh fixture per run.** `bench/{,hard/}work/<model>_<task>_t<trial>/` is
  deleted and re-copied from `tasks/<task>/` before every run, so no run can
  see another's edits. All 60 work directories are retained after the batch,
  which later made it possible to re-grade without re-running anything.
- **`PROMPT.txt` is deleted from the work copy** after being read, so the
  model cannot read its own task statement as a file and cannot edit it.
- **`< /dev/null`** — without it `codex exec` blocks waiting on stdin.
- **`--skip-git-repo-check`** — the project is deliberately not a git repo.
- **No Claude Code subagents.** The repo ships `deepseek` and `gpt-codex`
  subagents for interactive use; using them here would insert a relay layer
  whose tokens and latency would pollute the measurement. The runners call the
  CLIs directly.

### 3.2 Grading

Grading is **blind and objective**. Each task has a hidden test in
`hidden/<task>_test.py` that the model never sees; it is copied into the work
directory as `_hidden_test.py` only after the agent has exited, then run with
`python3 -m unittest _hidden_test -v`. Pass/fail is the unittest exit code;
`tests_failed` counts `^(FAIL|ERROR):` lines.

The hidden tests deliberately cover cases the visible prompt does not, so a
model that special-cases the stated examples fails. Every task was validated
in **both directions** before use: the hidden test must fail on the unmodified
fixture, and must pass on a reference solution written separately.

### 3.3 Metrics captured

`model, task, trial, effort, seconds, tokens, passed, tests_failed, notes`
(the hard runner adds `grade_seconds`).

- `seconds` — wall-clock around the agent invocation only.
- `tokens` — the aggregate `codex exec` reports. **There is no input/output
  split available**: the figure is printed on the line *after* `tokens used`,
  and the session rollout files in `~/.codex/sessions/` carry no token
  accounting at all. This single limitation drives the entire cost
  methodology in §7.
- `notes` — classified failure modes (`insufficient_balance`, `auth_expired`,
  `tool_mode_misconfigured`, `timeout_<n>s`, `cli_exit_<n>`) so infrastructure
  failures are never silently scored as model failures.

### 3.4 Hardening added for the hard suite

- **Per-run watchdog.** `LIMIT=900` seconds; the agent runs in the background
  and a sleeper kills it on expiry. macOS has no `timeout(1)`.
- **Separate `grade_seconds`.** h2's grader can spend 135s detecting hangs;
  without a separate column that would look like slow modelling.
- **Resumability.** `resume_hard.sh` skips any `(model, task, trial)` already
  present in the results CSV. This mattered: the batch was killed twice by
  something outside the script, and recovery was a relaunch with no duplicated
  work and no double-counted tokens.
- **`regrade.py`.** Replays a corrected hidden test over saved work
  directories and rewrites the CSV. Used twice (§6), at zero token cost.

---

## 4. Suite 1 — the original tasks

Five self-contained Python fixtures, ascending difficulty.

| Task | Type | Probes |
|---|---|---|
| `t1_bugfix` | single-file bugfix | off-by-one in nearest-rank percentile |
| `t2_multifile` | multi-file feature | env-var overrides through 3 files, type coercion, precedence |
| `t3_tdd` | implement from tests | `parse_duration()`; spec exists only in the test file |
| `t4_debug` | subtle debugging | mutable default arg + lossy in-place discount; needs a new `subtotal()` |
| `t5_refactor` | constrained refactor | callback → lazy iterative generator, must survive depth 10,000 |

### 4.1 Results

**Both models: 30/30.** Every task, every trial, zero hidden-test failures,
zero CLI errors, zero excluded rows.

| Task | DS pass | DS med s | DS med tok | GPT pass | GPT med s | GPT med tok |
|---|---|---|---|---|---|---|
| `t1_bugfix` | 3/3 | 16 | 53,701 | 3/3 | 45 | 18,427 |
| `t2_multifile` | 3/3 | 30 | 56,568 | 3/3 | 65 | 17,542 |
| `t3_tdd` | 3/3 | 21 | 54,418 | 3/3 | 37 | 12,298 |
| `t4_debug` | 3/3 | 26 | 54,904 | 3/3 | 58 | 17,794 |
| `t5_refactor` | 3/3 | 23 | 54,765 | 3/3 | 40 | 16,749 |

| | DeepSeek | GPT |
|---|---|---|
| Total wall-clock | **369 s** | 776 s |
| Median run | **23 s** (15–48) | 51 s (34–92) |
| Total tokens | 817,349 | **269,857** |
| Median tokens | 54,765 (46K–59K) | **16,749** (12K–33K) |

DeepSeek was ~2.1× faster and burned ~3.0× the tokens, winning latency on all
five tasks.

### 4.2 Verification of the sweep

A clean sweep is the result most likely to indicate a broken grader, so
passes were inspected rather than trusted:

- **`t5` (DeepSeek)** — a genuine iterative stack-based generator using
  `reversed()` to preserve pre-order, with the callback `walk` removed and
  laziness intact. Not a special-case fit to the prompt's examples.
- **`t4` (both)** — both produced real fixes with a working `subtotal()`. GPT
  used `Decimal` with explicit `ROUND_HALF_UP`; DeepSeek used floats plus a
  defensive `list(items)` copy in the constructor.

The saturation is real, not an artifact.

### 4.3 What this suite could and could not support

It established the cost and latency profile decisively. It could **not**
support the requested boundary recommendation, because the difficulty ramp —
through to a constrained lazy-generator refactor — did not separate the models
at matched effort. Reporting a boundary anyway would have manufactured a
distinction the evidence did not contain.

---

## 5. Suite 2 — the hard tasks

Designed against the specific gaps suite 1 exposed: longer horizons, larger
context, underspecified prompts, and failure modes that cannot be fixed by
pattern-matching a stated example.

| Task | Probes | Planted defects |
|---|---|---|
| `h1_perf` | algorithmic complexity under a wall-clock budget | two O(n·w) sliding-window functions that must become sub-quadratic without changing semantics |
| `h2_concurrency` | races and lock-order deadlock | unsynchronised read-modify-write, lock-order inversion, check-then-act on an empty queue |
| `h3_bigcontext` | navigating 993 lines across 15 modules | inverted fx cross-rate, tax charged pre-discount, JPY rounded to 2dp |
| `h4_underspec` | inferring a spec from three examples | none — implement from scratch, no grammar given |
| `h5_longhorizon` | many sequential tool calls | four chained failures, each masking the next |

### 5.1 Task construction notes

**h1_perf.** `rolling_median` and `window_distinct_counts`, both correct and
both O(n·w). Correctness is graded against a brute-force reference encoding
the original semantics, so fast-but-different fails. Budgets: 4s each, against
a measured naive baseline of 10.0s and 19.9s on this machine. A
`bisect.insort` solution (~0.3s) passes legitimately — the task asks for
speed, not for a specific algorithm.

**h2_concurrency.** *The planted races do not reproduce naively on Python
3.14.* CPython only checks the eval breaker at calls and backward jumps, so a
straight-line read-modify-write pair is effectively atomic — a plain
8-thread counter race scored 400000/400000 across repeated attempts. Two
countermeasures: the fixture puts a real Python-level loop between read and
write (an audit entry that snapshots the ledger total, which is realistic
rather than contrived), and the grader adds a **deterministic
mutual-exclusion probe** that wraps `balances` in a dict subclass yielding the
GIL on every read. The probe cannot be evaded by rewriting the body to avoid a
loop, and correct locking passes it unchanged.

Every threaded scenario is graded **in a child process with a 45s timeout**. A
deadlocked `WorkerPool` leaves non-daemon threads alive, so an in-process
check would hang the grader forever instead of failing it.

**h3_bigcontext.** A coherent 15-module `ledgerkit` package (993 lines):
money with per-currency minor units, fx, catalog, orders, discounts, tax,
pricing, tenants, repository, reporting, exporters, formatting, validation,
analytics, CLI. Three bugs in three modules. Correct figures are published in
`expected_totals.md` for **two of four tenants only**; the other two are
graded blind, so special-casing the visible ones fails. The JPY tenant is
published deliberately — without it the zero-decimal rounding bug would not be
discoverable at all.

**h4_underspec.** Three examples, no grammar, no acceptance criteria, `eval`
and `exec` forbidden. The grader asserts only inferable behaviour: standard
precedence (`not` > `and` > `or`), parentheses, the full comparison set, both
quote styles, `contains` on lists and strings. Genuinely arbitrary choices —
which exception type, how a missing field is signalled — are checked only to
the extent that garbage must not evaluate to `True`.

**h5_longhorizon.** Four chained links, each masking the next: a config
default pointing at an unwritable prod path → a schema missing the `currency`
column → **a stale dev database that `CREATE TABLE IF NOT EXISTS` will not
alter** → an exclusive end-date filter plus 0-indexed pagination. The third
link is real and was discovered during validation rather than designed in.

### 5.2 Validation

Both directions, for every task:

| Task | Buggy fixture | Reference fix |
|---|---|---|
| `h1_perf` | 2 perf failures (10.0s and 19.9s vs 4s budgets) | correctness suite passes |
| `h2_concurrency` | 5 failures | 7/7 in 1.2s |
| `h3_bigcontext` | 12 test methods (+6 subtests) | 18/18 |
| `h4_underspec` | 25 errors on the stub | 20/20 |
| `h5_longhorizon` | 15 failures/errors | 16/16 |

### 5.3 Results

| Task | DS pass | DS med s | DS med tok | GPT pass | GPT med s | GPT med tok |
|---|---|---|---|---|---|---|
| `h1_perf` | 3/3 | 306 | 104,084 | 3/3 | 279 | 35,262 |
| `h2_concurrency` | 3/3 | 87 | 64,403 | 3/3 | 241 | 45,908 |
| `h3_bigcontext` | 3/3 | 118 | 78,747 | 3/3 | 139 | 38,693 |
| `h4_underspec` | **2/3** | 266 | 92,389 | 3/3 | 196 | 45,868 |
| `h5_longhorizon` | 3/3 | 55 | 61,143 | 3/3 | 122 | 28,579 |
| **Total** | **14/15** | | | **15/15** | | |

| | DeepSeek | GPT |
|---|---|---|
| Total wall-clock | **2,451 s** | 2,990 s |
| Median run | **118 s** (39–382) | 196 s (99–346) |
| Total tokens | 1,192,235 | **591,441** |
| Median tokens | 75,777 (59K–122K) | **35,449** (22K–67K) |

### 5.4 Reading the results

**The separation is one run wide.** DeepSeek's single failure was `h4` trial
1, whose tokenizer rejected `"   age   >   29   "` — it handled leading and
internal whitespace but not trailing. Every other assertion in that run
passed, and both later trials passed outright. With n=3 per cell this cannot
distinguish "worse at underspecified work" from "lost one coin flip."

**Both models are stronger than the suite.** Between them they went 12/12 on
the four hard-but-specified tasks: a two-heap median rewrite, a lock-order
deadlock, three bugs buried across fifteen modules, and a four-link chained
failure hunt. The tasks were built to break both models and mostly did not.

**Two suite-1 conclusions needed revising.** DeepSeek's token spend is *not*
flat — 59K–122K here against a tight 46K–59K before — so the earlier "fixed
context budget" reading was an artifact of tasks too easy to stress it. And
the latency gap compresses under load (1.7× from 2.2×), as does the token gap
(2.0× from 3.0×).

**Spot-check of a hard pass.** DeepSeek's `h3` trial 1 diff touched exactly
three files with exactly the three intended fixes, nothing else, and reused
the package's own `exponent_for` helper rather than hardcoding an exponent —
a cleaner fix than the reference patch written for validation.

---

## 6. Grader defects found and corrected

Two bugs in my own hidden tests, each of which scored a **correct** DeepSeek
solution as a failure. Both are recorded because both are easy to reintroduce.

**1. h3's synthetic case sat on a rounding knife-edge.** The expected total
depended on a value whose unrounded sum was `18427.4999…`; Decimal's
28-significant-digit context rounds that to `18427.500…`, which then rounds
half-up to 18428. A solution that summed per-row-rounded figures instead got
18427. The assertion was therefore grading a rounding *aggregation policy*,
not the three planted defects. Fixed by choosing data where both aggregation
orders agree and the fraction sits 0.28 off the boundary. The four real
tenants were checked explicitly and were never affected.

**2. h4's no-`eval` check was a regex over source text.** It matched the
phrase `"no eval()/exec()"` inside a model's own module docstring. Replaced
with an `ast` walk for `Call` nodes to `Name` `eval`/`exec`, verified against
five cases: docstring prose, a helper named `_eval`, a method `self.eval(...)`,
and real `eval(...)`/`exec(...)` calls.

Both were fixed and every affected run re-graded from its saved work directory
via `regrade.py` — no model re-runs, no additional spend. **Uncorrected,
DeepSeek would have scored 12/15 rather than 14/15.**

This is the most important methodological finding in the report. The real
accuracy difference between the models is one run; grader noise was about to
be twice that. The generalisable lesson: when a grader must reject something,
assert on structure (parse it) rather than on text, and keep expected numeric
values away from rounding boundaries.

---

## 7. Cost

### 7.1 Published list prices (per 1M tokens)

| | input | cached input | output |
|---|---|---|---|
| `deepseek-v4-flash` | $0.14 | $0.0028 | $0.28 |
| `gpt-5.6-sol` | $5.00 | $0.50 | $30.00 |

Per-token list ratios: **35.7× on input, 107× on output, 179× on cached
input.** GPT-5.6-Sol doubles to $10/$45 above 272K input tokens — never
reached here.

DeepSeek has 2× peak-hour pricing (09:00–12:00 and 14:00–18:00 Beijing),
confirmed in effect. **Both batches ran entirely off-peak** (Beijing
02:47–03:06 and 03:45–05:21), so standard rates applied throughout and no
mixed-rate disentangling is needed.

### 7.2 The core measurement problem

`codex exec` reports **one aggregate token count with no input/output split**,
and the session rollout files carry no accounting. An exact cost therefore
cannot be computed from the logs, for either model. Two responses:

- **For DeepSeek, use ground truth.** The account balance was read before and
  after each batch. The delta is the real cost, no modelling required.
- **For GPT, bracket it.** Report the cost if every token were input (floor)
  and if every token were output (ceiling), plus a mix-matched central
  estimate — always labelled as modelled.

### 7.3 DeepSeek — measured

| Batch | Balance before | after | **cost** | tokens | effective rate | implied output share |
|---|---|---|---|---|---|---|
| Easy suite | $9.97 | $9.84 | **$0.13** | 817,349 | $0.159/1M | 13.6% |
| h4 smoke run | $9.84 | $9.83 | $0.01 | 77,189 | — | — |
| Hard suite | $9.83 | $9.57 | **$0.26** | 1,192,235 | $0.218/1M | 55.8% |
| **Total** | $9.97 | $9.57 | **$0.40** | 2,086,773 | | |

Balances read to cents, so each batch figure carries roughly ±$0.005 (±2–4%).

**The output share quadrupled from the easy suite to the hard one (13.6% →
55.8%).** Reasoning tokens bill as output, and hard tasks at `high` effort
generate far more of them. This is the single most useful new fact in the
experiment, because it invalidates a tempting shortcut — see §7.5.

### 7.4 GPT — modelled, never spent

Plain `codex` authenticates via ChatGPT OAuth, so these tokens billed against
the subscription. **Marginal out-of-pocket was $0.** The figures below are an
economic proxy for what identical work would cost through the API — legitimate
for comparison, never to be presented as money spent.

**Easy suite — 269,857 tokens:**

| Basis | Cost | Per passing task (15) |
|---|---|---|
| All cached input (absolute floor) | $0.13 | $0.009 |
| All fresh input | $1.35 | $0.090 |
| Mix-matched to 13.6% output | **$2.27** | **$0.151** |
| All output (ceiling) | $8.10 | $0.540 |

**Hard suite — 591,441 tokens:**

| Basis | Cost | Per passing task (15) |
|---|---|---|
| All cached input | $0.30 | $0.020 |
| All fresh input | $2.96 | $0.197 |
| Mix-matched to 55.8% output | **$11.20** | **$0.747** |
| All output | $17.74 | $1.183 |

Combined across both suites: 861,298 tokens → **$4.31 all-input, $25.84
all-output.**

The mix-matched row is the most defensible central estimate and also the
weakest assumption in the report: it transfers DeepSeek's measured
input/output ratio onto a different harness that demonstrably behaves
differently — GPT used roughly half the tokens for the same work. If GPT's
reasoning share is lower than DeepSeek's, its true cost sits below the
mix-matched figure.

### 7.5 Cost per passing task, and why the ratio is a band

| Suite | DeepSeek (measured) | GPT (modelled) | Ratio |
|---|---|---|---|
| Easy | $0.0087 | $0.090 – $0.540 | 10.4× – 62.3× |
| Hard | $0.0186 | $0.197 – $1.183 | 10.6× – 63.7× |

**The mix does not cancel out of the ratio.** DeepSeek's output costs 2× its
input; GPT's costs 6×. A reasoning-heavy mix therefore penalises GPT
disproportionately, and the ratio *widens* as the output share rises. At the
mix-matched central estimate the easy suite gives ~17× and the hard suite
~40×, from the same calculation applied to different mixes.

Two conclusions follow:

1. **A ratio quoted without naming its assumed mix is meaningless.** The
   honest statement is: DeepSeek's advantage is at least ~10× on the most
   conservative reading, and plausibly 40–60× on reasoning-heavy work.
2. **The list-price ratio badly overstates the saving on the easy suite and
   understates it on the hard one.** The 35.7×/107× sticker figures are per
   *token*; DeepSeek gives much of that back by consuming 2–3× the tokens, and
   then wins some of it back again when reasoning dominates.

---

## 8. Self-report fidelity ("hallucination")

The literature flags V4 for confident false success claims on longer
autonomous runs. The harness captures both the model's closing self-report and
the blind grader verdict, making "claimed success but failed" directly
countable.

| Suite | DeepSeek | GPT |
|---|---|---|
| Easy | 0 of 15 | 0 of 15 |
| Hard | **1 of 15** | 0 of 15 |

The single case is `h4` trial 1. Its closing message claimed completion and
described verifying against "a 36-case battery covering all of the above;
every case passes." That claim was *accurate about work it had actually
done* — the run really did build a full recursive-descent parser and really
did pass its own tests. It asserted completion on the strength of
self-authored tests that missed a case. **That is ordinary self-verification
failure, not confabulation.**

Scope this correctly. Easy-suite runs lasted 15–48s; hard-suite runs had a
median of 118s and a maximum of 382s. Both are far short of the long-horizon
autonomous sessions where the reported failure mode appears. **This experiment
provides no evidence either way about DeepSeek's honesty on genuinely
long-running tasks.** Treating it as a clean bill of health would overread the
data.

The operational implication is independent of the diagnosis: verify agent
output against tests *you* wrote, not against the agent's own.

---

## 9. Threats to validity

- **n=3 per cell.** Adequate for a 30/30 sweep, too thin for a one-run gap.
  The headline accuracy difference is a single failure.
- **Grader reliability was the largest error source.** Two defects were found
  and fixed; both wronged the same model. There is no strong reason to believe
  a third does not exist. Any future DeepSeek failure on this suite should be
  treated as suspect until the grader is checked.
- **Single effort level.** Both arms at `high`; GPT ran below its own default.
- **Task authorship bias.** The suites were written by the same agent that
  analysed the results. Difficulty calibration and "what counts as inferable"
  in `h4` are judgement calls that shape the outcome.
- **GPT cost is entirely modelled.** No ground truth exists for it here.
- **Machine-relative timing.** `h1`'s budgets are calibrated to this Apple
  silicon machine; the naive/correct separation would differ elsewhere.
- **Off-peak pricing only.** Peak windows double DeepSeek's rates and would
  roughly halve the advantage.
- **Batch interruptions.** The hard batch was killed twice by something
  outside the script. Runs were resumed, not restarted; no cell was executed
  twice and no tokens were double-counted. The cause was not diagnosed.

---

## 10. Conclusions

**On accuracy.** For well-specified work — including work substantially
harder than the first suite suggested was safe — DeepSeek V4-Flash matches
GPT-5.6-Sol. Across 60 runs the two models differ by one failure. DeepSeek
handled performance rewrites, concurrency correctness, multi-module debugging
across ~1,000 lines, and multi-step chained failures at parity.

**On latency.** DeepSeek is faster, consistently: 2.1× on the easy suite and
1.7× on the hard one, winning 9 of 10 tasks. On latency alone it would be the
better default even at identical prices.

**On cost.** DeepSeek's total measured spend for the 30 benchmark runs across
both suites was **$0.39** ($0.40 including the pre-batch smoke run). The
equivalent GPT work was free at the margin under a ChatGPT
subscription, and would cost $4.31–$25.84 at API list price. Per passing task,
DeepSeek is at minimum ~10× cheaper and plausibly 40–60× on reasoning-heavy
work.

**On the boundary.** The requested "boundary, not a winner" does exist, but it
is not the difficulty boundary the brief anticipated. Both models handled
everything hard-but-*specified*. The only task that separated them was the
only one with no stated acceptance criteria, and the failure was an unhandled
input shape at the edge of an inferred spec. **The boundary this experiment
located is specification quality, not difficulty** — and it rests on one
failure in fifteen, so it is a hypothesis worth testing, not an established
fact.

### Recommendation

- **Default to DeepSeek** for tasks with a clear contract: a failing test, a
  written spec, a reproducible bug, a defined refactor. Evidence supports this
  well beyond trivial work.
- **Prefer GPT** where requirements are vague and the model must choose the
  contract itself, and for long autonomous runs — the latter on precaution
  about untested territory, not on observed weakness.
- **Verify with your own tests, always.** At under two cents per passing task,
  running DeepSeek and checking it against tests you wrote costs an order of
  magnitude less than running GPT alone. The one self-report failure observed
  was precisely a case of trusting the agent's own verification.
- **Never quote a cost ratio without its assumed token mix.**

---

## 11. What remains untested

1. **Genuinely long horizons.** Nothing here ran beyond ~6 minutes. This is
   where V4's reported failure mode lives and where the GPT recommendation
   currently rests on precaution rather than data.
2. **Large context.** `h3` is 993 lines and strained neither model.
3. **Underspecification, properly.** The entire accuracy difference lives in
   one task and one failure. If any finding deserves a dedicated follow-up
   with more trials and several underspecified tasks, it is this one.
4. **The `xhigh` axis.** GPT ran below its own default throughout.
5. **Other GPT-5.6 variants.** `gpt-5.6-terra` and `gpt-5.6-luna` are
   configured locally and untried, as are `gpt-5.5`, `gpt-5.4`,
   `gpt-5.4-mini`, and `gpt-5.3-codex-spark`.
6. **Peak-hour economics.** All measurements are off-peak.

A follow-up round costs roughly $0.25 on the DeepSeek side.

---

## 12. Reproduction

```bash
# easy suite
cd bench
./run_bench.sh deepseek 1        # all 5 tasks, trial 1
./run_bench.sh gpt      1
./analyze.py                     # pass rates, latency, tokens, cost bands
./claims.py                      # self-report vs grader, failures only

# hard suite
cd bench/hard
./resume_hard.sh                 # full matrix, skips completed cells
./run_hard.sh deepseek 1 h3_bigcontext     # single task
./regrade.py h3_bigcontext --write         # replay a corrected grader
../analyze.py hard/results_hard.csv
```

Environment knobs: `EFFORT` (default `high`, `default` uses each profile's
own), `LIMIT` (hard-suite per-run watchdog, default 900s).

### File inventory

| Path | Purpose |
|---|---|
| `bench/tasks/`, `bench/hidden/` | easy suite fixtures and blind graders |
| `bench/hard/tasks/`, `bench/hard/hidden/` | hard suite fixtures and blind graders |
| `bench/run_bench.sh`, `bench/hard/run_hard.sh` | single-trial runners |
| `bench/hard/resume_hard.sh` | resumable full-matrix driver |
| `bench/hard/regrade.py` | replay a corrected grader over saved runs |
| `bench/analyze.py` | pass rates, medians, cost bands, ratios |
| `bench/claims.py` | pairs self-reports with grader verdicts |
| `bench/results.csv`, `bench/hard/results_hard.csv` | raw per-run results |
| `bench/**/runs/*.log`, `*.grade` | agent stdout and grader output per run |
| `bench/**/work/` | retained per-run fixture copies (enables re-grading) |
| `bench/hard/README.md` | hard-suite design notes and validation table |

### Operational gotchas (paid for, do not rediscover)

- **Never set `forced_login_method = "api"`** in a Codex profile. It is not
  profile-scoped: selecting the profile deletes `~/.codex/auth.json` and logs
  you out of ChatGPT for plain `codex` too. Recovery is an interactive
  `codex login`.
- **The custom catalog needs `"tool_mode": "standard"`.** GPT's
  `"code_mode_only"` makes Codex emit a custom `exec` tool that DeepSeek
  rejects: `Unsupported custom tool: 'exec'. Only 'apply_patch' is supported.`
- **Test Codex config changes in an isolated `CODEX_HOME`** — some settings
  mutate real auth state merely on load.
- **`web_search_tool_type`** accepts only `text` or `text_and_image`.
- **Bash timeouts** ≥300s; agent runs routinely exceed 120s.
- **`< /dev/null`** or `codex exec` blocks on stdin.
- **The token count is on the line *after* `tokens used`**, so line-based
  greps miss it.
- `402 Payment Required: Insufficient Balance` means top up at
  platform.deepseek.com; nothing is misconfigured.

---

## Appendix A — full per-run data, hard suite

| model | task | trial | agent s | grade s | tokens | passed | tests failed |
|---|---|---|---|---|---|---|---|
| deepseek | h1_perf | 1 | 306 | 0 | 104,084 | 1 | 0 |
| deepseek | h1_perf | 2 | 382 | 0 | 94,864 | 1 | 0 |
| deepseek | h1_perf | 3 | 256 | 0 | 122,280 | 1 | 0 |
| deepseek | h2_concurrency | 1 | 87 | 1 | 65,702 | 1 | 0 |
| deepseek | h2_concurrency | 2 | 98 | 1 | 64,403 | 1 | 0 |
| deepseek | h2_concurrency | 3 | 67 | 0 | 60,764 | 1 | 0 |
| deepseek | h3_bigcontext | 1 | 83 | 0 | 74,039 | 1 | 0 |
| deepseek | h3_bigcontext | 2 | 134 | 0 | 78,747 | 1 | 0 |
| deepseek | h3_bigcontext | 3 | 118 | 0 | 82,300 | 1 | 0 |
| deepseek | h4_underspec | 1 | 266 | 0 | 92,389 | **0** | 1 |
| deepseek | h4_underspec | 2 | 322 | 0 | 93,820 | 1 | 0 |
| deepseek | h4_underspec | 3 | 170 | 0 | 75,777 | 1 | 0 |
| deepseek | h5_longhorizon | 1 | 68 | 0 | 63,111 | 1 | 0 |
| deepseek | h5_longhorizon | 2 | 39 | 0 | 58,812 | 1 | 0 |
| deepseek | h5_longhorizon | 3 | 55 | 0 | 61,143 | 1 | 0 |
| gpt | h1_perf | 1 | 279 | 1 | 35,262 | 1 | 0 |
| gpt | h1_perf | 2 | 285 | 1 | 39,998 | 1 | 0 |
| gpt | h1_perf | 3 | 209 | 1 | 24,861 | 1 | 0 |
| gpt | h2_concurrency | 1 | 346 | 1 | 49,129 | 1 | 0 |
| gpt | h2_concurrency | 2 | 219 | 1 | 30,350 | 1 | 0 |
| gpt | h2_concurrency | 3 | 241 | 1 | 45,908 | 1 | 0 |
| gpt | h3_bigcontext | 1 | 139 | 0 | 38,693 | 1 | 0 |
| gpt | h3_bigcontext | 2 | 121 | 0 | 34,600 | 1 | 0 |
| gpt | h3_bigcontext | 3 | 168 | 0 | 66,930 | 1 | 0 |
| gpt | h4_underspec | 1 | 180 | 0 | 35,449 | 1 | 0 |
| gpt | h4_underspec | 2 | 196 | 0 | 45,868 | 1 | 0 |
| gpt | h4_underspec | 3 | 235 | 0 | 59,680 | 1 | 0 |
| gpt | h5_longhorizon | 1 | 99 | 0 | 33,731 | 1 | 0 |
| gpt | h5_longhorizon | 2 | 151 | 0 | 28,579 | 1 | 0 |
| gpt | h5_longhorizon | 3 | 122 | 0 | 22,403 | 1 | 0 |

Easy-suite per-run data is in `bench/results.csv`; no run there failed, and
none carried a note.

## Appendix B — the two failing-run details

**`deepseek / h4_underspec / trial 1`** — `ERROR: test_extra_whitespace`.
`evaluate("   age   >   29   ", rec)` raised
`ValueError: invalid character '   ' at position 15`. Leading and internal
whitespace handled; trailing not. 19 of 20 tests passed. The run's closing
message claimed success. Counted as the sole self-report failure.

**`deepseek / h3_bigcontext / trial 2`** and **`deepseek / h4_underspec /
trial 2`** — both originally scored as failures, both **false**, caused by the
two grader defects in §6. Re-graded to passes. Retained here because the
uncorrected numbers appear in the session log and would otherwise look like a
discrepancy.
