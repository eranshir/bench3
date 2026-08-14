"use strict";

// ---------- state ----------
let DATA = null;
const ARMS = ['deepseek-flash', 'deepseek-pro', 'gpt-sol', 'grok'];
const ARM_COLORS = {
  'deepseek-flash': '#4f8cff',
  'deepseek-pro': '#3ecf8e',
  'gpt-sol': '#a06bff',
  'grok': '#f5b942',
};
const CATEGORIES = ['coding', 'agentic-workflow', 'tool-use', 'reasoning', 'creativity', 'writing'];
const CAT_LABELS = {
  coding: 'Coding',
  'agentic-workflow': 'Agentic workflow',
  'tool-use': 'Tool use',
  reasoning: 'Reasoning',
  creativity: 'Creativity',
  writing: 'Writing quality',
};

// ---------- helpers ----------
const $ = function(sel) { return document.querySelector(sel); };

function runsFor(arm, task) {
  return DATA.runs.filter(function(r) { return r.arm === arm && r.task === task; });
}

function passRate(runs) {
  if (!runs.length) return null;
  return runs.reduce(function(s, r) { return s + r.passed; }, 0) / runs.length;
}

function median(arr) {
  if (!arr.length) return 0;
  var s = arr.slice().sort(function(a, b) { return a - b; });
  var m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function sum(arr) { return arr.reduce(function(a, b) { return a + b; }, 0); }

function fmtMoney(x) {
  if (x === 0) return '$0';
  if (x < 0.01) return '$' + x.toFixed(4);
  if (x < 1) return '$' + x.toFixed(3);
  return '$' + x.toFixed(2);
}

function fmtToks(n) { return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n); }

function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function passClass(rate) {
  if (rate === null) return '';
  if (rate >= 1) return 'pass';
  if (rate > 0) return 'partial';
  return 'fail';
}

function chart(el, option) {
  if (typeof echarts === 'undefined') {
    el.innerHTML = '<div style="color:#7d8aa3;padding:40px;text-align:center">Chart library blocked — check network access to cdn.jsdelivr.net</div>';
    return null;
  }
  var c = echarts.init(el);
  c.setOption(option);
  return c;
}

