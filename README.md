# deepseek — DeepSeek V4-Flash vs GPT-5.6-Sol coding benchmark

Original benchmark (2026-08-01): controlled Codex-CLI comparison of
deepseek-v4-flash vs gpt-5.6-sol — see [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md)
and the running narrative in [`REPORT.md`](REPORT.md).

## bench3 — three-provider benchmark (DeepSeek · OpenAI · xAI)

**Status: in progress (pilot running).**

Extends the benchmark to four arms — **deepseek-v4-flash, deepseek-v4-pro,
gpt-5.6-sol, grok-4.6** — over six task categories (coding, multi-step
agentic workflow, multi-step reasoning, creativity, writing quality, tool
use), measuring ability to solve, solution quality, time, tokens, and cost.

- Design & methodology: [`bench3/README.md`](bench3/README.md)
- Narrative report: [`bench3/NARRATIVE.md`](bench3/NARRATIVE.md)
- Live results: `bench3/results/` (CSVs + raw runs)
- Webapp explorer: `cd bench3 && python3 -m http.server 8931` →
  http://127.0.0.1:8931/webapp/
