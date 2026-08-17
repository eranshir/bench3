// bench3 results renderer
(function(){
  "use strict";
  const $ = s => document.querySelector(s);
  const el = (tag, cls, html) => { const e = document.createElement(tag); if(cls) e.className = cls; if(html!=null) e.innerHTML = html; return e; };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  const ORDER = ["deepseek-flash","deepseek-pro","gpt-sol","grok","mtplx"];
  const arm = id => BENCH.arms.find(a => a.id === id);

  /* ---------- arm cards ---------- */
  function renderCards(){
    const grid = $("#arm-cards");
    ORDER.forEach(id => {
      const a = arm(id), o = BENCH.overall[id];
      const card = el("div", "arm-card" + (id==="mtplx" ? " local" : ""));
      const bar = el("div", "bar");
      const fill = el("i"); fill.style.background = a.color;
      bar.appendChild(fill);
      card.innerHTML =
        '<div class="arm-name"><span class="swatch" style="background:'+a.color+'"></span>'+esc(a.name)+'</div>'+
        '<div class="arm-vendor">'+esc(a.vendor)+' · n='+o.n+' · '+(o.trials.length>1 ? o.trials.length+" trials" : "trial 1")+'</div>'+
        '<div class="arm-pass">'+o.pass_pct+'<small>% pass</small></div>';
      card.appendChild(bar);
      card.insertAdjacentHTML("beforeend",
        '<div class="arm-meta"><span>cost <b>$'+o.cost_usd.toFixed(o.cost_usd<1?4:2)+'</b></span>'+
        '<span>quality <b>'+(BENCH.judged[id].mean!=null ? BENCH.judged[id].mean.toFixed(2)+"/5" : "—")+'</b></span></div>');
      grid.appendChild(card);
      requestAnimationFrame(()=>requestAnimationFrame(()=>{ fill.style.width = o.pass_pct + "%"; }));
    });
  }

  /* ---------- category charts ---------- */
  const CAT_LABEL = {
    coding:"Coding", "agentic-workflow":"Agentic workflow", reasoning:"Reasoning",
    "tool-use":"Tool use", creativity:"Creativity", writing:"Writing"
  };
  function renderCats(){
    const stack = $("#category-charts");
    ["coding","agentic-workflow","reasoning","tool-use","creativity","writing"].forEach(cat => {
      const wrap = el("div", "cat-chart reveal");
      const d = BENCH.categories[cat];
      const max = Math.max(...ORDER.map(id => d[id] ? d[id].pct : 0));
      wrap.appendChild(el("div","cat-title",'<h4>'+CAT_LABEL[cat]+'</h4><span>hidden tests · objective checkers · blind rubric</span>'));
      const rows = el("div","cat-rows");
      ORDER.forEach(id => {
        const c = d[id]; if(!c) return;
        const a = arm(id);
        const row = el("div","cat-row");
        const bar = el("div","bar"); const fill = el("i"); fill.style.background = a.color;
        bar.appendChild(fill);
        row.appendChild(el("span","lbl",esc(a.name)));
        row.appendChild(bar);
        row.appendChild(el("span","pct", c.pct.toFixed(0)+"% · "+c.passed+"/"+c.n));
        rows.appendChild(row);
        requestAnimationFrame(()=>requestAnimationFrame(()=>{ fill.style.width = (100*c.pct/max)+"%"; }));
      });
      wrap.appendChild(rows);
      stack.appendChild(wrap);
    });
  }

  /* ---------- per-task table ---------- */
  function renderTasks(){
    $("#task-head").innerHTML = '<th>Task</th>'+ORDER.map(id=>'<th class="num">'+esc(arm(id).name)+'</th><th class="num">sec</th>').join("");
    const body = $("#task-body");
    BENCH.tasks.forEach(t => {
      const row = el("tr", t.category==="coding"||t.category==="agentic-workflow" ? "local-row":"");
      row.appendChild(el("td","task-name",esc(t.task)));
      ORDER.forEach(id => {
        const d = t.arms[id];
        if(!d || d.n===0){ row.appendChild(el("td","num","—")); row.appendChild(el("td","num","—")); return; }
        const cls = d.passed===d.n ? "pass" : (d.passed===0 ? "fail" : "skip");
        const label = d.passed+"/"+d.n;
        row.appendChild(el("td","num",'<span class="pill '+cls+'">'+label+'</span>'));
        row.appendChild(el("td","num", d.secs[0]>=1750 ? d.secs[0]+"s ⏱" : d.secs[0]+"s"));
      });
      body.appendChild(row);
    });
  }

  /* ---------- tps chart ---------- */
  function renderTps(){
    const wrap = el("div","cat-chart reveal");
    wrap.appendChild(el("div","cat-title",'<h4>Effective tokens/sec</h4><span>output tokens ÷ wall time · singleshot vs agentic</span>'));
    const rows = el("div","cat-rows");
    const modes = [["singleshot","singleshot"],["agentic","agentic"]];
    const max = Math.max(...ORDER.map(id=>Math.max(BENCH.tps[id].singleshot.mean, BENCH.tps[id].agentic.mean)));
    ORDER.forEach(id => {
      const a = arm(id);
      modes.forEach(([key]) => {
        const t = BENCH.tps[id][key]; if(!t.n) return;
        const row = el("div","cat-row");
        const bar = el("div","bar"); const fill = el("i"); fill.style.background = a.color;
        bar.appendChild(fill);
        row.appendChild(el("span","lbl",esc(a.name)+(key==="agentic"?" · agentic":" · single")));
        row.appendChild(bar);
        row.appendChild(el("span","pct", t.mean.toFixed(0)+" tok/s"));
        rows.appendChild(row);
        requestAnimationFrame(()=>requestAnimationFrame(()=>{ fill.style.width = (100*t.mean/max)+"%"; }));
      });
    });
    wrap.appendChild(rows);
    $("#tps-chart").appendChild(wrap);
  }

  /* ---------- thermal bars ---------- */
  function renderThermal(){
    const wrap = $("#thermal-bars");
    const rows = [
      ["Cool Mac · default sampler","36 – 46",92],
      ["Cool Mac · greedy (temp 0)","41",100],
      ["Hot (2h load) · greedy","28 – 34",72],
      ["Hot (2h load) · default","25 – 26",58],
    ];
    rows.forEach(r => {
      const row = el("div","duel-row");
      const bar = el("div","bar"); const fill = el("i"); fill.style.background = "var(--accent)"; fill.style.opacity = .85;
      bar.appendChild(fill);
      row.appendChild(el("span",null,esc(r[0])));
      row.appendChild(bar);
      row.appendChild(el("b",null,esc(r[1])+" tok/s"));
      wrap.appendChild(row);
      requestAnimationFrame(()=>requestAnimationFrame(()=>{ fill.style.width = r[2]+"%"; }));
    });
  }

  /* ---------- cost chart ---------- */
  function renderCost(){
    const wrap = el("div","cat-chart reveal");
    wrap.appendChild(el("div","cat-title",'<h4>Total API spend</h4><span>250+ runs · list prices · MTPLX runs on your own hardware</span>'));
    const rows = el("div","cat-rows");
    const vals = ORDER.map(id => BENCH.overall[id].cost_usd);
    const max = Math.max(...vals);
    ORDER.forEach((id,i) => {
      const a = arm(id), c = vals[i];
      const row = el("div","cat-row");
      const bar = el("div","bar"); const fill = el("i"); fill.style.background = a.color;
      bar.appendChild(fill);
      row.appendChild(el("span","lbl",esc(a.name)));
      row.appendChild(bar);
      row.appendChild(el("span","pct","$"+c.toFixed(c<1?4:2)));
      rows.appendChild(row);
      requestAnimationFrame(()=>requestAnimationFrame(()=>{ fill.style.width = (100*c/max)+"%"; }));
    });
    wrap.appendChild(rows);
    $("#cost-chart").appendChild(wrap);
  }

  /* ---------- mlxfast challenge ---------- */
  function renderMlxfast(){
    const m = BENCH.mlxfast;
    const wrap = el("div", "cat-chart reveal");
    const rows = el("div", "cat-rows");
    const max = 2.95;
    m.legs.forEach(leg => {
      const row = el("div", "cat-row");
      const bar = el("div", "bar"); const fill = el("i");
      fill.style.background = leg.depth === 8 ? "var(--gradient, var(--accent))" : "var(--accent)";
      fill.style.background = leg.depth === 8 ? "linear-gradient(90deg,#4ade80,#22d3ee)" : "var(--accent)";
      fill.style.opacity = leg.depth === 0 ? 0.35 : 0.85;
      bar.appendChild(fill);
      row.appendChild(el("span", "lbl", esc(leg.label)));
      row.appendChild(bar);
      row.appendChild(el("span", "pct", leg.speedup.toFixed(2)+"× · "+leg.tps+" tok/s"));
      rows.appendChild(row);
      requestAnimationFrame(()=>requestAnimationFrame(()=>{ fill.style.width = (100*leg.speedup/max)+"%"; }));
    });
    // reference + stock + mtplx mini-rows
    [
      ["Stock main (baseline harness)", m.stock_speedup],
      ["Leaderboard record · gated M5 Max", m.reference.speedup],
    ].forEach(([label, v]) => {
      const row = el("div", "cat-row");
      const bar = el("div", "bar"); const fill = el("i"); fill.style.background = "var(--accent2)"; fill.style.opacity = 0.7;
      bar.appendChild(fill);
      row.appendChild(el("span", "lbl", esc(label)));
      row.appendChild(bar);
      row.appendChild(el("span", "pct", v.toFixed(2)+"×"));
      rows.appendChild(row);
      requestAnimationFrame(()=>requestAnimationFrame(()=>{ fill.style.width = (100*v/max)+"%"; }));
    });
    wrap.appendChild(el("div", "cat-title", '<h4>Decode speedup vs true serial (MTP off)</h4><span>our M5 Max · '+esc(m.our_machine)+'</span>'));
    wrap.appendChild(rows);
    const grid = document.querySelector("#mlxfast-grid");
    if (grid) grid.appendChild(wrap);
  }

  /* ---------- reveal on scroll ---------- */
  function reveal(){
    const els = document.querySelectorAll(".reveal");
    if(!("IntersectionObserver" in window)){ els.forEach(n => n.classList.add("in")); return; }
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => { if(e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); } });
    }, {threshold:.12});
    els.forEach(n => io.observe(n));
    // safety net: never leave content invisible (fonts/IO hiccups, webviews)
    setTimeout(() => els.forEach(n => n.classList.add("in")), 2500);
  }

  renderCards(); renderCats(); renderTasks(); renderTps(); renderThermal(); renderMlxfast(); renderCost(); reveal();
})();