// ---------- overview ----------
function renderOverview() {
  var runs = DATA.runs;
  var totalCost = sum(runs.map(function(r) { return r.cost_usd; }));
  var passed = runs.filter(function(r) { return r.passed; }).length;
  var totalSecs = sum(runs.map(function(r) { return r.seconds; }));
  var totalToks = sum(runs.map(function(r) { return r.input_tokens + r.output_tokens; }));

  // key findings: discriminating tasks from the ladder
  var findings = '';
  var ladder = DATA.ladder || {};
  var disc = Object.keys(ladder).filter(function(t) { return ladder[t].discrimination >= 0.5; }).sort(function(a, b) { return ladder[b].discrimination - ladder[a].discrimination; });
  if (disc.length) {
    findings += "<div class='panel full' style='margin-bottom:14px'><h3>Key findings — where the arms separate</h3>";
    disc.forEach(function(t) {
      var L = ladder[t];
      var per = ARMS.map(function(a) {
        if (L.per_arm[a] === undefined) return null;
        return '<span style="color:' + ARM_COLORS[a] + ';font-weight:600">' + (DATA.arms[a] ? DATA.arms[a].display : a) + ' ' + Math.round(100 * L.per_arm[a]) + '%</span>';
      }).filter(Boolean).join(' · ');
      findings += '<div style="margin:6px 0"><strong>' + esc(t) + '</strong> <span style="color:#7d8aa3;font-size:12px">(difficulty ' + L.difficulty + ', discrimination ' + L.discrimination + ')</span><br/>' + per + '</div>';
    });
    findings += '</div>';
  }

  var cards = '';
  cards += "<div class='cards'>";
  cards += "<div class='card'><div class='label'>Runs</div><div class='value'>" + runs.length + "</div></div>";
  cards += "<div class='card'><div class='label'>Pass rate</div><div class='value'>" + (runs.length ? Math.round(100 * passed / runs.length) : 0) + "%</div><div class='sub'>" + passed + "/" + runs.length + " runs</div></div>";
  cards += "<div class='card'><div class='label'>Total spend</div><div class='value'>" + fmtMoney(totalCost) + "</div><div class='sub'>from list prices</div></div>";
  cards += "<div class='card'><div class='label'>Wall clock</div><div class='value'>" + Math.round(totalSecs / 60) + "m</div></div>";
  cards += "<div class='card'><div class='label'>Tokens</div><div class='value'>" + fmtToks(totalToks) + "</div><div class='sub'>in + out</div></div>";
  cards += '</div>';

  var html2 = "<div class='grid'>";
  html2 += "<div class='panel full'><h3>Pass rate by category</h3><div id='radar' class='chart'></div></div>";
  html2 += "<div class='panel full'><h3>Cost per run vs pass rate (per task)</h3><div id='scatter' class='chart'></div></div>";
  html2 += "<div class='panel full'><h3>Cost per passing task</h3><div id='cpp' class='chart'></div></div>";
  html2 += "<div class='panel full'><h3>Rubric quality (creativity + writing, mean per judge)</h3><div id='qual' class='chart'></div></div>";
  html2 += '</div>';

  $('#view').innerHTML = findings + cards + html2;

  var radarCats = CATEGORIES.filter(function(c) { return runs.some(function(r) { return r.category === c; }); });
  var radarData = ARMS.filter(function(a) { return runs.some(function(r) { return r.arm === a; }); }).map(function(a) {
    return {
      name: DATA.arms[a] ? DATA.arms[a].display : a,
      value: radarCats.map(function(c) {
        var g = runs.filter(function(r) { return r.arm === a && r.category === c; });
        return g.length ? +(100 * passRate(g)).toFixed(1) : null;
      }),
      lineStyle: { color: ARM_COLORS[a] },
      itemStyle: { color: ARM_COLORS[a] },
      areaStyle: { opacity: 0.12 },
    };
  });

  chart($('#radar'), {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#7d8aa3' } },
    radar: {
      indicator: radarCats.map(function(c) { return { name: CAT_LABELS[c] || c, max: 100 }; }),
      radius: '65%',
      axisName: { color: '#7d8aa3' },
      splitArea: { areaStyle: { color: ['rgba(24,32,48,0.3)', 'rgba(24,32,48,0.6)'] } },
      splitLine: { lineStyle: { color: '#232c3f' } },
    },
    series: [{ type: 'radar', data: radarData }],
  });

  var scatterData = ARMS.map(function(a) {
    return {
      name: DATA.arms[a] ? DATA.arms[a].display : a,
      type: 'scatter',
      symbolSize: 12,
      data: Object.keys(DATA.tasks).map(function(t) {
        var g = runsFor(a, t);
        if (!g.length) return null;
        var cost = sum(g.map(function(r) { return r.cost_usd; })) / g.length;
        return [cost, passRate(g) * 100];
      }).filter(Boolean),
    };
  });

  chart($('#scatter'), {
    tooltip: { trigger: 'item', formatter: function(p) { return p.seriesName + '<br/>cost ' + fmtMoney(p.value[0]) + ' · pass ' + p.value[1].toFixed(0) + '%'; } },
    legend: { bottom: 0, textStyle: { color: '#7d8aa3' } },
    xAxis: { type: 'log', name: 'cost / run', nameTextStyle: { color: '#7d8aa3' }, axisLabel: { color: '#7d8aa3', formatter: function(v) { return fmtMoney(v); } }, splitLine: { lineStyle: { color: '#1a2233' } } },
    yAxis: { type: 'value', name: 'pass rate %', max: 105, nameTextStyle: { color: '#7d8aa3' }, axisLabel: { color: '#7d8aa3' }, splitLine: { lineStyle: { color: '#1a2233' } } },
    series: scatterData,
  });

  // cost per passing task
  var cppData = ARMS.filter(function(a) {
    var g = runsForAll(a);
    return g.some(function(r) { return r.passed; });
  }).map(function(a) {
    var g = runsForAll(a);
    var npass = g.filter(function(r) { return r.passed; }).length;
    var cost = sum(g.map(function(r) { return r.cost_usd; }));
    return { name: DATA.arms[a] ? DATA.arms[a].display : a, value: +(cost / npass).toFixed(4) };
  });
  chart($('#cpp'), {
    tooltip: { trigger: 'item', formatter: function(p) { return p.name + '<br/>' + fmtMoney(p.value) + ' per passing task'; } },
    grid: { left: 90, right: 30, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: cppData.map(function(d) { return d.name; }), axisLabel: { color: '#7d8aa3', interval: 0, rotate: 20 } },
    yAxis: { type: 'value', name: 'USD / passing task', nameTextStyle: { color: '#7d8aa3' }, axisLabel: { color: '#7d8aa3', formatter: function(v) { return fmtMoney(v); } }, splitLine: { lineStyle: { color: '#1a2233' } } },
    series: [{ type: 'bar', data: cppData.map(function(d) { return { value: d.value, itemStyle: { color: ARM_COLORS[d.name] } }; }), barMaxWidth: 60 }],
  });

  renderQuality();
}

