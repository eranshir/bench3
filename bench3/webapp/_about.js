// ---------- about / introduction ----------
function renderAbout() {
  var arms = DATA.arms || {};
  var runs = DATA.runs || [];
  var n = runs.length;
  var cost = sum(runs.map(function(r) { return r.cost_usd; }));
  var h = '';
  h += "<div class='panel full' style='margin-bottom:16px;padding:28px'>";
  h += '<h1 style="font-size:28px;margin-bottom:6px">Which coding agent is right for you?</h1>';
  h += '<p style="color:#7d8aa3;font-size:15px;max-width:820px">A controlled, head-to-head comparison of four coding agents from three providers — DeepSeek, OpenAI and xAI — measured on solving ability, solution quality, speed, token use and cost, through the <em>same</em> harness and tools. Everything below is generated from real runs; nothing is estimated.</p>';
  h += '</div>';

  h += "<div class='panel full' style='margin-bottom:14px'><h3>What is this?</h3>";
  h += '<p style="color:#b6c1d6;max-width:900px">This site reports a benchmark: 4 models were asked to do 14 small, deliberately hard tasks (bugs, rewrites, reasoning problems, creative and technical writing, tool-orchestration). Each task was attempted by every model under identical conditions — the same prompt, the same tools, the same grading — so the only difference between columns is the model itself. The results are shown as pass rates, quality scores, time, tokens and cost, and every individual run is open for inspection.</p>';
  h += '</div>';

  // contenders
  h += "<div class='panel full' style='margin-bottom:14px'><h3>The contenders</h3>";
  h += '<table><thead><tr><th>Model</th><th>Provider</th><th>Input $/M</th><th>Cached $/M</th><th>Output $/M</th></tr></thead><tbody>';
  var order = ['deepseek-flash', 'deepseek-pro', 'gpt-sol', 'grok'];
  order.forEach(function(a) {
    var x = arms[a];
    if (!x) return;
    h += '<tr><td><strong>' + esc(x.display) + '</strong></td><td>' + esc(x.vendor) + '</td>';
    h += '<td>' + x.prices.input + '</td><td>' + x.prices.cached_input + '</td><td>' + x.prices.output + '</td></tr>';
  });
  h += '</tbody></table>';
  h += '<p style="color:#7d8aa3;font-size:12px;margin-top:8px">List prices per 1M tokens. Costs in this benchmark are computed from each run’s actual token usage at these prices.</p>';
  h += '</div>';

  // how it works
  h += "<div class='panel full' style='margin-bottom:14px'><h3>How the test works</h3>";
  h += '<ul style="color:#b6c1d6;max-width:900px;padding-left:20px;line-height:1.8">';
  h += '<li><strong>One harness, both modes.</strong> Multi-step coding and workflow tasks run as real agents (the DeepSeek Harness headless runner — same tool surface, sandbox and system prompt for every model). Reasoning, writing, creativity and tool-planning tasks run single-shot through one API client — again identical for every model. Only the model id and the wire spelling of the pinned reasoning effort differ.</li>';
  h += '<li><strong>Blind, objective grading where possible.</strong> Coding/workflow tasks are graded by hidden tests the model never saw (every grader was validated to fail on the buggy fixture and pass on a reference fix). Reasoning answers are checked exactly. Writing and creativity are scored against rubrics by a judge model — blindly, with the outputs anonymized and shuffled — and a second judge cross-checks a sample because judges have taste.</li>';
  h += '<li><strong>Effort is pinned.</strong> All models run at the same reasoning effort per task type (high for objective work; generation mode for writing/creativity — see the caveats).</li>';
  h += '</ul>';
  h += '</div>';

  // what is measured
  h += "<div class='panel full' style='margin-bottom:14px'><h3>What is measured, per run</h3>";
  h += "<div class='kv' style='grid-template-columns:repeat(auto-fit,minmax(150px,1fr))'>";
  h += '<div><div class="k">Pass / fail</div><div class="v">objective solve</div></div>';
  h += '<div><div class="k">Quality</div><div class="v">rubric 1–5</div></div>';
  h += '<div><div class="k">Wall-clock</div><div class="v">seconds</div></div>';
  h += '<div><div class="k">Tokens</div><div class="v">in · cached · out · reasoning</div></div>';
  h += '<div><div class="k">Cost</div><div class="v">from usage × list price</div></div>';
  h += '</div></div>';

  // how to read
  h += "<div class='panel full' style='margin-bottom:14px'><h3>How to read the results</h3>";
  h += '<ul style="color:#b6c1d6;max-width:900px;padding-left:20px;line-height:1.8">';
  h += '<li><strong>Pass rate</strong> is the fraction of trials a model solved. Saturated tasks (everyone passes) are still useful — they show all models handle hard-but-specified work; the differences then show up in time and cost.</li>';
  h += '<li><strong>The Ladder tab</strong> orders tasks hardest-first and shows <em>discrimination</em> — how much the models separated on that task. A discrimination of 1.0 means some model got it right and another got it wrong every time; 0 means no separation. The interesting tasks are the discriminating ones.</li>';
  h += '<li><strong>Cost per passing task</strong> is the honest economic number: total cost divided by solves. A model that is 40x cheaper per token but fails often can be more expensive in practice.</li>';
  h += '<li><strong>Quality scores</strong> come from a judge model; where a second judge scored the same output you will see both (e.g. <span style="color:#7d8aa3">4/5 (xcheck 3)</span>). Disagreement between judges is real and shown, not hidden.</li>';
  h += '<li>Click any task row to open every run: the prompt, what the model produced, its tool calls, its file diffs, its agent trajectory, the grader output, and the exact tokens and cost.</li>';
  h += '</ul>';
  h += '</div>';

  // key findings
  h += "<div class='panel full' style='margin-bottom:14px'><h3>What the data says so far</h3>";
  h += '<ul style="color:#b6c1d6;max-width:900px;padding-left:20px;line-height:1.8">';
  h += '<li>On everything hard-but-<em>specified</em> — concurrency bugs, performance rewrites, chained failure hunts, test-driven implementation — all four models solve essentially everything. The separation lives in two places: a hard counting-reasoning problem, and single-shot multi-call tool planning.</li>';
  h += '<li><strong>Reasoning ladder:</strong> deepseek-v4-flash 0/3 on the domino-tiling count (it spends its whole output budget thinking and never answers), deepseek-v4-pro 2/3, grok 3/3, gpt-5.6-sol 3/3 — and gpt is 3–5x faster at it than the other solvers.</li>';
  h += '<li><strong>Tool planning surprise:</strong> asked to emit a complete multi-call tool sequence in one shot, both DeepSeek models do it (pro 3/3, flash 2/3) while gpt stops after the first wave and grok writes the plan as prose instead of calling the tools. One task, one format — treat as a hypothesis.</li>';
  h += '<li><strong>Cost:</strong> per passing task, deepseek-v4-flash is roughly 38x cheaper than gpt-5.6-sol at list prices (and grok sits between). The entire benchmark cost under $4 to run.</li>';
  h += '<li><strong>Quality:</strong> both judges agree grok trails on creative and technical writing; whether gpt leads depends on who judges — each judge tends to prefer its own vendor’s prose.</li>';
  h += '</ul>';
  h += '</div>';

  // caveats
  h += "<div class='panel full' style='margin-bottom:14px'><h3>Honest caveats</h3>";
  h += '<ul style="color:#7d8aa3;max-width:900px;padding-left:20px;line-height:1.8;font-size:13px">';
  h += '<li>Small sample: 3 trials per single-shot task, 2–3 per agentic task. A one-run gap is not a settled ranking.</li>';
  h += '<li>Judges have taste and bias: blind judging removes the label, not the style preference. Scores carry roughly ±1 point of judge noise.</li>';
  h += '<li>The tool-planning tasks are single-shot by design (no tool execution), which is why every model fails the hardest one — multi-turn tool use is covered by the agentic tasks instead.</li>';
  h += '<li>deepseek-v4-flash’s reasoning failure is partly an effort artifact: at high effort it burns its whole output budget thinking. That is a real, reproducible behavior — and a configuration choice — not pure capability.</li>';
  h += '<li>Costs use current list prices; DeepSeek announced a price increase after this run. Timing is machine-relative.</li>';
  h += '<li>The task suites were authored by the same agent that analyses the results.</li>';
  h += '</ul>';
  h += '</div>';

  // navigate
  h += "<div class='panel full'><h3>Where to go from here</h3>";
  h += '<p style="color:#b6c1d6;max-width:900px">Start with <strong>Overview</strong> for the aggregate picture, then <strong>Ladder</strong> to see which tasks separate the models, then click any task to open the raw runs. <strong>Categories</strong> and <strong>Tasks</strong> give the per-category and per-trial detail. Every number in this site is backed by a file in <code>bench3/results/</code>.</p>';
  h += '</div>';

  $('#view').innerHTML = h;
}
