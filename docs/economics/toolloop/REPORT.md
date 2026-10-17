# Executed tool workflows — 17 October 2026

Completed 90 base workflows across 15 routes. Passed 90. Ran 0 enforced Aegis failure retries; recovered 0.

Each workflow executes local tools, returns each result to the model, and continues to a final answer. The grader replays the tool events and checks final fixture state. All model requests, including failed calls within a workflow and failure retries, contribute to cost.

The old prompts requested a complete tool plan in one response. Two explicitly said no results would be returned. The new prompts request executed actions and require the model to obtain prices and account IDs from tools. These are different task contracts. The old scores do not measure real tool-loop ability.

| Route | Old one-shot | Executed loop | After Aegis | Corrected tool errors | Model calls / workflow | Seconds (median) | Cost / 100K attempts | Cost / 100K successes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek V4.1 Flash — OpenRouter | 4/6 | 6/6 | 6/6 | 0 | 5.0 | 8.9 | $156.24 | $156.24 |
| DeepSeek V4.1 Flash — OpenRouter price-first | 4/6 | 6/6 | 6/6 | 2 | 5.3 | 57.8 | $124.35 | $124.35 |
| DeepSeek V4 Pro 0813 — OpenRouter | 3/6 | 6/6 | 6/6 | 1 | 5.0 | 15.1 | $367.07 | $367.07 |
| DeepSeek V4 Pro 0813 — OpenRouter price-first | 3/6 | 6/6 | 6/6 | 1 | 5.3 | 20.5 | $254.71 | $254.71 |
| DeepSeek V4.1 Flash — LunaRoute | 4/6 | 6/6 | 6/6 | 0 | 4.8 | 5.0 | $3.00 | $3.00 |
| GLM 5.3 — LunaRoute | 0/6 | 6/6 | 6/6 | 0 | 4.8 | 7.6 | $2.05 | $2.05 |
| GLM 5.3 Flash — LunaRoute | 4/6 | 6/6 | 6/6 | 1 | 5.0 | 12.4 | $2.12 | $2.12 |
| Muse Spark Open — LunaRoute | 2/6 | 6/6 | 6/6 | 0 | 5.2 | 12.7 | $4.58 | $4.58 |
| GPT-6 Luna — OpenAI API | 0/6 | 6/6 | 6/6 | 3 | 5.2 | 9.3 | $58.19 | $58.19 |
| GPT-6.1 Sol — OpenAI API | 0/6 | 6/6 | 6/6 | 0 | 5.0 | 12.8 | $963.90 | $963.90 |
| GPT-6 Astra — OpenAI API | 0/6 | 6/6 | 6/6 | 0 | 4.8 | 11.6 | $4,999.17 | $4,999.17 |
| Claude Haiku 5.5 — OpenRouter | 3/6 | 6/6 | 6/6 | 0 | 5.0 | 8.0 | $139.49 | $139.49 |
| Claude Sonnet 5.5 — OpenRouter | 4/6 | 6/6 | 6/6 | 0 | 4.3 | 8.9 | $2,376.46 | $2,376.46 |
| Claude Opus 5.5 — OpenRouter | 4/6 | 6/6 | 6/6 | 1 | 4.7 | 17.4 | $5,240.75 | $5,240.75 |
| Claude Fable 5.1 — OpenRouter | 4/6 | 6/6 | 6/6 | 2 | 5.0 | 21.1 | $14,179.38 | $14,179.38 |

Costs in the table include failure-only Aegis retries. LunaRoute uses the supplied full-capacity allocation. Token-billed routes use the sum of each request's cost, including OpenRouter credit fees.

## Run contract

- Three tasks: invoice creation, account unlock and notification, and inventory order creation.
- One low-effort and one high-effort attempt per route and task.
- Maximum 12 model requests, 32 tool calls, and 4,096 output tokens per request.
- Independent calls may share a model response. The runtime executes calls in listed order and returns a result for each call.
- Tool errors return to the model. A model may correct an argument error within its budget. Prohibited support-tool attempts fail acceptance.
- OpenAI Responses uses previous_response_id and function_call_output. Chat routes retain assistant reasoning fields and tool_call_id.
- Aegis failure retries use fresh fixture state, the full method payload, frozen local contracts, the official method gates, and a signed journal.
- There is no real email, purchase, invoice, or account mutation outside the local fixture.
- These three small deterministic tasks establish harness behavior. They do not establish a broad model ranking.

Provider connections required 3 fresh-state restarts. Returned receipts from partial workflows are included in cost and token totals. The 3 interrupted requests had no usage receipt, so their charges are unknown. Latency includes completed model requests and known partial-request time; the lost-connection wait is not fully measured.