function runsForAll(a) {
  return DATA.runs.filter(function(r) { return r.arm === a; });
}

function renderQuality() {
  var judged = DATA.runs.filter(function(r) { return r.judged; });
  if (!judged.length) return;
  var series = [];
  var byJudge = {};
  judged.forEach(function(r) {
    var j = r.judged;
    byJudge[j.judge] = byJudge[j.judge] || {};
    byJudge[j.judge][r.arm] = byJudge[j.judge][r.arm] || [];
    byJudge[j.judge][r.arm].push(j.mean);
  });
  var names = Object.keys(byJudge);
  names.forEach(function(jn) {
    var data = ARMS.filter(function(a) { return byJudge[jn][a]; }).map(function(a) {
      var vals = byJudge[jn][a];
      return { name: DATA.arms[a] ? DATA.arms[a].display : a, value: +(sum(vals) / vals.length).toFixed(2) };
    });
    series.push({ name: jn.indexOf('deepseek') >= 0 ? 'deepseek-v4-pro judge' : 'gpt-5.6-sol judge', type: 'bar', data: data, barMaxWidth: 40 });
  });
  if (!series.length) return;
  chart($('#qual'), {
    tooltip: { trigger: 'item', formatter: function(p) { return p.seriesName + '<br/>' + p.name + ': ' + p.value + '/5'; } },
    legend: { bottom: 0, textStyle: { color: '#7d8aa3' } },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: series[0].data.map(function(d) { return d.name; }), axisLabel: { color: '#7d8aa3', interval: 0, rotate: 20 } },
    yAxis: { type: 'value', name: 'mean rubric / 5', max: 5, nameTextStyle: { color: '#7d8aa3' }, axisLabel: { color: '#7d8aa3' }, splitLine: { lineStyle: { color: '#1a2233' } } },
    series: series,
  });
}

