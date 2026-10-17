# Task economics benchmark plan

## Status on 2026-10-17

- The historical objective pilot has 210 runs across 15 routes, seven tasks, and two effort levels.
- The current coding pilot has four routes and one sandboxed task. Each route passed three of four hidden tests.
- GPT-6.1 Sol passed all eight reasoning runs.
- The original tool pilot used a one-response tool-plan contract. It did not execute tool calls or return tool results. Keep those results as history, not as current tool-use evidence.
- The corrected tool pilot completed 90 workflows across 15 routes, three tasks, and two effort levels. All 90 passed. GPT passed 18/18 workflows. The grader replayed the executed tool calls.
- The current campaign adds ten new repetitions of all seven objective tasks for each of the 30 route/effort settings. This is 2,100 base tasks. A failed base task gets one full enforced Aegis retry.
- The new OpenRouter slice adds DeepSeek V4 Pro 0813 and the Claude Haiku, Opus, and Fable tiers.
- The real tool-loop gate is closed for these local tasks. The repeated task-cost comparison is the active evidence gate. The coding pilot remains separate.

## User and job

The user chooses a model and vendor route for a task. The user needs four values:

- cost per 100,000 attempts;
- pass rate;
- cost per 100,000 successful tasks;
- latency.

The task is the main unit. A vendor plan is one cost input. The study does not try to rank all models with one aggregate score.

## Earliest Testable — real tool journey

**User promise:** A user can compare a real tool task across the 15 enabled routes.

**Complete journey:** Send the prompt -> receive a tool call -> execute the deterministic tool -> return the result -> let the model continue -> grade the final answer -> add all call costs.

**Baseline:** The current harness asks for a complete dependent call sequence in one response. GPT-6.1 Sol returns valid first calls and waits for tool results. This makes the present tool result unsuitable for a general tool-use claim.

**Metric and threshold:** All 15 routes complete the same three tool workflows at low and high effort. Every workflow has a grade, a token record, and a cost record. The grader must reproduce each result from its tool trace. Returned provider receipts must agree with recorded charges within 1% or $0.001, whichever is larger. Disclose interrupted calls with no receipt.

**Falsifier:** A provider needs a different task contract that the harness cannot normalize without changing the user task.

**Deferrals:** New models, more repetitions, subjective writing tasks, a workload calculator, and cloud hosting.

**Observed evidence and decision:** All 90 corrected workflows passed. GPT passed 18/18, compared with 0/18 under the earlier one-response contract. The audit checked 447 returned provider receipts. Three connection resets required fresh-state restarts. Costs include returned receipts from partial workflows. Charges for three interrupted requests remain unknown. Continue to repeated measurement. This closes the harness gate, not a broad model-quality claim.

**Stop / Pivot / Continue:** Stop new model runs if trace replay or cost checks fail. Change a protocol adapter only if the user task stays the same. Continue when all routes complete the same journey and the report states known cost gaps.

## Earliest Usable — full price ladder

**User promise:** A user can choose a route for representative work without builder help.

**Complete journey:** Select a task type -> inspect cost per 100,000 attempts, pass rate, cost per 100,000 successes, and latency -> apply a minimum pass-rate threshold -> choose a route.

**Baseline:** The pilot has one observation per route, task, and effort. That sample cannot establish a stable pass-rate or cost order. The corrected tool pilot is separate from the historical one-response results.

**Model additions:**

- GLM 5.3, GLM 5.3 Flash, and Muse Spark Open through LunaRoute;
- GPT-6 Luna and GPT-6 Astra through the direct OpenAI API;
- Claude Haiku 5.5, Claude Sonnet 5.5, Claude Opus 5.5, and Claude Fable 5.1 through OpenRouter;
- DeepSeek V4 Pro 0813 through OpenRouter, with default and price-first routing.

Keep Claude and DeepSeek on OpenRouter. Keep GPT on the direct OpenAI API.

**LunaRoute catalog decision:**

- Add `glm-5.3-flash` to the main text benchmark. It is a separate live model variant and can change task throughput.
- Keep the four `-background` entries for a saturation and queue test. They are scheduler variants, not new quality models.
- Defer `glm-5.3-vision` and its background variant until the benchmark has image-input tasks.
- Test `clef-flash` and `djev` only in a separate System One decision benchmark. They do not generate normal chat text.
- Exclude `whisper-large-v3` from this benchmark. It is a transcription model.
- Keep image, embedding, and rerank catalogs in the snapshot, but test them only with matching task types.

**Representative slices:**

