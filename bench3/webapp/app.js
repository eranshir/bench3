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
  if (name === 'overview') renderOverview();
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
  setView('overview');
}).catch(function(err) {
  $('#view').innerHTML = "<div class='panel'><h3>No results yet</h3><p>Run <code>bin/build_webdata.py</code> after the benchmark produces results.</p><pre>" + esc(err.message) + '</pre></div>';
});

window.openTask = openTask;
window.closeModal = closeModal;