// ---------- categories ----------
function renderCategories() {
  var cats = CATEGORIES.filter(function(c) { return DATA.runs.some(function(r) { return r.category === c; }); });
  var out = '';
  cats.forEach(function(c) {
    var tasks = [];
    DATA.runs.forEach(function(r) { if (r.category === c && tasks.indexOf(r.task) < 0) tasks.push(r.task); });
    out += "<div class='panel full' style='margin-bottom:14px'>";
    out += '<h3>' + (CAT_LABELS[c] || c) + ' <span style="color:#7d8aa3;font-weight:400;font-size:12px">— ' + tasks.length + ' task(s)</span></h3>';
    out += '<table><thead><tr><th>task</th>';
    ARMS.forEach(function(a) { out += '<th>' + (DATA.arms[a] ? DATA.arms[a].display : a) + '</th>'; });
    out += '</tr></thead><tbody>';
    tasks.forEach(function(t) {
      out += '<tr onclick="openTask(\'' + t + '\')"><td><strong>' + esc(t) + '</strong></td>';
      ARMS.forEach(function(a) {
        var g = runsFor(a, t);
        if (!g.length) { out += '<td>—</td>'; return; }
        var rate = passRate(g);
        var medS = median(g.map(function(r) { return r.seconds; }));
        var cost = sum(g.map(function(r) { return r.cost_usd; }));
        var toks = sum(g.map(function(r) { return r.output_tokens; }));
        out += '<td><span class="' + passClass(rate) + '">' + Math.round(100 * rate) + '%</span> ';
        out += '<span style="color:#7d8aa3">· ' + medS + 's · ' + fmtToks(toks) + ' tok · ' + fmtMoney(cost) + '</span></td>';
      });
      out += '</tr>';
    });
    out += '</tbody></table></div>';
  });
  $('#view').innerHTML = out;
}

// ---------- tasks matrix ----------
function renderTasks() {
  var cats = CATEGORIES.filter(function(c) { return DATA.runs.some(function(r) { return r.category === c; }); });
  var out = '';
  cats.forEach(function(c) {
    var tasks = [];
    DATA.runs.forEach(function(r) { if (r.category === c && tasks.indexOf(r.task) < 0) tasks.push(r.task); });
    out += "<div class='panel full' style='margin-bottom:14px'><h3>" + (CAT_LABELS[c] || c) + '</h3>';
    out += '<table><thead><tr><th>task</th>';
    ARMS.forEach(function(a) { out += '<th>' + (DATA.arms[a] ? DATA.arms[a].display : a) + ' (trials)</th>'; });
    out += '</tr></thead><tbody>';
    tasks.forEach(function(t) {
      out += '<tr onclick="openTask(\'' + t + '\')"><td><strong>' + esc(t) + '</strong>';
      var meta = DATA.tasks[t] || {};
      var badges = '';
      if (meta.has_hidden_test) badges += "<span class='pill agentic'>hidden test</span> ";
      if (meta.has_check) badges += "<span class='pill singleshot'>check.py</span> ";
      if (meta.rubric) badges += "<span class='pill' style='background:rgba(245,185,66,.12);color:#f5b942'>rubric</span> ";
      out += '<br/><span style="color:#7d8aa3;font-size:11px">' + badges + '</span></td>';
      ARMS.forEach(function(a) {
        var g = runsFor(a, t);
        if (!g.length) { out += '<td>—</td>'; return; }
        out += '<td>';
        g.forEach(function(r) {
          out += r.passed ? "<span class='pass'>✓</span> " : "<span class='fail'>✗</span> ";
        });
        out += '</td>';
      });
      out += '</tr>';
    });
    out += '</tbody></table></div>';
  });
  $('#view').innerHTML = out;
}

