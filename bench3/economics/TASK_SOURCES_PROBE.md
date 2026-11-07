# Task-source probe, 7 November 2026

The economic campaigns score routes on seven objective tasks. A routing comparison needs about 100 or
more graded tasks in the band where a cheap route sometimes fails. Terminal-Bench is too hard for cheap
routes, and the current seven are almost all solved by them. This probe tried a few tasks from each
candidate source to see which ones spread routes apart, before choosing a blend.

## What was run

- `import_tasks.py` builds tasks under `tasks/imported/<family>/<id>/` in the layout `run_agentic.py`
  already runs. It fetches from the pinned upstream at import time; nothing upstream is committed.
  `imported_tasks.json` records what was imported and how its grader validated.
- Every grader was checked in both directions where a reference exists: it fails on the fixture and
  passes on the reference. Tasks that fail this are kept out of runs (`kept: false`).
- `run_probe.py` ran each kept task on four routes at high effort, on stingray (M5 Max), DSH 0.2.1-rc.5:
  `glm53-flash-lunaroute` and `ds41-lunaroute` twice each, `claude-sonnet55-openrouter` and
  `claude-opus55-openrouter` once each. Token-billed spend: USD 11.25.

| Family | Role it stands for | Source | Grader | Kept / tried |
|---|---|---|---|---|
| `polyglot` | coder | Aider Polyglot (Exercism) | upstream tests, run hidden | 6 / 6 |
| `code-contests` | coder | Harbor code-contests, 2 per rating band | stdin/stdout cases | 6 / 6 (one-way check: no reference) |
| `swe-verified` | coder | SWE-bench Verified, sympy, 2 per time band | fail-to-pass plus tests passing with the gold patch | 4 / 6 |
| `swe-locate` | explorer | SWE-bench Verified | answer names every file and one function the gold patch edits | 6 / 6 |
| `swe-review` | reviewer | SWE-bench Verified plus public submission patches | accept/reject must equal the harness verdict | 6 / 6 |
| `primevul` | deep reviewer | PrimeVul paired test split | names the vulnerable one of two versions | 6 / 6 |
| `iac-eval` | IaC coder | IaC-Eval, 2 per difficulty band | `terraform plan` with fake credentials, then IaC-Eval's own policy rule | 3 / 6 |

## Results (passes / valid runs)

| Family | GLM 5.3 Flash | DeepSeek 4.1 Flash | Sonnet 5.5 | Opus 5.5 | Claude USD |
|---|---|---|---|---|---|
| polyglot | 8/12 | 11/12 | 3/6 | 5/6 | 1.24 |
| code-contests | 11/12 | 10/12 | 5/6 | 5/6 | 0.77 |
| swe-verified | 7/8 | 8/8 | 2/4 | 3/4 | 1.38 |
| swe-locate | 10/12 | 10/10 | 4/6 | 5/6 | 1.52 |
| swe-review | 7/12 | 10/12 | 4/6 | 5/6 | 4.83 |
| primevul | 11/12 | 11/12 | 6/6 | 6/6 | 1.10 |
| iac-eval | 1/6 | 6/6 | 1/3 | 2/3 | 0.41 |

Median wall time per run: LunaRoute routes 33–316 s, Claude routes 13–147 s. Two DeepSeek runs were
invalid because LunaRoute answered `SERVER: backend unavailable`; they count as transport failures.

## What it shows

- DeepSeek 4.1 Flash passed as often as Opus 5.5 or more often in every family, in this harness.
  GLM 5.3 Flash separates from the others on IaC (1/6) and on reviewer tasks with a bad patch
  (it accepted wrong patches in 3 of 6 runs).
- Families that spread routes: `swe-review` (the reject cases), `iac-eval`, and parts of `polyglot`.
- Families at ceiling: `primevul` (showing both versions lets a model read the fix from the difference,
  so a single-version variant is needed), `code-contests` (rating bands did not matter here), and
  `swe-locate` (one hard task of six).
- Graded binary tasks (`swe-review`, `primevul`) pass half the time by guessing; read them against 50%.

## Not proven

- Every cell is one or two runs on a handful of tasks.
- All routes ran in DSH, a harness built for DeepSeek. Claude through OpenRouter inside DSH may do
  worse than in its own harness; this probe cannot separate the model from the harness.
- About half of IaC-Eval needs a live AWS account (AMI or zone lookups, or a stale reference), and those
  tasks fail validation here.

## Runner changes in the same branch

- The agent's environment gets only its route's credential. Before, `run_agentic.py` exported every stored
  key into the shell of the model under test. Each run's session, log and work tree are scanned for any
  stored credential value; a hit marks the run invalid and its copies are not kept.
- DSH 0.2 compatibility: a committed, secret-free settings template; a fresh, primed DSH home per run
  (a reused home fell back to the default DeepSeek route after one run); a placeholder for the DeepSeek
  boot check on other routes; `session.v4.jsonl.zstd` session files.
- A run counts as valid only if its session shows the route's own provider and model.
