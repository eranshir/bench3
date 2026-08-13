# Handoff: DeepSeek V4-Flash vs GPT-5.6-Sol — performance & cost comparison

**Written:** 2026-08-01. **Author:** previous Claude Code session.
**Your job:** run the benchmark below and produce an evidence-based verdict on
whether DeepSeek V4-Flash-0731 is good enough to displace GPT-5.6-Sol for some
share of Eran's Codex CLI work, and at what cost ratio.

Everything needed is already built and validated. You should not need to set
anything up — start at "How to run".

---

## 1. What already exists

| Thing | Location | Notes |
|---|---|---|
| DeepSeek Codex profile | `~/.codex/deepseek.config.toml` | selected via `--profile deepseek` |
| DeepSeek model catalog | `~/.codex/deepseek.models.json` | hand-authored; Codex ships none |
| `deepcodex` command | `~/.local/bin/deepcodex` | executable, on PATH, Keychain-backed |
| Plain `codex` | homebrew, v0.144.1 | GPT-5.6-Sol, ChatGPT OAuth, `xhigh` |
| API key | macOS Keychain, service `deepseek-api-key` | personal scope, not aegis |
| Claude Code subagents | `~/.claude/agents/{deepseek,gpt-codex}.md` | delegation relays |
| Benchmark | `bench/` (this repo) | 5 tasks + runner, validated |

Both CLIs are confirmed working end to end. A real DeepSeek run completed a
bugfix task in 17s / 55,007 tokens and passed the hidden grader.

**Do not use the Claude Code subagents to run the benchmark.** They add a Sonnet
relay layer whose tokens and latency would pollute the measurement. Use
`bench/run_bench.sh`, which calls the CLIs directly. The subagents are for
ad-hoc interactive use.

---

## 2. The benchmark

Five tasks in `bench/tasks/`, each a self-contained Python fixture with a
`PROMPT.txt`. Difficulty ascends:

| Task | Type | What it probes |
|---|---|---|
| `t1_bugfix` | single-file bugfix | off-by-one in nearest-rank percentile |
| `t2_multifile` | multi-file feature | env-var overrides threaded through 3 files, type coercion, precedence |
| `t3_tdd` | implement from tests | `parse_duration()`; spec lives only in the test file |
| `t4_debug` | subtle debugging | mutable default arg + lossy in-place discount; needs a new `subtotal()` |
| `t5_refactor` | constrained refactor | callback → lazy iterative generator; must not blow recursion at depth 10k |

**Grading is objective and blind.** Each task has a hidden test in
`bench/hidden/<task>_test.py` that the model never sees; it is copied in only
after the run. The hidden tests deliberately cover cases the visible prompt does
not, so a model that special-cases the stated examples fails.

Both directions are validated: all 5 hidden tests **fail** on the unmodified
fixtures, and I confirmed correct solutions **pass** for `t1` and `t5` (the
strictest). No task is accidentally pre-passing or impossible.

---

## 3. How to run

```bash
cd bench
./setup_bench.sh                 # regenerate fixtures (idempotent; only if needed)

./run_bench.sh deepseek 1        # all 5 tasks, trial 1
./run_bench.sh gpt      1
./run_bench.sh deepseek 2        # ...repeat for trials 2 and 3
./run_bench.sh gpt      2
./run_bench.sh deepseek 3
./run_bench.sh gpt      3
```

Results append to `bench/results.csv`:
`model,task,trial,effort,seconds,tokens,passed,tests_failed,notes`

Raw stdout per run is in `bench/runs/*.log`; grader output in `*.grade`.
Each run gets a fresh copy of the fixture in `bench/work/` — no contamination.

**Run 3 trials.** These agents are stochastic; n=1 will mislead you on both
pass rate and token count. 30 runs total, roughly 30–90 minutes wall-clock.

### Effort is pinned, deliberately

The two profiles default differently — DeepSeek `high`, GPT `xhigh`. Comparing
them as-configured would confound the model difference with an effort
difference, especially on latency. `run_bench.sh` therefore pins **both** to
`high` by default via `-c model_reasoning_effort=...`.

Override if you want a second axis:
```bash
EFFORT=xhigh   ./run_bench.sh gpt 4
EFFORT=default ./run_bench.sh gpt 5    # each profile's own setting
```
The effort used is recorded per row, so mixed runs stay analyzable. Report the
matched-effort comparison as the headline; anything else is a footnote.

---

## 4. Cost methodology — read this before quoting any dollar figure

There is a real asymmetry here, and the honest write-up has to name it.

### Published prices (per 1M tokens)

| | input | cached input | output |
|---|---|---|---|
| `deepseek-v4-flash` | $0.14 | $0.0028 | $0.28 |
| `gpt-5.6-sol` | $5.00 | $0.50 | $30.00 |