// ---------- difficulty ladder ----------
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
  h += '<p style="color:#b6c1d6;max-width:900px">This site reports a benchmark: 4 models were asked to do a set of small, deliberately hard tasks (bugs, rewrites, reasoning problems, creative and technical writing, tool-orchestration). Each task was attempted by every model under identical conditions — the same prompt, the same tools, the same grading — so the only difference between columns is the model itself. The results are shown as pass rates, quality scores, time, tokens and cost, and every individual run is open for inspection.</p>';
  h += '</div>';

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
  h += '<p style="color:#7d8aa3;font-size:12px;margin-top:8px">List prices per 1M tokens. Costs in this benchmark are computed from each run\u2019s actual token usage at these prices.</p>';
  h += '</div>';

  h += "<div class='panel full' style='margin-bottom:14px'><h3>How the test works</h3>";
  h += '<ul style="color:#b6c1d6;max-width:900px;padding-left:20px;line-height:1.8">';
  h += '<li><strong>One harness, both modes.</strong> Multi-step coding and workflow tasks run as real agents (the DeepSeek Harness headless runner — same tool surface, sandbox and system prompt for every model). Reasoning, writing, creativity and tool-planning tasks run single-shot through one API client — again identical for every model. Only the model id and the wire spelling of the pinned reasoning effort differ.</li>';
  h += '<li><strong>Blind, objective grading where possible.</strong> Coding/workflow tasks are graded by hidden tests the model never saw (every grader was validated to fail on the buggy fixture and pass on a reference fix). Reasoning answers are checked exactly. Writing and creativity are scored against rubrics by a judge model — blindly, with the outputs anonymized and shuffled — and a second judge cross-checks a sample because judges have taste.</li>';
  h += '<li><strong>Effort is pinned.</strong> All models run at the same reasoning effort per task type (high for objective work; generation mode for writing and creativity — see the caveats).</li>';
  h += '</ul>';
  h += '</div>';

  h += "<div class='panel full' style='margin-bottom:14px'><h3>What is measured, per run</h3>";
  h += "<div class='kv' style='grid-template-columns:repeat(auto-fit,minmax(150px,1fr))'>";
  h += '<div><div class="k">Pass / fail</div><div class="v">objective solve</div></div>';
  h += '<div><div class="k">Quality</div><div class="v">rubric 1-5</div></div>';
  h += '<div><div class="k">Wall-clock</div><div class="v">seconds</div></div>';
  h += '<div><div class="k">Tokens</div><div class="v">in - cached - out - reasoning</div></div>';
  h += '<div><div class="k">Cost</div><div class="v">from usage x list price</div></div>';
  h += '</div></div>';

  h += "<div class='panel full' style='margin-bottom:14px'><h3>How to read the results</h3>";
  h += '<ul style="color:#b6c1d6;max-width:900px;padding-left:20px;line-height:1.8">';
  h += '<li><strong>Pass rate</strong> is the fraction of trials a model solved. Saturated tasks (everyone passes) are still useful — they show all models handle hard-but-specified work; the differences then show up in time and cost.</li>';
  h += '<li><strong>The Ladder tab</strong> orders tasks hardest-first and shows <em>discrimination</em> — how much the models separated on that task. A discrimination of 1.0 means some model got it right and another got it wrong every time; 0 means no separation. The interesting tasks are the discriminating ones.</li>';
  h += '<li><strong>Cost per passing task</strong> is the honest economic number: total cost divided by solves. A model that is 40x cheaper per token but fails often can be more expensive in practice.</li>';
  h += '<li><strong>Quality scores</strong> come from a judge model; where a second judge scored the same output you will see both (e.g. <span style="color:#7d8aa3">4/5 (xcheck 3)</span>). Disagreement between judges is real and shown, not hidden.</li>';
  h += '<li>Click any task row to open every run: the prompt, what the model produced, its tool calls, its file diffs, its agent trajectory, the grader output, and the exact tokens and cost.</li>';
  h += '</ul>';
  h += '</div>';

  h += "<div class='panel full' style='margin-bottom:14px'><h3>What the data says so far</h3>";
  h += '<ul style="color:#b6c1d6;max-width:900px;padding-left:20px;line-height:1.8">';
  h += '<li>On everything hard-but-<em>specified</em> — concurrency bugs, performance rewrites, chained failure hunts, test-driven implementation — all four models solve essentially everything. The separation lives in two places: a hard counting-reasoning problem, and single-shot multi-call tool planning.</li>';
  h += '<li><strong>Reasoning:</strong> on the hardest counting problem (domino tilings), deepseek-v4-flash fails 5/5 (it spends its whole output budget thinking and never answers) and deepseek-v4-pro fails 3/5, while grok and gpt-5.6-sol solve all 5 — gpt 3-5x faster. A second hard problem shows the same shape (pro 1/3, flash 2/3, gpt/grok 3/3). Easy reasoning (coupon collector) is solved by everyone.</li>';
  h += '<li><strong>Tool planning — the big surprise, now robust:</strong> asked to emit a complete multi-call tool sequence in one shot, DeepSeek models do it nearly every time across three different task domains (pro 13/13, flash 10/11), while gpt-5.6-sol fails every single attempt (0/13 — it stops after the first tool wave) and grok is inconsistent (2/13, sometimes writing the plan as prose instead of calling the tools). This is a real, repeated behavioral difference in this format.</li>';
  h += '<li><strong>Cost:</strong> per passing task, deepseek-v4-flash is roughly 38x cheaper than gpt-5.6-sol at list prices (and grok sits between). The entire benchmark so far cost ' + fmtMoney(cost) + ' across ' + n + ' runs.</li>';
  h += '<li><strong>Quality:</strong> both judges agree grok trails on creative and technical writing; whether gpt leads depends on who judges — each judge tends to prefer its own vendor prose.</li>';
  h += '</ul>';
  h += '</div>';

  h += "<div class='panel full' style='margin-bottom:14px'><h3>Honest caveats</h3>";
  h += '<ul style="color:#7d8aa3;max-width:900px;padding-left:20px;line-height:1.8;font-size:13px">';
  h += '<li>Sample sizes: 3-5 trials per single-shot task (the discriminating ones got 5), 2-3 per agentic task. A one-run gap is not a settled ranking.</li>';
  h += '<li>Judges have taste and bias: blind judging removes the label, not the style preference. Scores carry roughly +/-1 point of judge noise.</li>';
  h += '<li>The tool-planning tasks are single-shot by design (no tool execution); the decoy-heavy one fails every model, while the two dependency-chain ones separate the models sharply. Multi-turn tool use is covered by the agentic tasks instead.</li>';
  h += '<li>deepseek-v4-flash reasoning failures are partly an effort artifact: at high effort it spends its whole output budget thinking. That is a real, reproducible behavior — and a configuration choice — not pure capability.</li>';
  h += '<li>Costs use current list prices; DeepSeek announced a price increase after this run. Timing is machine-relative.</li>';
  h += '<li>The task suites were authored by the same agent that analyses the results.</li>';
  h += '</ul>';
  h += '</div>';

  h += "<div class='panel full'><h3>Where to go from here</h3>";
  h += '<p style="color:#b6c1d6;max-width:900px">Start with <strong>Overview</strong> for the aggregate picture, then <strong>Ladder</strong> to see which tasks separate the models, then click any task to open the raw runs. <strong>Categories</strong> and <strong>Tasks</strong> give the per-category and per-trial detail. Every number in this site is backed by a file in <code>bench3/results/</code>.</p>';
  h += '</div>';

  $('#view').innerHTML = h;
}
function renderLadder() {
  var ladder = DATA.ladder || {};
  var keys = Object.keys(ladder);
  if (!keys.length) { $('#view').innerHTML = "<div class='panel'><h3>No ladder data yet</h3></div>"; return; }
  keys.sort(function(a, b) { return ladder[b].difficulty - ladder[a].difficulty || ladder[b].discrimination - ladder[a].discrimination; });
  var h = "<div class='panel full'><h3>Difficulty ladder — hardest first</h3>";
  h += "<div class='legend'>";
  ARMS.forEach(function(a) { if (DATA.arms[a]) h += "<span><span class='dot' style='background:" + ARM_COLORS[a] + "'></span>" + DATA.arms[a].display + '</span>'; });
  h += '</div>';
  h += '<table><thead><tr><th>task</th><th>difficulty</th><th>discrimination</th>';
  ARMS.forEach(function(a) { h += '<th>' + (DATA.arms[a] ? DATA.arms[a].display : a) + '</th>'; });
  h += '</tr></thead><tbody>';
  keys.forEach(function(t) {
    var L = ladder[t];
    h += '<tr onclick="openTask(\'' + t + '\')"><td><strong>' + esc(t) + '</strong></td>';
    h += '<td>' + L.difficulty + '</td><td>' + L.discrimination + '</td>';
    ARMS.forEach(function(a) {
      if (L.per_arm[a] === undefined) { h += '<td>—</td>'; return; }
      var rate = L.per_arm[a];
      h += '<td><span class="' + passClass(rate) + '">' + Math.round(100 * rate) + '%</span></td>';
    });
    h += '</tr>';
  });
  h += '</tbody></table></div>';
  $('#view').innerHTML = h;
}

