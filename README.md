# bench3 — model benchmark harness & results

Runs identical tasks across cloud frontier models (DeepSeek V4 Flash/Pro,
GPT-5.6 Sol, Grok 4.6) and local runtimes (MTPLX · Qwen 3.8 27B) and publishes
the results — see [`docs/`](docs/) for the live site and infographic, and
[`bench3/`](bench3/) for the harness.

Historical: the original 2026-08-01 Codex-CLI comparison of deepseek-v4-flash
vs gpt-5.6-sol lives in [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md) and the
running narrative in [`REPORT.md`](REPORT.md).

## bench3 — three-provider benchmark (DeepSeek · OpenAI · xAI)

**Status: pilot near complete — singleshot done (96 runs), agentic on the
last arm; full results, findings, and the webapp explorer are in `bench3/`.**

Key early findings (see [`bench3/FINDINGS.md`](bench3/FINDINGS.md)):
- r1_tiling separates the reasoning stacks: flash 0/3, pro 2/3, grok 3/3,
  gpt-sol 3/3 (fastest at 37-42s).
- Cost per passing task: flash $0.003, pro $0.006, grok $0.015,
  gpt-sol $0.049 — total spend under $2 for 120+ runs.
- Single-shot multi-call tool planning fails on every arm (a ceiling),
  with distinct failure modes per provider.

Extends the benchmark to four arms — **deepseek-v4-flash, deepseek-v4-pro,
gpt-5.6-sol, grok-4.6** — over six task categories (coding, multi-step
agentic workflow, multi-step reasoning, creativity, writing quality, tool
use), measuring ability to solve, solution quality, time, tokens, and cost.

- Design & methodology: [`bench3/README.md`](bench3/README.md)
- Narrative report: [`bench3/NARRATIVE.md`](bench3/NARRATIVE.md)
- Live results: `bench3/results/` (CSVs + raw runs)
- Webapp explorer: `cd bench3 && python3 -m http.server 8931` →
  http://127.0.0.1:8931/webapp/
