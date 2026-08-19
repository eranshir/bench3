# GLM 5.2 Vision (LunaRoute) — bench3 results

**Date:** 2026-08-19 · **Harness:** bench3 (same tasks/checkers as all arms) · **Trial:** 1
**Provider:** LunaRoute (https://gw.lunaroute.com/v1, OpenAI-compatible chat) · **Model:** glm-5.2-vision (524k context, reasoning+tools+vision)

## Overall

| Arm | Pass | Wall | Med/task |
|---|---|---|---|
| **GLM 5.2 Vision (LunaRoute)** | **13/16 (81%)** | 3064s | 65s |
| DeepSeek V4 Pro | 40/50 (80%) | 3326s | 17s |
| Grok 4.6 | 39/50 (78%) | 2633s | 24s |
| DeepSeek V4 Flash | 38/50 (76%) | 2491s | 7s |
| MTPLX Qwen 3.8 27B (local) | 12/16 (75%) | 6350s | 116s |
| GPT-5.6 Sol | 35/50 (70%) | 1827s | 11s |

**GLM 5.2 Vision posts the highest pass rate on the board (trial 1).** Caveats: n=16 (one trial), and w2_rewrite's
"pass" is nominal — the model burned its entire 16k-token output budget on reasoning and returned empty content.
Honest count: 12/16 real passes.

## Per-task (trial 1)

| Task | Type | Result | Time | Notes |
|---|---|---|---|---|
| r1_tiling | reasoning | ✅ | 392s | flash 0%, pro 40% fail this |
| r4_catalan | reasoning | ✅ | 74s | pro 33%, flash 66% |
| r2/r3 | reasoning | ✅ | 25/53s | |
| t1_orchestrate | tool-use | ✅ | 19s | gpt/grok/mtplx all fail |
| t2_toolselect | tool-use | ❌ | 7s | universal failure |
| t3_inventory | tool-use | ❌ | 16s | fails like gpt |
| a1_chained | agentic | ✅ | 57s | |
| a2_buildtestfix | agentic | ✅ | 298s | gpt 33% |
| c1_deadlock | coding | ❌ | 598s | **only arm to fail it** (all others 100%) |
| c2_perf | coding | ✅ | 328s | |
| c3_adversarial | coding | ✅ | 18s | |
| k1_product | creativity | ✅ | 286s | judged 4.4/5 |
| k2_story | creativity | ✅ | 372s | judged 4.0/5 |
| w1_explain | writing | ✅ | 57s | judged 4.75/5 |
| w2_rewrite | writing | ⚠️ | 464s | empty content — 16k tokens burned on reasoning |

**Judged quality: 4.38/5 (n=3)** — top tier (DS Pro 4.39, GPT 4.37).

## Where it lands

- **Strengths:** reasoning (4/4, incl. the two tasks DeepSeek fails), agentic workflow (2/2), and
  t1 tool orchestration (which GPT/Grok/MTPLX all fail). Highest overall pass rate on the board.
- **Weakness:** c1_deadlock — the ONLY arm to fail it. Tool-use t2/t3 also fail (shared with GPT).
- **Character:** extremely verbose reasoner. Even with reasoning_effort=none (wire for generation tasks),
  GLM still burned 8-16k tokens on reasoning per creative/writing task (w2 returned empty content), making
  it the slowest singleshot arm (~200-460s per generation task). Its agent-loop speed is cloud-fast (18-598s).
- **Cost:** pricing not published in the LunaRoute UI at benchmark time — recorded as unknown, not free.
- **Note:** GLM's reasoning appears in message.reasoning, not usage.reasoning_tokens, so the harness's
  reasoning-token column undercounts it (shows 0).

## Setup

- LunaRoute endpoint verified (models/chat/completions/responses all live; 524k context; vision+tools+reasoning).
- Wire: harness "high" → reasoning_effort high; harness "off" (generation) → reasoning_effort none.
- Credentials stored in ~/.dsh/.credentials.yaml (LUNAROUTE_API_KEY); never in the repo.