- short objective reasoning;
- long objective reasoning;
- real tool loop;
- sandboxed coding repair.

**Metric and threshold:** Complete ten new repetitions for every enabled route, task, and effort setting. The matrix contains 15 routes, seven objective tasks, and two effort levels: 2,100 base tasks. Exclude pilot repetition 1; use repetition IDs 2 through 11. Every completed repetition must pass exact coverage and independent grade replay. Every failed base task must have one enforced retry with a valid evidence journal. A passing retry must also pass the method closure gate. An unresolved infrastructure error prevents completion.

**Measurement contract:** Freeze route settings, task files, method files, and runner source in the campaign manifest. Randomize task order within each repetition. Keep base and retry output limits equal: 4,096 tokens for tiling and each tool request; 8,192 tokens for the other reasoning tasks. Tool workflows allow at most 12 model requests and 32 tool calls. Preserve partial receipts after a connection failure. A transport restart is not a model task retry.

**User evidence:** Publish task cost, pass rate, successful-task cost, and median time after each completed task. Save a verified report-data snapshot after each full repetition. Show low and high effort separately. Use 95% Wilson intervals for pass rates and a 1,000-draw percentile bootstrap for task-cost variation. Do not treat a repeated fixed task as a new task sample. Ten repetitions do not guarantee statistical significance or broad model quality.

**Failure intervention:** When a graded base run fails, run one paired retry
with the full enforced Aegis Method. Keep base and retry scores separate.
Report the recovery count and the total base-plus-retry cost and time. A
provider or credential failure does not trigger this intervention because it
is not a model task failure. The earlier Lite condition remains historical.

The enforced follow-up is a separate condition. It uses the full managed
method payload, local `.am` contracts, Aegis Method plan/completion/closure
gates, the existing objective checker as the falsifier, and one isolated
signed Aegis evidence journal per retry. It keeps the original provider route
and records the result as `aegis_enforced_retry`.

**Falsifier:** Trace replay disagrees with a grade, a method journal is invalid, or a task measures provider protocol instead of user outcome. Wide or overlapping intervals can leave a route choice unresolved. That is an evidence limit, not permission to declare a winner.

**Deferrals:** Automatic production routing, broad subjective evaluation, and a workload calculator.

**Stop / Pivot / Continue:** Stop the campaign for an unresolved infrastructure or integrity failure. Diagnose and resume the same campaign without discarding completed records. Change task scope or budgets only in a new declared experiment. After ten verified repetitions, review whether the evidence supports a real route choice. Do not add paid repetitions without a new user request.

## Earliest Lovable — workload decision tool

**User promise:** A user can enter a workload mix and get the lowest-cost route that meets quality and latency limits.

**Complete journey:** Set task shares and volumes -> set minimum pass rate and maximum latency -> view valid routes -> inspect evidence -> export the chosen routing policy.

**Baseline:** The current workflow uses tables and manual comparison.

**Metric and threshold:** The user prefers the tool to the current workflow for two real routing decisions and returns for a later model or price change.

**Falsifier:** The recommendation does not change a real route, capacity, or purchase decision.

**Deferrals:** Automatic route changes and cloud hosting. Keep the first tool local.

**Stop / Pivot / Continue:** Stop if the tool has no decision value. Pivot the workload model when observed use differs from the benchmark. Continue only after observed repeat use or clear preference.

## Dependency classification

**Verified hard dependencies:**

- The Usable gate depends on a working real tool loop.
- A valid enforced retry needs working method gates and a valid signed evidence journal.

**Route dependencies:**

- OpenRouter access is verified for the active DeepSeek and Claude routes.
- Two Claude Opus Aegis retries were policy refusals. This is a route-policy limit, not a credential failure.

**Resource relationships:**

- More repetitions use more API budget and run time. This affects batch size, not task order.
- GLM 5.3, GLM 5.3 Flash, and Muse Spark Open need model-specific LunaRoute throughput measurements before the report can assign their fixed-plan cost per task.
- LunaRoute background variants need a sustained-load test. Their lower scheduler priority can change queue time and achieved account throughput.

**Evidence relationships:**

- One repetition cannot establish a stable quality or latency rank.
- Real tool-loop evidence must replace the one-shot tool-plan result before a tool-use claim.
- The repeated task measurements inform a later workload tool. They do not make that tool technically impossible to build sooner.
- Repeated prompts estimate variation on these fixed tasks. They do not establish performance on unseen tasks or prove that an Aegis recovery was caused by the method instead of another attempt.

**Preference relationships:**

- More visual detail and more model tiers can wait until the task-level result changes a real decision.
