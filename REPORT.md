# DeepSeek V4-Flash-0731 vs GPT-5.6-Sol — benchmark results

> **Superseded by [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md)**, which
> consolidates both suites plus the harness, task designs, validation
> evidence, cost methodology and threats to validity. This file is retained as
> the running narrative log, written batch by batch as the work happened.
>
> **Part 1 (below)** is the original suite, which saturated at 30/30.
> **[Part 2](#part-2--the-hard-suite)** is the harder suite built afterwards,
> which did separate the models.


**Run:** 2026-08-01, 21:47–22:06 IDT (Beijing 02:47–03:06, **off-peak throughout**).
**Configuration:** 5 tasks × 3 trials × 2 models = 30 runs, `model_reasoning_effort=high`
pinned on both. Blind grading against hidden tests the models never saw.
**Raw data:** `bench/results.csv`, `bench/runs/*.log`, `bench/runs/*.grade`.

---

## 1. Headline: the benchmark saturated

**Both models passed 30/30.** Every task, every trial, zero hidden-test failures,
zero CLI errors, zero excluded rows.

This is the most important thing to say up front, because it changes what the
exercise can support. The handoff asked for a recommendation shaped like
"DeepSeek for t1/t3-shaped work, GPT for t4/t5-shaped work." **The data cannot
support a boundary of that kind, because no boundary appeared.** The difficulty
ramp that was designed into the suite — through to a constrained
callback→lazy-generator refactor that must survive depth 10,000 — did not
separate these two models at `high` effort.

Reporting a boundary anyway would be manufacturing a distinction the evidence
does not contain. What the run *does* establish, decisively, is the cost and
latency profile, and the absence of the hallucination failure mode. Those are
real findings and they are below.

I sanity-checked the passes rather than trusting the counter, because a clean
sweep is exactly the result most likely to indicate a broken grader:

- `t5` (DeepSeek) — a genuine iterative stack-based generator, `reversed()` to
  preserve pre-order, callback `walk` removed, laziness intact. Not a
  special-case fit to the prompt's examples.
- `t4` (both) — both produced real fixes with a working `subtotal()`. GPT used
  `Decimal` with explicit `ROUND_HALF_UP`; DeepSeek used floats plus a
  defensive `list(items)` copy in the constructor.

The grader is sound and was independently validated in both directions last
session. The saturation is real, not an artifact.

---

## 2. Pass rate, latency, tokens (matched effort = `high`)

| Task | DS pass | DS med s | DS med tok | GPT pass | GPT med s | GPT med tok |
|---|---|---|---|---|---|---|
| `t1_bugfix` | 3/3 | 16 | 53,701 | 3/3 | 45 | 18,427 |
| `t2_multifile` | 3/3 | 30 | 56,568 | 3/3 | 65 | 17,542 |
| `t3_tdd` | 3/3 | 21 | 54,418 | 3/3 | 37 | 12,298 |
| `t4_debug` | 3/3 | 26 | 54,904 | 3/3 | 58 | 17,794 |
| `t5_refactor` | 3/3 | 23 | 54,765 | 3/3 | 40 | 16,749 |

| | DeepSeek | GPT |
|---|---|---|
| Total tokens | 817,349 | 269,857 |
| Total wall-clock | 369 s | 776 s |
| Median run | 23 s (15–48) | 51 s (34–92) |
| Median tokens | 54,765 (46K–59K) | 16,749 (12K–33K) |

**DeepSeek is ~2.1× faster wall-clock and burns ~3.0× the tokens.** It won on
latency in all 5 tasks. Its token consumption is also strikingly flat —
46K–59K regardless of task difficulty, a ~1.3× spread — while GPT's varies
2.7× with the work. DeepSeek appears to spend a large fixed context budget per
run; GPT scales its spend to the problem.

---

## 3. Cost

### DeepSeek — measured, not modelled

**Account balance $9.97 → $9.84. Actual cost of the 15-run batch: $0.13.**

This is ground truth, and it lets us calibrate rather than guess. Against the
817,349 reported tokens, $0.13 implies an effective blended rate of
$0.159/1M — slightly *above* the all-input rate of $0.14. Solving the mix
(assuming no cache discount reached these requests) gives roughly **13.6%
output, 86.4% input**, which is what an input-dominated agent loop should look
like. The bracket predicted from the logs was $0.114 (all-input) to $0.229
(all-output); the measured figure sits near the input floor, as expected.

Precision caveat: the balance reads to cents, so $0.13 carries roughly ±$0.005,
about ±4%.

### GPT — modelled, never money spent

Plain `codex` authenticates via ChatGPT OAuth, so these tokens billed against
Eran's subscription quota. **Marginal out-of-pocket was $0.** Everything below
is an *economic proxy* for what identical work would cost through the API.

| Basis | Modelled cost, 15 runs |
|---|---|
| All tokens as cached input (absolute floor) | $0.13 |
| All tokens as fresh input | $1.35 |
| **Mix-matched to DeepSeek's measured 86/14 split** | **$2.27** |
| All tokens as output (ceiling) | $8.10 |

The mix-matched figure is the most defensible central estimate, but it carries
a real assumption: it transfers DeepSeek's measured input/output ratio onto
GPT, and the two harnesses demonstrably behave differently. Treat $2.27 as an
estimate inside a $1.35–$8.10 band, not a measurement.

### Cost per *passing* task

Because both models went 15/15, the pass-rate adjustment is a no-op here and
the cost ratio passes through unchanged.

| | Cost per passing task |
|---|---|
| DeepSeek (measured) | **$0.0087** |
| GPT (modelled, mix-matched) | **$0.151** |

**Ratio: ~17× cheaper.** On a like-for-like all-input basis it is ~10×.

The honest headline is that **the effective advantage is roughly 10–17×, not
the 36× (input) or 107× (output) the list prices imply.** DeepSeek gives back
about two-thirds of its per-token price advantage by consuming ~3× the tokens.
Anyone quoting the sticker ratio for agent work is overstating the saving by
2–3×.

---

## 4. The hallucination check

The literature flags V4 for confident false success claims on longer autonomous
runs. **It did not appear: 0 of 15 DeepSeek runs claimed success while failing
the hidden test.** There were no failures at all, so there was nothing to
misreport.

This is a genuine null result, but scope it correctly: these runs lasted 15–48
seconds. That is nowhere near the "longer autonomous runs" regime where the
failure mode is reported. **This run provides no evidence either way about
DeepSeek's honesty on long-horizon tasks** — it only shows the mode is absent
on short, well-specified ones. Treating it as a clean bill of health would
overread the data.

---

## 5. Recommendation

**For work resembling this suite — single-file bugfixes, small multi-file
features, TDD against a given spec, contained debugging, bounded refactors —
DeepSeek V4-Flash is a straight substitute.** Equal accuracy, half the
latency, and ~10–17× cheaper on a real measured basis. On latency alone it
would be the better default even if the prices were identical.

**Where the line falls is genuinely unknown**, and that is the main gap in this
exercise. The suite topped out below both models' capability. What the evidence
supports:

- **Switch by default** for short, well-specified, verifiable tasks.
- **Keep GPT** for long-horizon autonomous work, until the hallucination
  question is tested at a duration where it actually bites. That is a
  precaution about untested territory, not an observed weakness.
- **Verification stays cheap and mandatory.** At $0.0087 a task, running
  DeepSeek and checking its output against tests costs far less than GPT alone.
  The economics favour verify-don't-trust.

### What a discriminating benchmark would need

To locate the boundary, the next run should raise difficulty until something
breaks:

1. **Longer horizons** — tasks needing 10+ tool calls over many minutes, which
   is where the hallucination mode is reported and where DeepSeek's flat token
   budget may become a real constraint.
2. **Larger context** — the flat 46K–59K spend hints at a working-set ceiling;
   a task spanning a genuinely large codebase would probe it.
3. **Underspecified prompts** — every task here stated its acceptance criteria.
   Ambiguity is where model quality usually separates.
4. **The `xhigh` axis** — GPT's own default was held back to `high` for
   matching. Whether `xhigh` buys GPT anything is untested.

Cheap to do: the DeepSeek side of a run this size costs about 13 cents.

---

## 6. Caveats

- n=3 per cell. Fine for 30/30, too thin for small pass-rate differences.
- One effort level (`high`) only.
- Off-peak Beijing pricing throughout. Peak windows (09:00–12:00, 14:00–18:00
  Beijing) double DeepSeek's rates, which would compress the advantage to
  roughly 5–9×. **Timing matters to the economics** — from Israel, peak
  corresponds to about 04:00–07:00 and 09:00–13:00 local.
- The GPT dollar figure is modelled throughout and was never money spent.

---

# Part 2 — the hard suite

**Run:** 2026-08-01 22:45 – 2026-08-02 00:21 IDT (Beijing 03:45–05:21,
**off-peak throughout**, so standard DeepSeek rates again).
**Configuration:** 5 new tasks × 3 trials × 2 models = 30 runs,
`model_reasoning_effort=high` pinned on both. Models: `deepseek-v4-flash` and
`gpt-5.6-sol`.
**Raw data:** `bench/hard/results_hard.csv`, `bench/hard/runs/`.
**Suite design and validation:** `bench/hard/README.md`.

## 1. The suite separated them — barely

| Task | probes | DeepSeek | GPT |
|---|---|---|---|
| `h1_perf` | sub-quadratic rewrite under a wall-clock budget | 3/3 | 3/3 |
| `h2_concurrency` | races + lock-order deadlock | 3/3 | 3/3 |
| `h3_bigcontext` | 3 bugs across a 993-line, 15-module package | 3/3 | 3/3 |
| `h4_underspec` | infer a spec from 3 examples, no grammar | **2/3** | 3/3 |
| `h5_longhorizon` | 4 chained defects, each masking the next | 3/3 | 3/3 |
| **Total** | | **14/15** | **15/15** |

One failure separates them, in one task. That is a real difference and it is
also a thin one — n=3 per cell cannot distinguish "DeepSeek is worse at
underspecified work" from "DeepSeek lost one coin flip."

**The single failure:** `h4` trial 1 rejected `"   age   >   29   "` —
its tokenizer handled leading and internal whitespace but not trailing. Every
other assertion in that run passed. The two later trials passed outright.

Worth stating plainly: the tasks were built to be hard enough to break both
models, and mostly they did not. Both cleared a two-heap median rewrite, a
lock-order deadlock, three bugs buried across fifteen modules, and a
four-link chained-failure hunt, on essentially every attempt.

## 2. Two grader bugs, both of which wronged DeepSeek

I found and fixed two defects in my own hidden tests, each of which scored a
*correct* DeepSeek solution as a failure:

1. **h3's synthetic case sat exactly on a rounding boundary.** The unrounded
   total was `18427.4999…`, which Decimal's 28-digit context rounds to
   `.500…` and then up. It was grading a rounding-aggregation preference
   rather than the three planted bugs. The four real tenants were unaffected —
   verified before changing anything.
2. **h4's no-`eval` check was a regex** that matched the phrase
   "no eval()/exec()" inside the model's own docstring. Now an `ast` walk for
   real calls.

Both were fixed and every affected run re-graded from its saved work
directory via `bench/hard/regrade.py` — no model re-runs, no extra spend.
**Uncorrected, DeepSeek would have scored 12/15 rather than 14/15.** The
headline difference between the models is one failure; grader noise was
about to be twice that size. Any future run of this suite should treat a
DeepSeek failure as suspect until the grader is checked.

## 3. Latency and tokens

| | DeepSeek | GPT |
|---|---|---|
| Total wall-clock | **2,451 s** | 2,990 s |
| Median run | **118 s** (55–382) | 196 s (99–346) |
| Total tokens | 1,192,235 | **591,441** |
| Median tokens | 75,777 | **35,449** |

The Part 1 pattern holds in direction but compresses. DeepSeek is still
faster (1.7× on median, was 2.2×) and still heavier (2.0× the tokens, was
3.0×). Its token spend is no longer flat: it ranged 58K–122K here against a
tight 46K–59K on the easy suite, so the earlier "fixed context budget"
reading was an artifact of tasks that were too easy to stress it.

## 4. Cost

### DeepSeek — measured

**Balance $9.83 → $9.57. Actual cost of the 15-run batch: $0.26.**

Against 1,192,235 tokens that is an effective **$0.218/1M**, which implies
roughly a **56% output share** — versus 13.6% on the easy suite. Reasoning
tokens bill as output, and hard tasks at `high` effort generate a lot of
them. This is the most useful new fact in Part 2, and it changes the cost
model rather than just refining it.

### GPT — modelled, never money spent

Still ChatGPT-OAuth billed, so marginal out-of-pocket was **$0**.

| Basis | 15 runs | vs DeepSeek's measured $0.26 |
|---|---|---|
| All tokens as fresh input (floor) | $2.96 | 11× |
| Mix-matched to DeepSeek's 56% output | **$11.20** | **43×** |
| All tokens as output (ceiling) | $17.74 | 68× |

**Why the band is so wide, and why it matters.** It is tempting to assume the
mix cancels out of a ratio. It does not. DeepSeek's output costs 2× its input;
GPT's costs 6×. A reasoning-heavy mix therefore penalises GPT
disproportionately, and the ratio *widens* as the output share rises — from
~11× at the all-input floor to ~68× at the ceiling. Part 1's ~17× came from
mix-matching at a 13.6% output share; the same method at 56% gives ~43×. Both
are the same calculation on different mixes, which is precisely why a ratio
quoted without naming its assumed mix is not meaningful.

### Cost per passing task

| | Per passing task |
|---|---|
| DeepSeek (measured, 14 passes) | **$0.0186** |
| GPT (modelled, 15 passes) | $0.197 – $1.183, central ~$0.75 |

**Ratio: 11× at the most conservative reading, ~40× at the mix-matched
central estimate.** The wide band is honest: the exact figure cannot be
recovered because `codex exec` reports only an aggregate token count.

## 5. The hallucination check

**1 of 15 DeepSeek runs claimed success while failing the hidden test**
(h4 trial 1). GPT: 0 of 15.

The claim was not a fabrication about work it had not done — the run really
did build a full recursive-descent parser and really did pass its own
36-case battery, which it described accurately. It asserted completion on
the strength of self-authored tests that missed a case. That is the ordinary
failure of self-verification, not the confabulation mode the literature
flags for V4.

Scope it correctly again: median run 118s, longest 382s. Longer than Part 1's
15–48s, still far short of a genuinely long-horizon autonomous session. The
mode remains untested where it is reported to appear.

## 6. Revised recommendation

**Substitute DeepSeek by default for well-specified work, including work
considerably harder than Part 1 suggested was safe.** It matched GPT on
performance rewrites, concurrency correctness, multi-module debugging across
~1,000 lines, and multi-step chained failures — 12/12 on those four tasks,
faster on wall-clock, at a small fraction of the cost.

**The boundary this run actually found is specification quality, not
difficulty.** Both models handled everything hard-but-specified. The only
task that separated them was the only one with no stated acceptance criteria,
and the failure was an unhandled input shape at the edge of the inferred
spec. That is a coherent and plausible weakness, but it rests on one failure
in fifteen — treat it as a hypothesis to test, not an established fact.

Practical form:

- **DeepSeek** for tasks with a clear contract: a failing test, a spec, a
  reproducible bug, a defined refactor. Verify with tests you wrote, not with
  its own.
- **GPT** where the requirements are vague and the model must choose the
  contract, and for long autonomous runs — the latter still on precaution,
  not evidence.
- **Verification remains the cheap part.** At under two cents per passing
  task, running DeepSeek and checking it against your own tests costs an
  order of magnitude less than GPT alone.

### What is still untested

1. **Genuinely long horizons.** Nothing here ran beyond ~6 minutes.
2. **Large context.** `h3` is ~1,000 lines; it did not strain either model.
3. **The `xhigh` axis.** GPT's own default effort was held at `high`
   throughout both suites.
4. **Other GPT-5.6 variants.** `terra` and `luna` are configured locally and
   untried.
5. **Underspecification, properly.** One task and one failure is where the
   entire accuracy difference lives. If any finding deserves a dedicated
   follow-up, it is this one.

## 7. Caveats

- n=3 per cell. The 14/15 vs 15/15 gap is one run wide.
- Single effort level (`high`) for both models.
- Off-peak Beijing pricing throughout. Peak windows double DeepSeek's rates
  and would roughly halve the advantage.
- The GPT dollar figure is modelled and was never money spent.
- `h1`'s timing budgets are calibrated to this machine.