GPT-5.6-Sol doubles to $10 / $45 for any request over 272K input tokens.
DeepSeek has documented 2x peak-hour pricing (09:00–12:00 and 14:00–18:00
Beijing) with an effective date still listed as pending — **check whether it has
taken effect** before quoting, and note the run's wall-clock time.

### Three problems you must handle honestly

1. **`codex exec` reports only an aggregate token count.** There is no
   input/output split on stdout, and I confirmed the session rollout files in
   `~/.codex/sessions/` carry no token accounting at all. So you cannot compute
   an exact cost from the logs. Do not pretend otherwise.

   Handle it by reporting a **range**: cost if all tokens were input (floor) and
   if all were output (ceiling). Agent loops are heavily input-dominated because
   the whole context is resent each turn, so the true figure sits near the floor
   — say that, but show the range.

2. **DeepSeek has a hard ground truth; use it.** Note the account balance at
   platform.deepseek.com *before* and *after* the batch. The delta is the real
   dollar cost, no modelling required. This is the single most valuable number
   in the whole exercise — do not skip it.

3. **GPT costs are modelled, not measured.** Plain `codex` authenticates via
   ChatGPT OAuth, so those tokens bill against Eran's subscription quota, not
   per-token. Marginal out-of-pocket is effectively $0 until he hits a rate
   limit. Applying API list price to GPT is an *economic proxy* for what the
   same work would cost via API — legitimate for comparison, but label it
   clearly as modelled. Never present it as money actually spent.

---

## 5. What to produce

A written comparison covering:

- **Pass rate per task per model** (out of 3 trials), plus which specific hidden
  tests failed and why — read the `.grade` files. "DeepSeek failed t4" is much
  less useful than "DeepSeek fixed the mutable default but never added
  `subtotal()`, failing 1 of 6".
- **Median wall-clock and tokens per task**, matched effort.
- **Cost**: DeepSeek measured from balance delta; GPT modelled from list price
  with the range and the caveat above.
- **The cost-per-*passing*-task ratio.** This is the number that actually
  matters. A model that is 100x cheaper but passes half as often is 50x cheaper
  in practice, not 100x — and if it fails the hard tasks specifically, the
  cheapness is worth much less than the ratio suggests.
- **A recommendation with a boundary**, not a winner. The useful output is
  something like "DeepSeek for t1/t3-shaped work, GPT for t4/t5-shaped work",
  with the observed evidence for where the line falls.

Watch for the failure mode the literature flags for V4: high hallucination rate
on longer autonomous runs. If DeepSeek's summary claims success where the grader
disagrees, that is a headline finding — quantify it (how many runs claimed
success but failed the hidden tests?). The runner captures both, so this is
directly measurable.

---

## 6. Gotchas already paid for — do not rediscover these

- **Never set `forced_login_method = "api"`** in a Codex profile. It is not
  profile-scoped; selecting the profile *deletes* `~/.codex/auth.json` and logs
  Eran out of ChatGPT for plain `codex` too. It cost a re-login last session.
  Recovery is `codex login`, which is interactive — you cannot do it for him.
- **The catalog needs `"tool_mode": "standard"`.** GPT's `"code_mode_only"`
  makes Codex emit a custom `exec` tool that DeepSeek rejects outright:
  `Unsupported custom tool: 'exec'. Only 'apply_patch' is supported.`
- **Test Codex config changes in an isolated `CODEX_HOME`** — some settings
  mutate real auth state merely on load.
- **Custom catalog entries need many required fields** (e.g. `base_instructions`).
  Build them by deep-copying an entry from `codex debug models` and overriding
  only what differs. `web_search_tool_type` accepts only `text` or
  `text_and_image` — not `none`.
- **Bash timeouts**: agent runs routinely exceed 120s. Use ≥300000 ms.
- **stdin**: always append `< /dev/null` or `codex exec` blocks waiting on input.
- **`--skip-git-repo-check`**: needed outside a git repo. This project is not a
  git repo.
- `402 Payment Required: Insufficient Balance` means top up at
  platform.deepseek.com — nothing is misconfigured.
- The token count is on the line *after* `tokens used`, so line-based greps miss
  it. The runner already handles this.

---

## 7. Budget guardrail

The DeepSeek side of a full 3-trial run is cheap — roughly 850K tokens, well
under a dollar even at output rates. The GPT side consumes subscription quota
rather than dollars.

If DeepSeek's balance runs out mid-batch, rows will land with
`notes=insufficient_balance` and `passed=0`. **Those are not model failures** —
exclude them and tell Eran to top up, rather than scoring them as losses.

---

## 8. Context note

`~/Documents/Projects/deepseek` is personal-scope: no git remote, not under
`~/Documents/Projects/mithran/`, and the API key deliberately lives in the macOS
Keychain rather than aegis-secret (which is Mithran-scoped). Keep it that way.
If this work ever gets pointed at Nexar code, that becomes a vendor/data-handling
decision requiring a CISO request in `getnexar/ciso-requests` first.