// ---------- run detail ----------
function openTask(task) {
  var runs = DATA.runs.filter(function(r) { return r.task === task; });
  if (!runs.length) return;
  var meta = DATA.tasks[task] || {};
  var h = '';
  h += "<button class='close' onclick='closeModal()'>✕</button>";
  h += '<h2>' + esc(task) + '</h2>';
  h += '<div class="sub">' + (CAT_LABELS[meta.category] || meta.category) + '</div>';
  if (meta.prompt) h += '<h3 style="margin:14px 0 6px">Prompt</h3><pre>' + esc(meta.prompt) + '</pre>';
  if (meta.rubric) h += '<h3 style="margin:14px 0 6px">Rubric</h3><pre>' + esc(JSON.stringify(meta.rubric, null, 1)) + '</pre>';
  runs.sort(function(a, b) { return a.arm.localeCompare(b.arm) || a.trial - b.trial; });
  runs.forEach(function(r) {
    var d = r.detail || {};
    var tc = (d.tool_calls || []).map(function(t) {
      return "<div style='margin:2px 0'><span class='pill agentic'>" + esc(t.name) + '</span> <code>' + esc(t.args) + '</code></div>';
    }).join('');
    h += "<div class='panel' style='margin-top:16px'>";
    h += '<h3>' + (DATA.arms[r.arm] ? DATA.arms[r.arm].display : r.arm) + ' · trial ' + r.trial + ' ';
    h += r.passed ? "<span class='pass' style='float:right'>PASS</span>" : "<span class='fail' style='float:right'>FAIL</span>";
    h += '</h3>';
    h += "<div class='kv'>";
    h += '<div><div class="k">seconds</div><div class="v">' + r.seconds + 's</div></div>';
    h += '<div><div class="k">input</div><div class="v">' + fmtToks(r.input_tokens) + '</div></div>';
    h += '<div><div class="k">cached</div><div class="v">' + fmtToks(r.cache_read_tokens) + '</div></div>';
    h += '<div><div class="k">output</div><div class="v">' + fmtToks(r.output_tokens) + '</div></div>';
    h += '<div><div class="k">reasoning</div><div class="v">' + fmtToks(r.reasoning_tokens) + '</div></div>';
    h += '<div><div class="k">cost</div><div class="v">' + fmtMoney(r.cost_usd) + '</div></div>';
    h += '<div><div class="k">mode</div><div class="v">' + r.mode + '</div></div>';
    if (r.notes) h += '<div><div class="k">notes</div><div class="v">' + esc(r.notes) + '</div></div>';
    if (r.judged) h += '<div><div class="k">rubric mean</div><div class="v">' + r.judged.mean + '/5</div></div>';
    h += '</div>';
    if (r.judged && r.judged.scores) {
      var s = r.judged.scores;
      h += '<h4 style="margin:8px 0 4px">Rubric scores (' + esc(r.judged.judge) + (r.judged.crosscheck ? ' · cross-check ' + esc(r.judged.crosscheck.judge) : '') + ')</h4>';
      h += '<div class="kv">';
      Object.keys(s).forEach(function(k) {
        var v = s[k] + '/5';
        if (r.judged.crosscheck && r.judged.crosscheck.scores[k] !== undefined) {
          var c = r.judged.crosscheck.scores[k];
          v += ' <span style="color:' + (c >= s[k] ? '#3ecf8e' : '#f5b942') + '">(xcheck ' + c + ')</span>';
        }
        h += '<div><div class="k">' + esc(k) + '</div><div class="v">' + v + '</div></div>';
      });
      h += '</div>';
    }
    if (tc) h += '<h4 style="margin:8px 0 4px">Tool calls</h4>' + tc;
    if (d.content) h += '<h4 style="margin:8px 0 4px">Output</h4><pre>' + esc(d.content) + '</pre>';
    if (d.diffs && d.diffs.length) {
      h += '<h4 style="margin:8px 0 4px">Changed files (' + d.diffs.length + ')</h4>';
      h += '<div class="kv">';
      d.diffs.forEach(function(x) { h += '<div><div class="k">' + esc(x.file) + '</div><div class="v">' + esc(x.status) + '</div></div>'; });
      h += '</div>';
      d.diffs.forEach(function(x) { if (x.diff) h += '<pre>' + esc(x.diff) + '</pre>'; });
    }
    if (d.grade) h += '<h4 style="margin:8px 0 4px">Hidden-test grade</h4><pre>' + esc(d.grade) + '</pre>';
    if (d.check) h += '<h4 style="margin:8px 0 4px">Checker</h4><pre>' + esc(d.check) + '</pre>';
    if (d.trajectory && d.trajectory.length) {
      h += '<h4 style="margin:8px 0 4px">Agent trajectory</h4><div style="max-height:320px;overflow-y:auto;border:1px solid #232c3f;border-radius:8px;padding:8px">';
      d.trajectory.forEach(function(ev) {
        if (ev.type === 'user') h += '<div style="color:#7d8aa3;font-size:11px;margin-top:6px">USER</div><div>' + esc(ev.text) + '</div>';
        else h += '<div style="color:#4f8cff;font-size:11px;margin-top:6px">ASSISTANT' + (ev.reasoning ? ' <span style="color:#7d8aa3">(reasoning ' + esc(ev.reasoning) + ')</span>' : '') + '</div><div>' + esc(ev.text) + '</div>';
      });
      h += '</div>';
    }
    if (d.session_path) h += '<h4 style="margin:8px 0 4px">Session file</h4><pre>' + esc(d.session_path) + '</pre>';
    h += '</div>';
  });
  $('#modal-card').innerHTML = h;
  $('#modal').classList.remove('hidden');
}

function closeModal() {
  $('#modal').classList.add('hidden');
}

// ---------- routing ----------
function setView(name) {
  document.querySelectorAll('.tab').forEach(function(t) { t.classList.toggle('active', t.dataset.view === name); });
  if (name === 'about') renderAbout();
  else if (name === 'overview') renderOverview();
  else if (name === 'categories') renderCategories();
  else if (name === 'ladder') renderLadder();
  else renderTasks();
}

// ---------- boot ----------
fetch('data/results.json').then(function(r) {
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}).then(function(data) {
  DATA = data;
  var n = (data.runs || []).length;
  var cost = sum((data.runs || []).map(function(r) { return r.cost_usd; }));
  $('#meta').textContent = n + ' runs · ' + fmtMoney(cost) + ' spent';
  document.querySelectorAll('.tab').forEach(function(t) { t.addEventListener('click', function() { setView(t.dataset.view); }); });
  setView('about');  // landing page for first-time visitors
}).catch(function(err) {
  $('#view').innerHTML = "<div class='panel'><h3>No results yet</h3><p>Run <code>bin/build_webdata.py</code> after the benchmark produces results.</p><pre>" + esc(err.message) + '</pre></div>';
});

window.openTask = openTask;
window.closeModal = closeModal;

