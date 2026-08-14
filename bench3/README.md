# bench3 — three-provider benchmark (DeepSeek / OpenAI / xAI)

Continuation of the repo's first benchmark (bench/). Now four arms through one
harness: **deepseek-v4-flash, deepseek-v4-pro, gpt-5.6-sol, grok-4.6**.

Design goals: *deep, thorough, cost-effective*. Tasks are **hardest-but-smallest**
— each is one focused, hard, small probe — and laddered hardest-first per
category so the runs find the difficulty boundary where arms separate.

## Arms

Defined in `arms.yaml` (DSH route + model + pinned effort + list prices).

| Arm | Provider route | Model | Effort | In $/M | Cached $/M | Out $/M |
|---|---|---|---|---|---|---|
| deepseek-flash | deepseek-official | deepseek-v4-flash | high | 0.14 | 0.0028 | 0.28 |
| deepseek-pro   | deepseek-official | deepseek-v4-pro   | high | 0.42 | 0.0084 | 0.87 |
| gpt-sol        | openai            | gpt-5.6-sol       | high | 5.00 | 0.50 | 30.00 |
| grok           | xai               | grok-4.6          | high | 2.00 | 0.20 | 6.00 |

Same harness and tools for every arm:
- **Agentic mode** (coding, agentic-workflow): DSH `headless` profile in an
  isolated `DSH_HOME` (`.dsh-home/`, gitignored) — identical tool surface,
  sandbox, and system prompt for all four arms; effort pinned via
  `agent-default-model` settings; exact per-call usage parsed from the session
  transcript; full trajectories retained for the qualitative explorer.
- **Single-shot mode** (reasoning, creativity, writing, tool use): one direct
  API client for all four arms (only wire params differ); exact usage from each
  response; optional function-calling (`tools.json`).

Credentials: the runner exports the user's keys from `~/.dsh/.credentials.yaml`
into the process environment (dsh's inherited-env layer wins over the store).
Keys never land in this repo.

## Cost accounting

Every run records `input_tokens, cache_read_tokens, output_tokens,
reasoning_tokens` and a computed `cost_usd` from list prices. For agentic runs
the tokens come from the session transcript (`assistant/message` usage events);
for single-shot runs from the API `usage` object. xAI additionally reports
`cost_in_usd_ticks` per response (cross-check). DeepSeek account-balance deltas
remain available as ground truth for the DeepSeek arms.

## Categories and tasks

| Category | Mode | Grading |
|---|---|---|
| coding | agentic | hidden tests (blind) + diff review |
| agentic-workflow | agentic | hidden tests (blind) + artifact checks |
| tool-use | single-shot | check.py on the emitted tool-call sequence |
| reasoning | single-shot | check.py on the final answer |
| creativity | single-shot | rubric judge (blind, shuffled) |
| writing | single-shot | rubric judge (blind, shuffled) |

Task layout: `tasks/<category>/<task>/` with `PROMPT.txt` (agentic), or
`prompt.txt` + `mode.txt` (+ `system.txt`, `tools.json`, `check.py`,
`max_tokens.txt`) for single-shot. Objective graders are validated in **both
directions**: they must fail on the shipped fixture and pass on a reference
solution.

## Running

```bash
cd bench3
./bin/init_home.sh                      # one-time: bootstrap .dsh-home
./bin/run_agentic.sh [arm] [trial] [task]     # e.g. all, 1
./bin/run_singleshot.py [arm] [trial] [task]
./bin/judge.py                           # rubric judging of subjective tasks (phase 2)
```

Results: `results/results.csv` (agentic) and `results/results_singleshot.csv`.
Raw artifacts: `runs/` (logs, grades, raw responses), `work/` (fixture
copies), `.dsh-home/sessions/` (full trajectories).

## Webapp

`webapp/` — static single-page explorer (quantitative dashboards + per-run
qualitative drill-down), generated from the results CSVs + run artifacts.
